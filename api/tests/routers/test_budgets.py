"""Tests for /api/budgets endpoints — 3 tests."""

from __future__ import annotations


def test_get_budgets_empty(client):
    """GET /api/budgets with no data returns empty list."""
    resp = client.get("/api/budgets?month=2026-04")
    assert resp.status_code == 200
    assert resp.json() == []


def test_put_budgets_stores_and_returns(client):
    """PUT /api/budgets stores budgets and returns them."""
    resp = client.put("/api/budgets?month=2026-04", json={
        "budgets": [
            {"category": "food", "amount": 50000, "alert_threshold_pct": 90},
            {"category": "transport", "amount": 10000},
        ]
    })
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    categories = {b["category"] for b in data}
    assert categories == {"food", "transport"}


def test_budgets_different_month_isolation(client):
    """Budgets for different months are isolated."""
    client.put("/api/budgets?month=2026-04", json={
        "budgets": [{"category": "food", "amount": 50000}]
    })
    client.put("/api/budgets?month=2026-05", json={
        "budgets": [{"category": "food", "amount": 60000}]
    })

    apr = client.get("/api/budgets?month=2026-04").json()
    may = client.get("/api/budgets?month=2026-05").json()
    assert len(apr) == 1
    assert apr[0]["amount"] == 50000
    assert len(may) == 1
    assert may[0]["amount"] == 60000
