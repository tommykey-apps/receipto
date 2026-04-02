"""Integration tests chaining Lambda handlers: output of one feeds input of next.

Uses DynamoDB Local for real persistence. Moto for S3 (receipt_validator needs it).
Textract is mocked since there's no local Textract service.
"""

from __future__ import annotations

import importlib
import io
import json
import os
import sys
from unittest.mock import MagicMock, patch

import boto3
import pytest
from moto import mock_aws

_DYNAMODB_ENDPOINT = "http://localhost:8000"


def _dynamodb_local_available() -> bool:
    try:
        client = boto3.client(
            "dynamodb",
            endpoint_url=_DYNAMODB_ENDPOINT,
            region_name="ap-northeast-1",
            aws_access_key_id="testing",
            aws_secret_access_key="testing",
        )
        client.list_tables()
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _dynamodb_local_available(),
    reason="DynamoDB Local not reachable at localhost:8000",
)


def _reload_lambda_module(module_name: str):
    """Reload a lambda module so it picks up current DYNAMODB_TABLE env var
    and connects to DynamoDB Local via patched boto3."""
    if module_name in sys.modules:
        del sys.modules[module_name]
    return importlib.import_module(module_name)


def _make_dynamodb_resource():
    """Create a DynamoDB resource pointing at DynamoDB Local."""
    return boto3.resource(
        "dynamodb",
        endpoint_url=_DYNAMODB_ENDPOINT,
        region_name="ap-northeast-1",
        aws_access_key_id="testing",
        aws_secret_access_key="testing",
    )


class TestPipelineChain:
    """Chain Lambda handlers together, simulating Step Functions pipeline."""

    def test_full_pipeline(self, table):
        """Full pipeline: validator -> ocr -> categorizer -> saver -> budget_checker -> notifier.

        Textract is mocked. S3 uses moto for receipt_validator.
        """
        user_id = "pipeline-user"
        receipt_id = "rcpt-001"
        bucket = "test-receipts"
        s3_key = f"uploads/{user_id}/{receipt_id}/receipt.jpg"

        # Pre-create receipt record in DynamoDB (as the API would do)
        table.put_item(Item={
            "pk": f"USER#{user_id}",
            "sk": f"RCV#{receipt_id}",
            "id": receipt_id,
            "s3_key": s3_key,
            "filename": "receipt.jpg",
            "status": "processing",
        })

        table_name = os.environ["DYNAMODB_TABLE"]
        ddb_resource = _make_dynamodb_resource()

        # Step 1: receipt_validator (needs S3 with moto)
        with mock_aws():
            s3_client = boto3.client("s3", region_name="ap-northeast-1")
            s3_client.create_bucket(
                Bucket=bucket,
                CreateBucketConfiguration={"LocationConstraint": "ap-northeast-1"},
            )
            s3_client.put_object(
                Bucket=bucket,
                Key=s3_key,
                Body=b"fake-jpeg-content",
                ContentType="image/jpeg",
            )

            mod_validator = _reload_lambda_module("receipt_validator")
            # Patch the module-level s3 client to use moto's
            mod_validator.s3 = s3_client

            validator_event = {
                "bucket": bucket,
                "s3_key": s3_key,
                "receipt_id": receipt_id,
                "user_id": user_id,
            }
            validator_result = mod_validator.handler(validator_event, None)

        assert validator_result["valid"] is True

        # Step 2: ocr_processor (mock Bedrock Claude)
        import io
        mock_bedrock_body = json.dumps({
            "content": [{"type": "text", "text": json.dumps({
                "store_name": "セブンイレブン",
                "amount": 1280,
                "date": "2025-03-15",
            })}],
        })

        mod_ocr = _reload_lambda_module("ocr_processor")
        mock_bedrock = MagicMock()
        mock_bedrock.invoke_model.return_value = {"body": io.BytesIO(mock_bedrock_body.encode())}
        mod_ocr.bedrock = mock_bedrock

        ocr_event = {
            "bucket": bucket,
            "s3_key": s3_key,
            "receipt_id": receipt_id,
            "user_id": user_id,
        }
        ocr_result = mod_ocr.handler(ocr_event, None)

        assert ocr_result["ocr_success"] is True
        assert ocr_result["extracted"]["amount"] == 1280
        assert ocr_result["extracted"]["store_name"] == "セブンイレブン"

        # Step 3: categorizer (pure logic, no AWS)
        mod_categorizer = _reload_lambda_module("categorizer")
        cat_event = {
            "receipt_id": receipt_id,
            "user_id": user_id,
            "extracted": ocr_result["extracted"],
        }
        cat_result = mod_categorizer.handler(cat_event, None)
        assert cat_result["category"] == "food"  # セブン matches food

        # Step 4: expense_saver (writes to DynamoDB Local)
        mod_saver = _reload_lambda_module("expense_saver")
        # Patch module-level dynamodb/table to use DynamoDB Local
        mod_saver.dynamodb = ddb_resource
        mod_saver.table = ddb_resource.Table(table_name)

        saver_event = {
            "user_id": user_id,
            "receipt_id": receipt_id,
            "extracted": cat_result["extracted"],
            "category": cat_result["category"],
        }
        saver_result = mod_saver.handler(saver_event, None)
        assert saver_result["saved"] is True
        assert saver_result["amount"] == 1280

        # Step 5: budget_checker (reads from DynamoDB Local)
        # First set a budget
        table.put_item(Item={
            "pk": f"USER#{user_id}",
            "sk": f"BDG#{saver_result['month']}#food",
            "month": saver_result["month"],
            "category": "food",
            "amount": 1000,
            "alert_threshold_pct": 80,
        })

        mod_checker = _reload_lambda_module("budget_checker")
        mod_checker.dynamodb = ddb_resource
        mod_checker.table = ddb_resource.Table(table_name)

        checker_event = {
            "user_id": user_id,
            "month": saver_result["month"],
            "category": "food",
            "amount": 1280,
        }
        checker_result = mod_checker.handler(checker_event, None)
        assert checker_result["has_budget"] is True
        assert checker_result["budget_exceeded"] is True  # 1280/1000 = 128%

        # Step 6: notifier (uses SNS, mock it)
        with mock_aws():
            sns_client = boto3.client("sns", region_name="ap-northeast-1")
            resp = sns_client.create_topic(Name="budget-alerts")
            topic_arn = resp["TopicArn"]
            os.environ["BUDGET_ALERT_TOPIC_ARN"] = topic_arn

            mod_notifier = _reload_lambda_module("notifier")
            mod_notifier.sns = sns_client
            mod_notifier.TOPIC_ARN = topic_arn

            notifier_event = {
                "user_id": user_id,
                "month": checker_result["month"],
                "category": "food",
                "budget_amount": checker_result["budget_amount"],
                "current_spent": checker_result["current_spent"],
                "pct_used": checker_result["pct_used"],
            }
            notifier_result = mod_notifier.handler(notifier_event, None)
            assert notifier_result["notified"] is True

    def test_invalid_file_type_stops_pipeline(self, table):
        """Invalid file type: validator returns valid=False."""
        user_id = "pipeline-user"
        receipt_id = "rcpt-bad"
        bucket = "test-receipts"
        s3_key = f"uploads/{user_id}/{receipt_id}/file.exe"

        with mock_aws():
            s3_client = boto3.client("s3", region_name="ap-northeast-1")
            s3_client.create_bucket(
                Bucket=bucket,
                CreateBucketConfiguration={"LocationConstraint": "ap-northeast-1"},
            )
            s3_client.put_object(
                Bucket=bucket,
                Key=s3_key,
                Body=b"not-an-image",
                ContentType="application/octet-stream",
            )

            mod_validator = _reload_lambda_module("receipt_validator")
            mod_validator.s3 = s3_client

            result = mod_validator.handler({
                "bucket": bucket,
                "s3_key": s3_key,
                "receipt_id": receipt_id,
                "user_id": user_id,
            }, None)

        assert result["valid"] is False
        assert "Invalid file" in result["error"]

    def test_ocr_no_amount_saver_returns_not_saved(self, table):
        """OCR extracts no amount: saver returns saved=False."""
        user_id = "pipeline-user"
        receipt_id = "rcpt-noamt"
        table_name = os.environ["DYNAMODB_TABLE"]
        ddb_resource = _make_dynamodb_resource()

        # OCR returns no amount
        extracted = {"store_name": "SomeStore", "amount": None, "date": None}

        mod_saver = _reload_lambda_module("expense_saver")
        mod_saver.dynamodb = ddb_resource
        mod_saver.table = ddb_resource.Table(table_name)

        result = mod_saver.handler({
            "user_id": user_id,
            "receipt_id": receipt_id,
            "extracted": extracted,
            "category": "other",
        }, None)

        assert result["saved"] is False
        assert "No amount" in result["error"]

    def test_no_budget_set_not_exceeded(self, table):
        """No budget set for category: budget_exceeded=False."""
        user_id = "pipeline-user"
        table_name = os.environ["DYNAMODB_TABLE"]
        ddb_resource = _make_dynamodb_resource()

        mod_checker = _reload_lambda_module("budget_checker")
        mod_checker.dynamodb = ddb_resource
        mod_checker.table = ddb_resource.Table(table_name)

        result = mod_checker.handler({
            "user_id": user_id,
            "month": "2025-03",
            "category": "entertainment",
            "amount": 5000,
        }, None)

        assert result["budget_exceeded"] is False
        assert result["has_budget"] is False
