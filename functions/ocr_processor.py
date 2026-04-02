"""Extract expense data from receipt using Amazon Textract AnalyzeExpense."""

from __future__ import annotations

import os
import re

import boto3

# Lambda runs in us-east-1 alongside Textract — no cross-region needed
textract = boto3.client("textract")


def _extract_field(expense_fields: list[dict], field_type: str) -> str | None:
    for field in expense_fields:
        ft = field.get("Type", {}).get("Text", "")
        if ft == field_type:
            return field.get("ValueDetection", {}).get("Text")
    return None


def _parse_amount(raw: str | None) -> int | None:
    """Parse amount string to integer yen value."""
    if not raw:
        return None
    cleaned = re.sub(r"[¥￥,、円\s]", "", raw)
    try:
        return int(float(cleaned))
    except ValueError:
        return None


def handler(event: dict, context: object) -> dict:  # noqa: ARG001
    s3_key = event["s3_key"]
    receipt_id = event["receipt_id"]
    user_id = event["user_id"]

    # Use the us-east-1 replica bucket (S3Object reference, 10MB limit)
    us_bucket = os.environ.get("RECEIPTS_BUCKET_US", event.get("bucket", ""))

    resp = textract.analyze_expense(
        Document={"S3Object": {"Bucket": us_bucket, "Name": s3_key}}
    )

    store_name = None
    total_amount = None
    date = None

    for doc in resp.get("ExpenseDocuments", []):
        summary_fields = doc.get("SummaryFields", [])
        vendor = _extract_field(summary_fields, "VENDOR_NAME")
        if vendor:
            store_name = vendor

        total = _extract_field(summary_fields, "TOTAL")
        if total:
            total_amount = _parse_amount(total)

        invoice_date = _extract_field(summary_fields, "INVOICE_RECEIPT_DATE")
        if invoice_date:
            date = invoice_date

    return {
        "receipt_id": receipt_id,
        "user_id": user_id,
        "bucket": event.get("bucket", ""),
        "s3_key": s3_key,
        "extracted": {
            "store_name": store_name or "",
            "amount": total_amount,
            "date": date,
        },
        "ocr_success": total_amount is not None,
    }
