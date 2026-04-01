"""Tests for ocr_processor Lambda function."""

from __future__ import annotations

import importlib
from unittest.mock import patch

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


def test_handler_with_vendor_and_total(aws):
    """Textract returns VENDOR_NAME and TOTAL => ocr_success=True."""
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


def test_handler_no_total(aws):
    """Textract returns no TOTAL => ocr_success=False."""
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
