"""Save extracted expense to DynamoDB and update monthly summary."""

from __future__ import annotations

import os
from datetime import datetime, timezone

import boto3
from ulid import ULID

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ.get("DYNAMODB_TABLE", "expense-tracker"))


def handler(event: dict, context: object) -> dict:  # noqa: ARG001
    user_id = event["user_id"]
    receipt_id = event["receipt_id"]
    extracted = event["extracted"]
    category = event["category"]

    amount = extracted.get("amount")
    if amount is None:
        return {
            "user_id": user_id,
            "receipt_id": receipt_id,
            "saved": False,
            "error": "No amount extracted from receipt",
        }

    expense_id = str(ULID())
    now = datetime.now(timezone.utc).isoformat()
    month = now[:7]

    expense = {
        "pk": f"USER#{user_id}",
        "sk": f"EXP#{now}#{expense_id}",
        "id": expense_id,
        "amount": amount,
        "category": category,
        "store_name": extracted.get("store_name", ""),
        "memo": "",
        "receipt_id": receipt_id,
        "created_at": now,
    }
    table.put_item(Item=expense)

    # Update monthly summary
    try:
        table.update_item(
            Key={"pk": f"USER#{user_id}", "sk": f"SUM#{month}"},
            UpdateExpression=(
                "SET #total = if_not_exists(#total, :zero) + :amt, "
                "#cnt = if_not_exists(#cnt, :zero) + :one, "
                "#month = :month, "
                "#bycat.#cat = if_not_exists(#bycat.#cat, :zero) + :amt"
            ),
            ExpressionAttributeNames={
                "#total": "total",
                "#cnt": "expense_count",
                "#month": "month",
                "#bycat": "by_category",
                "#cat": category,
            },
            ExpressionAttributeValues={
                ":amt": amount,
                ":one": 1,
                ":zero": 0,
                ":month": month,
            },
        )
    except Exception:
        table.put_item(
            Item={
                "pk": f"USER#{user_id}",
                "sk": f"SUM#{month}",
                "month": month,
                "total": amount,
                "expense_count": 1,
                "by_category": {category: amount},
            }
        )

    # Update receipt status with OCR results
    table.update_item(
        Key={"pk": f"USER#{user_id}", "sk": f"RCV#{receipt_id}"},
        UpdateExpression="SET #status = :s, expense_id = :eid, store_name = :sn, amount = :amt, category = :cat",
        ExpressionAttributeNames={"#status": "status"},
        ExpressionAttributeValues={
            ":s": "completed",
            ":eid": expense_id,
            ":sn": extracted.get("store_name", ""),
            ":amt": amount,
            ":cat": category,
        },
    )

    return {
        "user_id": user_id,
        "receipt_id": receipt_id,
        "expense_id": expense_id,
        "amount": amount,
        "category": category,
        "month": month,
        "saved": True,
    }
