"""Validate uploaded receipt file format by checking S3 object Content-Type."""

from __future__ import annotations

import boto3

ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "application/pdf",
}

s3 = boto3.client("s3")


def handler(event: dict, context: object) -> dict:  # noqa: ARG001
    bucket = event["bucket"]
    s3_key = event["s3_key"]
    receipt_id = event["receipt_id"]
    user_id = event["user_id"]

    head = s3.head_object(Bucket=bucket, Key=s3_key)
    content_type = head.get("ContentType", "")
    content_length = head.get("ContentLength", 0)

    valid = content_type in ALLOWED_CONTENT_TYPES
    max_size = 10 * 1024 * 1024  # 10MB

    if content_length > max_size:
        valid = False

    return {
        "receipt_id": receipt_id,
        "user_id": user_id,
        "bucket": bucket,
        "s3_key": s3_key,
        "content_type": content_type,
        "content_length": content_length,
        "valid": valid,
        "error": None if valid else f"Invalid file: type={content_type}, size={content_length}",
    }
