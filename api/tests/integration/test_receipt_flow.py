"""Integration tests for receipt upload flow against DynamoDB Local."""

from __future__ import annotations

import pytest


class TestReceiptFlow:
    """Receipt upload and retrieval tests."""

    def test_upload_receipt_stored_processing(self, client, table):
        """POST upload: receipt stored with status='processing'."""
        resp = client.post(
            "/api/receipts/upload",
            json={"filename": "receipt.jpg", "content_type": "image/jpeg"},
        )
        assert resp.status_code == 201
        data = resp.json()

        receipt_id = data["receipt_id"]
        assert receipt_id
        assert data["upload_url"]
        assert data["s3_key"]

        # Verify raw item in DynamoDB
        raw_items = table.scan()["Items"]
        rcv_items = [i for i in raw_items if i.get("sk", "").startswith("RCV#")]
        assert len(rcv_items) == 1
        assert rcv_items[0]["status"] == "processing"
        assert rcv_items[0]["filename"] == "receipt.jpg"

    def test_upload_then_get_receipt(self, client, table):
        """POST upload then GET returns the receipt."""
        upload_resp = client.post(
            "/api/receipts/upload",
            json={"filename": "photo.png", "content_type": "image/png"},
        )
        receipt_id = upload_resp.json()["receipt_id"]

        get_resp = client.get(f"/api/receipts/{receipt_id}")
        assert get_resp.status_code == 200
        receipt = get_resp.json()
        assert receipt["id"] == receipt_id
        assert receipt["filename"] == "photo.png"
        assert receipt["status"] == "processing"

    def test_get_nonexistent_receipt_404(self, client, table):
        """GET non-existent receipt returns 404."""
        resp = client.get("/api/receipts/nonexistent-id-12345")
        assert resp.status_code == 404
