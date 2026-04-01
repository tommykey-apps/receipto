"""Tests for receipt_validator Lambda function."""

from __future__ import annotations

import importlib

import boto3


def _make_event(bucket="test-receipts", s3_key="receipts/test.jpg",
                receipt_id="rcv-001", user_id="user-123"):
    return {
        "bucket": bucket,
        "s3_key": s3_key,
        "receipt_id": receipt_id,
        "user_id": user_id,
    }


def test_valid_jpeg_under_10mb(s3_bucket):
    """Valid JPEG under 10MB should return valid=True."""
    s3 = boto3.client("s3", region_name="ap-northeast-1")
    s3.put_object(Bucket=s3_bucket, Key="receipts/test.jpg",
                  Body=b"x" * 1000, ContentType="image/jpeg")

    import receipt_validator
    importlib.reload(receipt_validator)

    result = receipt_validator.handler(_make_event(bucket=s3_bucket), None)
    assert result["valid"] is True
    assert result["error"] is None


def test_valid_pdf(s3_bucket):
    """Valid PDF should return valid=True."""
    s3 = boto3.client("s3", region_name="ap-northeast-1")
    s3.put_object(Bucket=s3_bucket, Key="receipts/test.jpg",
                  Body=b"%PDF-1.4 fake", ContentType="application/pdf")

    import receipt_validator
    importlib.reload(receipt_validator)

    result = receipt_validator.handler(_make_event(bucket=s3_bucket), None)
    assert result["valid"] is True


def test_invalid_content_type(s3_bucket):
    """text/plain should return valid=False with error message."""
    s3 = boto3.client("s3", region_name="ap-northeast-1")
    s3.put_object(Bucket=s3_bucket, Key="receipts/test.jpg",
                  Body=b"hello", ContentType="text/plain")

    import receipt_validator
    importlib.reload(receipt_validator)

    result = receipt_validator.handler(_make_event(bucket=s3_bucket), None)
    assert result["valid"] is False
    assert "text/plain" in result["error"]


def test_file_exceeds_10mb(s3_bucket):
    """File larger than 10MB should return valid=False."""
    s3 = boto3.client("s3", region_name="ap-northeast-1")
    big_body = b"x" * (10 * 1024 * 1024 + 1)
    s3.put_object(Bucket=s3_bucket, Key="receipts/test.jpg",
                  Body=big_body, ContentType="image/jpeg")

    import receipt_validator
    importlib.reload(receipt_validator)

    result = receipt_validator.handler(_make_event(bucket=s3_bucket), None)
    assert result["valid"] is False


def test_output_contains_passthrough_fields(s3_bucket):
    """Output should contain receipt_id, user_id, bucket, s3_key."""
    s3 = boto3.client("s3", region_name="ap-northeast-1")
    s3.put_object(Bucket=s3_bucket, Key="receipts/test.jpg",
                  Body=b"img", ContentType="image/jpeg")

    import receipt_validator
    importlib.reload(receipt_validator)

    event = _make_event(bucket=s3_bucket, receipt_id="rcv-xyz", user_id="usr-abc")
    result = receipt_validator.handler(event, None)
    assert result["receipt_id"] == "rcv-xyz"
    assert result["user_id"] == "usr-abc"
    assert result["bucket"] == s3_bucket
    assert result["s3_key"] == "receipts/test.jpg"
