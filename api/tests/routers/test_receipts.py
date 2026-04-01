"""Tests for /api/receipts endpoints — 4 tests."""

from __future__ import annotations


def test_upload_receipt_returns_201(client):
    """POST /api/receipts/upload returns 201 with upload_url, receipt_id, s3_key."""
    resp = client.post("/api/receipts/upload", json={"filename": "receipt.jpg"})
    assert resp.status_code == 201
    data = resp.json()
    assert "upload_url" in data
    assert "receipt_id" in data
    assert "s3_key" in data
    assert data["upload_url"]  # non-empty


def test_upload_receipt_s3_key_format(client):
    """s3_key follows format: uploads/{user_id}/{receipt_id}/{filename}."""
    resp = client.post("/api/receipts/upload", json={"filename": "photo.png"})
    data = resp.json()
    s3_key = data["s3_key"]

    parts = s3_key.split("/")
    assert parts[0] == "uploads"
    assert parts[1] == "test-user"  # DEV_USER_ID
    assert parts[2] == data["receipt_id"]
    assert parts[3] == "photo.png"


def test_get_receipt_status_processing(client):
    """GET /api/receipts/{id} returns receipt with status='processing'."""
    upload = client.post("/api/receipts/upload", json={"filename": "receipt.jpg"})
    receipt_id = upload.json()["receipt_id"]

    resp = client.get(f"/api/receipts/{receipt_id}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "processing"
    assert resp.json()["id"] == receipt_id


def test_get_receipt_not_found_returns_404(client):
    """GET /api/receipts/{id} for non-existent returns 404."""
    resp = client.get("/api/receipts/nonexistent")
    assert resp.status_code == 404
