"""Tests for ocr_processor Lambda function."""

from __future__ import annotations

import importlib
import io
import json
from unittest.mock import MagicMock, patch

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


def test_parse_amount_integer():
    assert _parse_amount(970) == 970


def test_parse_amount_float():
    assert _parse_amount(1500.0) == 1500


# --- handler tests ---

def _bedrock_response(store_name=None, amount=None, date=None):
    """Build a fake Bedrock Claude response."""
    data = {
        "store_name": store_name,
        "amount": amount,
        "date": date,
    }
    body_content = json.dumps({
        "content": [{"type": "text", "text": json.dumps(data)}],
    })

    mock_resp = {
        "body": io.BytesIO(body_content.encode()),
    }
    return mock_resp


def _setup_s3_buckets(monkeypatch):
    """Create source S3 bucket with test images."""
    s3_tokyo = boto3.client("s3", region_name="ap-northeast-1")
    s3_tokyo.create_bucket(
        Bucket="test-bucket",
        CreateBucketConfiguration={"LocationConstraint": "ap-northeast-1"},
    )
    s3_tokyo.put_object(Bucket="test-bucket", Key="receipts/r1.jpg", Body=b"fake-image")
    s3_tokyo.put_object(Bucket="test-bucket", Key="receipts/r2.jpg", Body=b"fake-image")


def test_handler_with_store_and_amount(aws, monkeypatch):
    """Claude returns store_name and amount => ocr_success=True."""
    _setup_s3_buckets(monkeypatch)

    import ocr_processor
    importlib.reload(ocr_processor)

    mock_resp = _bedrock_response(store_name="マクドナルド", amount=970, date="2026-04-02")
    with patch.object(ocr_processor.bedrock, "invoke_model", return_value=mock_resp):
        event = {
            "bucket": "test-bucket",
            "s3_key": "receipts/r1.jpg",
            "receipt_id": "rcv-001",
            "user_id": "user-123",
        }
        result = ocr_processor.handler(event, None)

    assert result["ocr_success"] is True
    assert result["extracted"]["store_name"] == "マクドナルド"
    assert result["extracted"]["amount"] == 970
    assert result["extracted"]["date"] == "2026-04-02"


def test_handler_no_amount(aws, monkeypatch):
    """Claude returns no amount => ocr_success=False."""
    _setup_s3_buckets(monkeypatch)

    import ocr_processor
    importlib.reload(ocr_processor)

    mock_resp = _bedrock_response(store_name="不明な店", amount=None, date=None)
    with patch.object(ocr_processor.bedrock, "invoke_model", return_value=mock_resp):
        event = {
            "bucket": "test-bucket",
            "s3_key": "receipts/r2.jpg",
            "receipt_id": "rcv-002",
            "user_id": "user-123",
        }
        result = ocr_processor.handler(event, None)

    assert result["ocr_success"] is False
    assert result["extracted"]["amount"] is None
