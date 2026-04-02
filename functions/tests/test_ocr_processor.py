"""Tests for ocr_processor Lambda function."""

from __future__ import annotations

import importlib
import os
from unittest.mock import patch

import boto3

from ocr_processor import _parse_amount


# --- _parse_amount pure function tests ---

def test_parse_amount_yen_symbol():
    assert _parse_amount("¥1,500") == 1500


def test_parse_amount_fullwidth_yen():
    assert _parse_amount("￥2,000") == 2000


def test_parse_amount_en_suffix():
    assert _parse_amount("3000円") == 3000


def test_parse_amount_yen_with_space():
    assert _parse_amount("¥ 1,500") == 1500


def test_parse_amount_none():
    assert _parse_amount(None) is None


def test_parse_amount_non_numeric():
    assert _parse_amount("abc") is None


# --- handler tests ---

def _textract_response(vendor_name=None, total=None):
    """Build a fake Textract AnalyzeExpense response."""
    fields = []
    if vendor_name is not None:
        fields.append({
            "Type": {"Text": "VENDOR_NAME"},
            "ValueDetection": {"Text": vendor_name},
        })
    if total is not None:
        fields.append({
            "Type": {"Text": "TOTAL"},
            "ValueDetection": {"Text": total},
        })
    return {
        "ExpenseDocuments": [{"SummaryFields": fields}],
    }


def _setup_s3_buckets(monkeypatch):
    """Create source (Tokyo) and destination (us-east-1) S3 buckets for moto."""
    s3_tokyo = boto3.client("s3", region_name="ap-northeast-1")
    s3_tokyo.create_bucket(
        Bucket="test-bucket",
        CreateBucketConfiguration={"LocationConstraint": "ap-northeast-1"},
    )
    s3_tokyo.put_object(Bucket="test-bucket", Key="receipts/r1.jpg", Body=b"fake-image")
    s3_tokyo.put_object(Bucket="test-bucket", Key="receipts/r2.jpg", Body=b"fake-image")

    s3_us = boto3.client("s3", region_name="us-east-1")
    s3_us.create_bucket(Bucket="test-bucket-us")

    monkeypatch.setenv("RECEIPTS_BUCKET_US", "test-bucket-us")


def test_handler_with_vendor_and_total(aws, monkeypatch):
    """Textract returns VENDOR_NAME and TOTAL => ocr_success=True."""
    _setup_s3_buckets(monkeypatch)

    import ocr_processor
    importlib.reload(ocr_processor)

    mock_resp = _textract_response(vendor_name="セブンイレブン", total="¥1,500")
    with patch.object(ocr_processor.textract, "analyze_expense", return_value=mock_resp):
        event = {
            "bucket": "test-bucket",
            "s3_key": "receipts/r1.jpg",
            "receipt_id": "rcv-001",
            "user_id": "user-123",
        }
        result = ocr_processor.handler(event, None)

    assert result["ocr_success"] is True
    assert result["extracted"]["store_name"] == "セブンイレブン"
    assert result["extracted"]["amount"] == 1500


def test_handler_no_total(aws, monkeypatch):
    """Textract returns no TOTAL => ocr_success=False."""
    _setup_s3_buckets(monkeypatch)

    import ocr_processor
    importlib.reload(ocr_processor)

    mock_resp = _textract_response(vendor_name="セブンイレブン", total=None)
    with patch.object(ocr_processor.textract, "analyze_expense", return_value=mock_resp):
        event = {
            "bucket": "test-bucket",
            "s3_key": "receipts/r2.jpg",
            "receipt_id": "rcv-002",
            "user_id": "user-123",
        }
        result = ocr_processor.handler(event, None)

    assert result["ocr_success"] is False
    assert result["extracted"]["amount"] is None
