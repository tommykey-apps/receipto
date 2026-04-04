"""Write OCR results to receipt record. Expense is created by the user after review."""

from __future__ import annotations

import os

import boto3

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ.get("DYNAMODB_TABLE", "expense-tracker"))


def handler(event: dict, context: object) -> dict:  # noqa: ARG001
    user_id = event["user_id"]
    receipt_id = event["receipt_id"]
    extracted = event["extracted"]
    category = event["category"]

    amount = extracted.get("amount")
    store_name = extracted.get("store_name", "")

    # Write OCR results to receipt record (no expense created yet)
    table.update_item(
        Key={"pk": f"USER#{user_id}", "sk": f"RCV#{receipt_id}"},
        UpdateExpression="SET #status = :s, store_name = :sn, amount = :amt, category = :cat",
        ExpressionAttributeNames={"#status": "status"},
        ExpressionAttributeValues={
            ":s": "completed" if amount is not None else "failed",
            ":sn": store_name,
            ":amt": amount,
            ":cat": category,
        },
    )

    return {
        "user_id": user_id,
        "receipt_id": receipt_id,
        "amount": amount,
        "category": category,
        "saved": amount is not None,
    }
