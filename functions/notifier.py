"""Send budget alert notification via SNS."""

from __future__ import annotations

import os

import boto3

sns = boto3.client("sns")
TOPIC_ARN = os.environ.get("BUDGET_ALERT_TOPIC_ARN", "")


def handler(event: dict, context: object) -> dict:  # noqa: ARG001
    user_id = event["user_id"]
    month = event["month"]
    category = event["category"]
    budget_amount = event["budget_amount"]
    current_spent = event["current_spent"]
    pct_used = event["pct_used"]

    subject = f"【家計簿】予算超過アラート - {category} ({month})"
    message = (
        f"予算超過のお知らせ\n\n"
        f"カテゴリ: {category}\n"
        f"対象月: {month}\n"
        f"予算額: ¥{budget_amount:,}\n"
        f"利用額: ¥{current_spent:,}\n"
        f"利用率: {pct_used}%\n\n"
        f"予算を見直すか、支出を抑えることをご検討ください。"
    )

    if TOPIC_ARN:
        sns.publish(
            TopicArn=TOPIC_ARN,
            Subject=subject,
            Message=message,
            MessageAttributes={
                "user_id": {"DataType": "String", "StringValue": user_id},
            },
        )

    return {
        "user_id": user_id,
        "notified": bool(TOPIC_ARN),
        "month": month,
        "category": category,
    }
