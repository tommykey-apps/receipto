"""Tests for notifier Lambda function."""

from __future__ import annotations

import importlib

import boto3


def _make_event(user_id="user-123", month="2026-03", category="food",
                budget_amount=10000, current_spent=12000, pct_used=120.0):
    return {
        "user_id": user_id,
        "month": month,
        "category": category,
        "budget_amount": budget_amount,
        "current_spent": current_spent,
        "pct_used": pct_used,
    }


def test_valid_topic_publishes(sns_topic):
    """With a valid TOPIC_ARN, publishes to SNS and returns notified=True."""
    import notifier
    importlib.reload(notifier)
    # After reload, re-read the env var
    notifier.TOPIC_ARN = sns_topic
    notifier.sns = boto3.client("sns", region_name="ap-northeast-1")

    result = notifier.handler(_make_event(), None)
    assert result["notified"] is True


def test_empty_topic_arn_not_notified(aws):
    """Empty/missing TOPIC_ARN => notified=False."""
    import notifier
    importlib.reload(notifier)
    notifier.TOPIC_ARN = ""
    notifier.sns = boto3.client("sns", region_name="ap-northeast-1")

    result = notifier.handler(_make_event(), None)
    assert result["notified"] is False


def test_message_body_contains_details(sns_topic):
    """Published message contains category, budget amount, and percentage."""
    import notifier
    importlib.reload(notifier)
    notifier.TOPIC_ARN = sns_topic
    notifier.sns = boto3.client("sns", region_name="ap-northeast-1")

    # Subscribe and capture
    sqs = boto3.client("sqs", region_name="ap-northeast-1")
    queue_url = sqs.create_queue(QueueName="test-queue")["QueueUrl"]
    queue_arn = sqs.get_queue_attributes(
        QueueUrl=queue_url, AttributeNames=["QueueArn"]
    )["Attributes"]["QueueArn"]

    sns_client = boto3.client("sns", region_name="ap-northeast-1")
    sns_client.subscribe(TopicArn=sns_topic, Protocol="sqs", Endpoint=queue_arn)

    event = _make_event(category="food", budget_amount=10000, pct_used=120.0)
    notifier.handler(event, None)

    messages = sqs.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=1).get("Messages", [])
    assert len(messages) > 0
    body = messages[0]["Body"]
    assert "food" in body
    assert "10,000" in body
    assert "120.0" in body
