"""Generate weekly expense digest and send via SES."""

from __future__ import annotations

import os
from datetime import datetime, timezone

import boto3
from boto3.dynamodb.conditions import Key

ses = boto3.client("ses")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ.get("DYNAMODB_TABLE", "expense-tracker"))

SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "noreply@example.com")


def _format_currency(amount: int) -> str:
    return f"¥{amount:,}"


def handler(event: dict, context: object) -> dict:  # noqa: ARG001
    user_id = event["user_id"]
    email = event["email"]
    month = datetime.now(timezone.utc).strftime("%Y-%m")

    # Get monthly summary
    resp = table.get_item(Key={"PK": f"USER#{user_id}", "SK": f"SUM#{month}"})
    summary = resp.get("Item")

    if not summary:
        return {"user_id": user_id, "sent": False, "reason": "No expenses this month"}

    total = int(summary.get("total", 0))
    expense_count = int(summary.get("expense_count", 0))
    by_category = summary.get("by_category", {})

    # Get budgets
    budget_resp = table.query(
        KeyConditionExpression=Key("PK").eq(f"USER#{user_id}")
        & Key("SK").begins_with(f"BDG#{month}"),
    )
    budgets = {item["category"]: int(item["amount"]) for item in budget_resp.get("Items", [])}

    # Build category breakdown
    category_lines = []
    for cat, spent in sorted(by_category.items(), key=lambda x: int(x[1]), reverse=True):
        spent_int = int(spent)
        line = f"  {cat}: {_format_currency(spent_int)}"
        if cat in budgets:
            budget_amt = budgets[cat]
            pct = round(spent_int / budget_amt * 100, 1) if budget_amt > 0 else 0
            line += f" / {_format_currency(budget_amt)} ({pct}%)"
        category_lines.append(line)

    body = (
        f"週次支出レポート ({month})\n"
        f"{'=' * 40}\n\n"
        f"合計支出: {_format_currency(total)}\n"
        f"支出件数: {expense_count}件\n\n"
        f"カテゴリ別内訳:\n"
        + "\n".join(category_lines)
        + "\n"
    )

    ses.send_email(
        Source=SENDER_EMAIL,
        Destination={"ToAddresses": [email]},
        Message={
            "Subject": {"Data": f"【家計簿】週次レポート ({month})", "Charset": "UTF-8"},
            "Body": {"Text": {"Data": body, "Charset": "UTF-8"}},
        },
    )

    return {
        "user_id": user_id,
        "sent": True,
        "email": email,
        "total": total,
        "expense_count": expense_count,
    }
