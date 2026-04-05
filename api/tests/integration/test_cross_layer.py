"""Cross-layer integration tests: API and Lambda sharing the same DynamoDB Local table.

Verifies that data written by one layer is readable by the other.
These tests run under the API's venv (which has FastAPI) and add the
functions directory to sys.path for importing Lambda handlers.
"""

from __future__ import annotations

import importlib
import os
import sys

import boto3
import pytest
from moto import mock_aws

_DYNAMODB_ENDPOINT = "http://localhost:8000"

# Add functions directory to sys.path so we can import Lambda handlers
_FUNCTIONS_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "functions")
)
if _FUNCTIONS_DIR not in sys.path:
    sys.path.insert(0, _FUNCTIONS_DIR)


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


def _purge_all_modules() -> None:
    """Purge both API and Lambda modules."""
    modules_to_remove = [
        mod for mod in list(sys.modules)
        if mod.startswith((
            "app", "routers", "store", "auth", "models",
            "expense_saver", "budget_checker", "categorizer",
            "ocr_processor", "receipt_validator", "notifier",
        ))
    ]
    for mod in modules_to_remove:
        del sys.modules[mod]


def _make_dynamodb_resource():
    return boto3.resource(
        "dynamodb",
        endpoint_url=_DYNAMODB_ENDPOINT,
        region_name="ap-northeast-1",
        aws_access_key_id="testing",
        aws_secret_access_key="testing",
    )


class TestCrossLayer:
    """Tests verifying API and Lambda can share the same DynamoDB table."""

    def test_api_expense_readable_by_lambda(self, client, table):
        """Create expense via FastAPI TestClient, read via budget_checker Lambda."""
        table_name = os.environ["DYNAMODB_TABLE"]
        ddb_resource = _make_dynamodb_resource()

        # Create expense via API
        resp = client.post(
            "/api/expenses",
            json={"amount": 2000, "category": "food", "store_name": "マクドナルド"},
        )
        assert resp.status_code == 201
        expense = resp.json()
        month = expense["created_at"][:7]

        # Set a budget in the table
        table.put_item(Item={
            "pk": "USER#integration-test-user",
            "sk": f"BDG#{month}#food",
            "month": month,
            "category": "food",
            "amount": 5000,
            "alert_threshold_pct": 80,
        })

        # Use budget_checker Lambda to read from the same table
        _purge_all_modules()
        import budget_checker
        budget_checker.dynamodb = ddb_resource
        budget_checker.table = ddb_resource.Table(table_name)

        result = budget_checker.handler({
            "user_id": "integration-test-user",
            "month": month,
            "category": "food",
            "amount": 2000,
        }, None)

        assert result["has_budget"] is True
        assert result["current_spent"] == 2000
        assert result["budget_amount"] == 5000

    def test_lambda_ocr_then_api_creates_expense(self, client, table):
        """Lambda writes OCR result to receipt, API creates expense after user review."""
        table_name = os.environ["DYNAMODB_TABLE"]
        ddb_resource = _make_dynamodb_resource()
        ddb_table = ddb_resource.Table(table_name)

        # Pre-create receipt
        ddb_table.put_item(Item={
            "pk": "USER#integration-test-user",
            "sk": "RCV#rcpt-cross-01",
            "id": "rcpt-cross-01",
            "status": "processing",
        })

        # Lambda writes OCR results to receipt (no expense created)
        _purge_all_modules()
        import expense_saver
        expense_saver.dynamodb = ddb_resource
        expense_saver.table = ddb_table

        saver_result = expense_saver.handler({
            "user_id": "integration-test-user",
            "receipt_id": "rcpt-cross-01",
            "extracted": {"store_name": "ローソン", "amount": 350, "date": None},
            "category": "food",
        }, None)
        assert saver_result["saved"] is True

        # No expense yet
        resp = client.get("/api/expenses")
        assert resp.status_code == 200
        assert len(resp.json()) == 0

        # User creates expense via API
        resp = client.post("/api/expenses", json={
            "store_name": "ローソン", "amount": 350, "category": "food",
        })
        assert resp.status_code == 201
        month = resp.json()["created_at"][:7]

        # Expense and summary exist
        resp = client.get("/api/expenses")
        assert len(resp.json()) == 1

        resp = client.get(f"/api/summary/monthly?month={month}")
        assert resp.status_code == 200
        assert resp.json()["total"] == 350
