"""Shared fixtures for all tests.

Key challenge: router modules create module-level DynamoDBStore() instances at
import time, so moto must be active *before* the app is imported. We achieve
this by:
  1. Setting env vars (DEV_USER_ID, DYNAMODB_TABLE, AWS credentials) at
     module load time.
  2. Using an autouse session-scoped fixture that starts mock_aws before
     any test imports the app.
  3. Re-importing the app module inside the fixture so every DynamoDBStore()
     connects to the moto-managed DynamoDB.
"""

from __future__ import annotations

import importlib
import os
import sys

import boto3
import pytest
from moto import mock_aws

# ── Set env vars BEFORE anything is imported ──
os.environ["DEV_USER_ID"] = "test-user"
os.environ["DYNAMODB_TABLE"] = "expense-tracker"
os.environ["RECEIPTS_BUCKET"] = "test-receipts-bucket"
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
os.environ["AWS_ACCESS_KEY_ID"] = "testing"
os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
os.environ["AWS_SECURITY_TOKEN"] = "testing"
os.environ["AWS_SESSION_TOKEN"] = "testing"
# Remove any real DynamoDB endpoint so boto3 uses moto
os.environ.pop("DYNAMODB_ENDPOINT", None)
os.environ.pop("S3_ENDPOINT", None)


def _create_table() -> None:
    """Create the DynamoDB table inside the active moto context."""
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    dynamodb.create_table(
        TableName="expense-tracker",
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


def _create_s3_bucket() -> None:
    """Create the S3 bucket inside the active moto context."""
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket="test-receipts-bucket")


def _purge_app_modules() -> None:
    """Remove cached app modules so they re-import with fresh DynamoDBStore."""
    modules_to_remove = [
        mod for mod in sys.modules
        if mod.startswith(("app", "routers", "store", "auth", "models"))
    ]
    for mod in modules_to_remove:
        del sys.modules[mod]


@pytest.fixture(autouse=True)
def aws_mocks():
    """Activate moto for every test, creating fresh table + bucket each time."""
    with mock_aws():
        _create_table()
        _create_s3_bucket()

        # Purge cached modules so DynamoDBStore reconnects to moto
        _purge_app_modules()

        yield


@pytest.fixture()
def client(aws_mocks):
    """FastAPI TestClient with moto-backed DynamoDB."""
    # Import INSIDE the fixture so module-level DynamoDBStore() uses moto
    _purge_app_modules()
    from app import create_app
    from starlette.testclient import TestClient

    app = create_app()
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def store(aws_mocks):
    """A DynamoDBStore instance backed by moto."""
    _purge_app_modules()
    from store.dynamodb import DynamoDBStore
    return DynamoDBStore()
