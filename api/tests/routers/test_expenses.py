"""Tests for /api/expenses endpoints — 9 tests."""

from __future__ import annotations


def test_create_expense_returns_201(client):
    """POST /api/expenses returns 201 with Expense JSON."""
    resp = client.post("/api/expenses", json={"amount": 1500, "category": "food", "store_name": "Lawson"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["amount"] == 1500
    assert data["category"] == "food"
    assert data["store_name"] == "Lawson"
    assert "id" in data
    assert "created_at" in data


def test_create_expense_updates_monthly_summary(client):
    """POST /api/expenses also updates the monthly summary."""
    resp = client.post("/api/expenses", json={"amount": 1000, "category": "food"})
    assert resp.status_code == 201
    month = resp.json()["created_at"][:7]

    summary = client.get(f"/api/summary/monthly?month={month}")
    assert summary.status_code == 200
    assert summary.json()["total"] == 1000
    assert summary.json()["expense_count"] == 1


def test_list_expenses_empty(client):
    """GET /api/expenses with no data returns empty list."""
    resp = client.get("/api/expenses")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_expenses_after_creates(client):
    """GET /api/expenses returns all created expenses."""
    client.post("/api/expenses", json={"amount": 100, "category": "food"})
    client.post("/api/expenses", json={"amount": 200, "category": "transport"})

    resp = client.get("/api/expenses")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_list_expenses_month_filter(client):
    """GET /api/expenses?month=YYYY-MM filters by month."""
    r = client.post("/api/expenses", json={"amount": 100, "category": "food"})
    month = r.json()["created_at"][:7]

    resp = client.get(f"/api/expenses?month={month}")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1

    resp_empty = client.get("/api/expenses?month=1999-01")
    assert resp_empty.json() == []


def test_update_expense_success(client):
    """PUT /api/expenses/{id} updates and returns the expense."""
    r = client.post("/api/expenses", json={"amount": 100, "category": "food"})
    eid = r.json()["id"]

    resp = client.put(f"/api/expenses/{eid}", json={"amount": 999, "memo": "updated"})
    assert resp.status_code == 200
    assert resp.json()["amount"] == 999
    assert resp.json()["memo"] == "updated"


def test_update_expense_empty_body_returns_400(client):
    """PUT with empty body (no updatable fields) returns 400."""
    r = client.post("/api/expenses", json={"amount": 100, "category": "food"})
    eid = r.json()["id"]

    resp = client.put(f"/api/expenses/{eid}", json={})
    assert resp.status_code == 400


def test_update_expense_not_found_returns_404(client):
    """PUT on non-existent expense returns 404."""
    resp = client.put("/api/expenses/nonexistent", json={"amount": 500})
    assert resp.status_code == 404


def test_delete_expense_decrements_summary(client):
    """DELETE /api/expenses/{id} decrements the monthly summary."""
    r = client.post("/api/expenses", json={"amount": 1000, "category": "food"})
    eid = r.json()["id"]
    month = r.json()["created_at"][:7]

    resp = client.delete(f"/api/expenses/{eid}")
    assert resp.status_code == 204

    summary = client.get(f"/api/summary/monthly?month={month}")
    assert summary.json()["total"] == 0
    assert summary.json()["expense_count"] == 0
