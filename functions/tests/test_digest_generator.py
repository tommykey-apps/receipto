"""Tests for digest_generator Lambda function."""

from __future__ import annotations

import importlib
from datetime import datetime, timezone
from unittest.mock import patch

import boto3

from digest_generator import _format_currency


def test_format_currency_positive():
    assert _format_currency(12345) == "¥12,345"


def test_format_currency_zero():
    assert _format_currency(0) == "¥0"


def test_no_expenses_not_sent(ddb_table):
    """No monthly summary => sent=False."""
    import digest_generator
    importlib.reload(digest_generator)
    digest_generator.table = ddb_table

    event = {"user_id": "user-123", "email": "user@example.com"}
    result = digest_generator.handler(event, None)
    assert result["sent"] is False


def test_with_expenses_sends_email(ddb_table, ses_verified):
    """With expenses in summary, SES send_email is called and sent=True."""
    import digest_generator
    importlib.reload(digest_generator)
    digest_generator.table = ddb_table
    digest_generator.ses = boto3.client("ses", region_name="ap-northeast-1")

    month = datetime.now(timezone.utc).strftime("%Y-%m")

    ddb_table.put_item(Item={
        "PK": "USER#user-123",
        "SK": f"SUM#{month}",
        "month": month,
        "total": 25000,
        "expense_count": 10,
        "by_category": {"food": 15000, "transport": 10000},
    })

    event = {"user_id": "user-123", "email": "user@example.com"}
    result = digest_generator.handler(event, None)
    assert result["sent"] is True
    assert result["total"] == 25000
    assert result["expense_count"] == 10
