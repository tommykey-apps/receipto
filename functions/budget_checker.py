"""Check if monthly spending exceeds budget thresholds."""

from __future__ import annotations

import os

import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ.get("DYNAMODB_TABLE", "expense-tracker"))


def handler(event: dict, context: object) -> dict:  # noqa: ARG001
    user_id = event["user_id"]
    month = event["month"]
    category = event["category"]
    amount = event["amount"]

    # Get budget for this category and month
    resp = table.query(
        KeyConditionExpression=Key("pk").eq(f"USER#{user_id}")
        & Key("sk").eq(f"BDG#{month}#{category}"),
    )
    items = resp.get("Items", [])

    if not items:
        return {
            "user_id": user_id,
            "month": month,
            "category": category,
            "budget_exceeded": False,
            "has_budget": False,
        }

    budget = items[0]
    budget_amount = int(budget["amount"])
    threshold_pct = int(budget.get("alert_threshold_pct", 80))

    # Get current monthly summary
    summary_resp = table.get_item(
        Key={"pk": f"USER#{user_id}", "sk": f"SUM#{month}"}
    )
    summary = summary_resp.get("Item", {})
    by_category = summary.get("by_category", {})
    current_spent = int(by_category.get(category, 0))

    pct_used = (current_spent / budget_amount * 100) if budget_amount > 0 else 0
    exceeded = pct_used >= threshold_pct

    return {
        "user_id": user_id,
        "month": month,
        "category": category,
        "budget_amount": budget_amount,
        "current_spent": current_spent,
        "pct_used": round(pct_used, 1),
        "threshold_pct": threshold_pct,
        "budget_exceeded": exceeded,
        "has_budget": True,
    }
