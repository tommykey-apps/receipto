"""Tests for expense_saver Lambda function (OCR result writer)."""

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
    """Valid amount writes OCR results and returns saved=True."""
    import expense_saver
    importlib.reload(expense_saver)
    expense_saver.table = ddb_table

    ddb_table.put_item(Item={
        "pk": "USER#user-123", "sk": "RCV#rcv-001", "status": "processing",
    })

    result = expense_saver.handler(_make_event(), None)
    assert result["saved"] is True


def test_receipt_status_completed(ddb_table):
    """After save, receipt status is 'completed' with OCR results."""
    import expense_saver
    importlib.reload(expense_saver)
    expense_saver.table = ddb_table

    ddb_table.put_item(Item={
        "pk": "USER#user-123", "sk": "RCV#rcv-001", "status": "processing",
    })

    expense_saver.handler(_make_event(receipt_id="rcv-001"), None)

    rcv = ddb_table.get_item(
        Key={"pk": "USER#user-123", "sk": "RCV#rcv-001"}
    ).get("Item")
    assert rcv["status"] == "completed"
    assert rcv["store_name"] == "セブン"
    assert int(rcv["amount"]) == 1500
    assert rcv["category"] == "food"


def test_no_expense_created(ddb_table):
    """expense_saver should NOT create an expense item (user does that after review)."""
    import expense_saver
    importlib.reload(expense_saver)
    expense_saver.table = ddb_table

    ddb_table.put_item(Item={
        "pk": "USER#user-123", "sk": "RCV#rcv-001", "status": "processing",
    })

    expense_saver.handler(_make_event(), None)

    resp = ddb_table.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key("pk").eq("USER#user-123")
            & boto3.dynamodb.conditions.Key("sk").begins_with("EXP#"),
    )
    assert len(resp["Items"]) == 0


def test_amount_none_marks_failed(ddb_table):
    """amount=None should mark receipt as failed."""
    import expense_saver
    importlib.reload(expense_saver)
    expense_saver.table = ddb_table

    ddb_table.put_item(Item={
        "pk": "USER#user-123", "sk": "RCV#rcv-001", "status": "processing",
    })

    result = expense_saver.handler(_make_event(amount=None), None)
    assert result["saved"] is False

    rcv = ddb_table.get_item(
        Key={"pk": "USER#user-123", "sk": "RCV#rcv-001"}
    ).get("Item")
    assert rcv["status"] == "failed"
