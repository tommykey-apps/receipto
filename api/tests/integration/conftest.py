"""Integration test fixtures using REAL DynamoDB Local (not moto).

DynamoDB Local must be running on http://localhost:8000.
S3 uses moto since presigned URLs don't need a real service.

IMPORTANT: The parent conftest.py has an autouse `aws_mocks` fixture that
activates moto for ALL tests.  We override it here to disable moto, so that
DynamoDB calls reach DynamoDB Local instead.
"""

from __future__ import annotations

import os
import sys
import uuid

import boto3
import pytest
from moto import mock_aws

# ---------------------------------------------------------------------------
# Check DynamoDB Local reachability once at import time
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Override parent conftest's autouse aws_mocks → no-op for integration tests
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def aws_mocks():
    """Override the parent conftest's aws_mocks: do NOT activate moto globally.

    Integration tests manage their own moto contexts (S3 only) and use
    real DynamoDB Local for DynamoDB.
    """
    yield


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _purge_app_modules() -> None:
    """Remove cached app modules so DynamoDBStore reconnects."""
    modules_to_remove = [
        mod for mod in list(sys.modules)
        if mod.startswith(("app", "routers", "store", "auth", "models"))
    ]
    for mod in modules_to_remove:
        del sys.modules[mod]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture()
def integration_table():
    """Create a fresh DynamoDB table on DynamoDB Local, tear down after test."""
    table_name = f"test-integration-{uuid.uuid4().hex[:12]}"

    # Set env vars BEFORE importing app modules
    os.environ["DYNAMODB_ENDPOINT"] = _DYNAMODB_ENDPOINT
    os.environ["DYNAMODB_TABLE"] = table_name
    os.environ["DEV_USER_ID"] = "integration-test-user"
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
    table = dynamodb.create_table(
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
    table.meta.client.get_waiter("table_exists").wait(TableName=table_name)

    yield table

    # Cleanup
    table.delete()


@pytest.fixture()
def table(integration_table):
    """Alias that also purges app modules so the app picks up the new table."""
    _purge_app_modules()
    yield integration_table


@pytest.fixture()
def client(table):
    """FastAPI TestClient pointed at the real DynamoDB Local table.

    Uses moto ONLY for S3 (presigned URLs). DynamoDB goes to DynamoDB Local
    because DYNAMODB_ENDPOINT env var is set.
    """
    os.environ["RECEIPTS_BUCKET"] = "test-receipts-bucket"
    os.environ.pop("S3_ENDPOINT", None)

    _purge_app_modules()

    with mock_aws():
        # Create S3 bucket in moto
        s3 = boto3.client("s3", region_name="ap-northeast-1")
        s3.create_bucket(
            Bucket="test-receipts-bucket",
            CreateBucketConfiguration={"LocationConstraint": "ap-northeast-1"},
        )

        from app import create_app
        from starlette.testclient import TestClient

        app = create_app()
        with TestClient(app) as c:
            yield c
