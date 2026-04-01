"""Tests for Pydantic models in models/schemas.py — 10 tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from models.schemas import (
    Budget,
    Category,
    ExpenseCreate,
    ExpenseUpdate,
    MonthlySummary,
    PresignedUrlResponse,
    UploadRequest,
)


# ── ExpenseCreate ──

def test_expense_create_required_fields():
    """amount and category are required; store_name and memo default to empty."""
    ec = ExpenseCreate(amount=1500, category="food")
    assert ec.amount == 1500
    assert ec.category == "food"
    assert ec.store_name == ""
    assert ec.memo == ""


def test_expense_create_missing_amount():
    """Missing amount raises ValidationError."""
    with pytest.raises(ValidationError):
        ExpenseCreate(category="food")


def test_expense_create_missing_category():
    """Missing category raises ValidationError."""
    with pytest.raises(ValidationError):
        ExpenseCreate(amount=500)


# ── ExpenseUpdate ──

def test_expense_update_all_optional():
    """All fields are optional; empty model is valid."""
    eu = ExpenseUpdate()
    assert eu.amount is None
    assert eu.category is None
    assert eu.store_name is None
    assert eu.memo is None


def test_expense_update_partial_fields():
    """Partial fields work correctly."""
    eu = ExpenseUpdate(amount=2000, memo="updated")
    assert eu.amount == 2000
    assert eu.memo == "updated"
    assert eu.category is None
    assert eu.store_name is None


# ── Budget ──

def test_budget_alert_threshold_default():
    """alert_threshold_pct defaults to 80."""
    b = Budget(category="food", amount=50000)
    assert b.alert_threshold_pct == 80


# ── Category ──

def test_category_defaults():
    """icon defaults to 'tag', sort_order defaults to 0."""
    c = Category(name="custom", display_name="Custom")
    assert c.icon == "tag"
    assert c.sort_order == 0


# ── MonthlySummary ──

def test_monthly_summary_all_required():
    """All fields are required for MonthlySummary."""
    ms = MonthlySummary(month="2026-04", total=10000, by_category={"food": 5000}, expense_count=3)
    assert ms.month == "2026-04"
    assert ms.total == 10000
    assert ms.by_category == {"food": 5000}
    assert ms.expense_count == 3


# ── UploadRequest ──

def test_upload_request_content_type_default():
    """content_type defaults to 'image/jpeg'."""
    ur = UploadRequest(filename="receipt.jpg")
    assert ur.content_type == "image/jpeg"


# ── PresignedUrlResponse ──

def test_presigned_url_response_all_required():
    """All 3 fields are required for PresignedUrlResponse."""
    pr = PresignedUrlResponse(
        upload_url="https://s3.example.com/upload",
        receipt_id="rcpt-123",
        s3_key="uploads/user/rcpt-123/file.jpg",
    )
    assert pr.upload_url == "https://s3.example.com/upload"
    assert pr.receipt_id == "rcpt-123"
    assert pr.s3_key == "uploads/user/rcpt-123/file.jpg"
