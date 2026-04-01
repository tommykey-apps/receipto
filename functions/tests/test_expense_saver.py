"""Tests for expense_saver Lambda function."""

from __future__ import annotations

import importlib

import boto3


def _make_event(user_id="user-123", receipt_id="rcv-001", amount=1500,
                category="food", store_name="セブン"):
    return {
        "user_id": user_id,
        "receipt_id": receipt_id,
        "extracted": {
            "amount": amount,
            "store_name": store_name,
            "date": "2026-03-15",
        },
        "category": category,
    }


def test_save_valid_amount(ddb_table):
    """Save with valid amount returns saved=True and expense_id."""
    import expense_saver
    importlib.reload(expense_saver)
    # Point module-level table at our mock table
    expense_saver.table = ddb_table

    result = expense_saver.handler(_make_event(), None)
    assert result["saved"] is True
    assert "expense_id" in result
    assert len(result["expense_id"]) > 0


def test_monthly_summary_updated(ddb_table):
    """After save, SUM#{month} item has correct total and expense_count."""
    import expense_saver
    importlib.reload(expense_saver)
    expense_saver.table = ddb_table

    result = expense_saver.handler(_make_event(amount=1500), None)
    month = result["month"]

    summary = ddb_table.get_item(
        Key={"pk": "USER#user-123", "sk": f"SUM#{month}"}
    ).get("Item")
    assert summary is not None
    assert int(summary["total"]) == 1500
    assert int(summary["expense_count"]) == 1


def test_receipt_status_completed(ddb_table):
    """After save, RCV#{receipt_id} item has status='completed'."""
    import expense_saver
    importlib.reload(expense_saver)
    expense_saver.table = ddb_table

    # Pre-create the receipt item so the update_item has something to update
    ddb_table.put_item(Item={
        "pk": "USER#user-123",
        "sk": "RCV#rcv-001",
        "status": "processing",
    })

    expense_saver.handler(_make_event(receipt_id="rcv-001"), None)

    rcv = ddb_table.get_item(
        Key={"pk": "USER#user-123", "sk": "RCV#rcv-001"}
    ).get("Item")
    assert rcv["status"] == "completed"


def test_amount_none_returns_not_saved(ddb_table):
    """amount=None should return saved=False with error."""
    import expense_saver
    importlib.reload(expense_saver)
    expense_saver.table = ddb_table

    event = _make_event(amount=None)
    result = expense_saver.handler(event, None)
    assert result["saved"] is False
    assert "error" in result
