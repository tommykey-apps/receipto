"""Integration test fixtures for Lambda functions using DynamoDB Local.

DynamoDB Local must be running on http://localhost:8000.
S3, SNS, SES use moto.
"""

from __future__ import annotations

import importlib
import os
import sys
import uuid

import boto3
import pytest
from moto import mock_aws

_DYNAMODB_ENDPOINT = "http://localhost:8000"

os.environ.setdefault("RECEIPTS_BUCKET_US", "test-receipts-us")


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


def _purge_lambda_modules() -> None:
    """Remove cached Lambda modules so they pick up new table config."""
    modules_to_remove = [
        mod for mod in list(sys.modules)
        if mod.startswith((
            "expense_saver", "budget_checker", "categorizer",
            "ocr_processor", "receipt_validator", "notifier",
            # Also purge API modules for cross-layer tests
            "app", "routers", "store", "auth", "models",
        ))
    ]
    for mod in modules_to_remove:
        del sys.modules[mod]


@pytest.fixture()
def table():
    """Create a fresh DynamoDB table on DynamoDB Local."""
    table_name = f"test-integration-{uuid.uuid4().hex[:12]}"

    os.environ["DYNAMODB_ENDPOINT"] = _DYNAMODB_ENDPOINT
    os.environ["DYNAMODB_TABLE"] = table_name
    os.environ["AWS_DEFAULT_REGION"] = "ap-northeast-1"
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"

    dynamodb = boto3.resource(
        "dynamodb",
        endpoint_url=_DYNAMODB_ENDPOINT,
        region_name="ap-northeast-1",
        aws_access_key_id="testing",
        aws_secret_access_key="testing",
    )
    tbl = dynamodb.create_table(
        TableName=table_name,
        KeySchema=[
            {"AttributeName": "pk", "KeyType": "HASH"},
            {"AttributeName": "sk", "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "pk", "AttributeType": "S"},
            {"AttributeName": "sk", "AttributeType": "S"},
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    tbl.meta.client.get_waiter("table_exists").wait(TableName=table_name)

    _purge_lambda_modules()

    yield tbl

    tbl.delete()


@pytest.fixture()
def s3_bucket():
    """Create a moto S3 bucket."""
    with mock_aws():
        s3 = boto3.client("s3", region_name="ap-northeast-1")
        bucket_name = "test-receipts"
        s3.create_bucket(
            Bucket=bucket_name,
            CreateBucketConfiguration={"LocationConstraint": "ap-northeast-1"},
        )
        yield bucket_name


@pytest.fixture()
def sns_topic():
    """Create a moto SNS topic."""
    with mock_aws():
        client = boto3.client("sns", region_name="ap-northeast-1")
        resp = client.create_topic(Name="budget-alerts")
        topic_arn = resp["TopicArn"]
        os.environ["BUDGET_ALERT_TOPIC_ARN"] = topic_arn
        yield topic_arn


@pytest.fixture()
def ses_verified():
    """Verify SES identities in moto."""
    with mock_aws():
        client = boto3.client("ses", region_name="ap-northeast-1")
        client.verify_email_identity(EmailAddress="noreply@example.com")
        client.verify_email_identity(EmailAddress="user@example.com")
        yield client
