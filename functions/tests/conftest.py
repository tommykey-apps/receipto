"""Shared fixtures for Lambda function tests."""

from __future__ import annotations

import os

import boto3
import pytest
from moto import mock_aws

# Set env vars before any module-level imports in Lambda code
os.environ["DYNAMODB_TABLE"] = "expense-tracker"
os.environ["AWS_DEFAULT_REGION"] = "ap-northeast-1"
os.environ["AWS_ACCESS_KEY_ID"] = "testing"
os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
os.environ["AWS_SECURITY_TOKEN"] = "testing"
os.environ["AWS_SESSION_TOKEN"] = "testing"


@pytest.fixture()
def aws(monkeypatch):
    """Activate moto mock for all AWS services."""
    with mock_aws():
        yield


@pytest.fixture()
def ddb_table(aws):
    """Create a DynamoDB table with pk (HASH) and sk (RANGE) — lowercase keys."""
    dynamodb = boto3.resource("dynamodb", region_name="ap-northeast-1")
    table = dynamodb.create_table(
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
    table.meta.client.get_waiter("table_exists").wait(TableName="expense-tracker")
    return table


@pytest.fixture()
def s3_bucket(aws):
    """Create a moto S3 bucket."""
    s3 = boto3.client("s3", region_name="ap-northeast-1")
    s3.create_bucket(
        Bucket="test-receipts",
        CreateBucketConfiguration={"LocationConstraint": "ap-northeast-1"},
    )
    return "test-receipts"


@pytest.fixture()
def sns_topic(aws, monkeypatch):
    """Create a moto SNS topic and set BUDGET_ALERT_TOPIC_ARN."""
    client = boto3.client("sns", region_name="ap-northeast-1")
    resp = client.create_topic(Name="budget-alerts")
    topic_arn = resp["TopicArn"]
    monkeypatch.setenv("BUDGET_ALERT_TOPIC_ARN", topic_arn)
    return topic_arn


@pytest.fixture()
def ses_verified(aws):
    """Verify a SES email identity."""
    client = boto3.client("ses", region_name="ap-northeast-1")
    client.verify_email_identity(EmailAddress="noreply@example.com")
    client.verify_email_identity(EmailAddress="user@example.com")
    return client
