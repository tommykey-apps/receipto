"""Tests for /api/summary endpoints — 4 tests."""

from __future__ import annotations


def test_monthly_summary_empty(client):
    """GET /api/summary/monthly with no expenses returns zero-valued summary."""
    resp = client.get("/api/summary/monthly?month=2026-04")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert data["by_category"] == {}
    assert data["expense_count"] == 0


def test_monthly_summary_reflects_expenses(client):
    """After creating expenses, summary reflects correct totals."""
    client.post("/api/expenses", json={"amount": 1000, "category": "food"})
    client.post("/api/expenses", json={"amount": 2000, "category": "transport"})

    # Get the month from the created expenses
    expenses = client.get("/api/expenses").json()
    month = expenses[0]["created_at"][:7]

    resp = client.get(f"/api/summary/monthly?month={month}")
    data = resp.json()
    assert data["total"] == 3000
    assert data["expense_count"] == 2
    assert data["by_category"]["food"] == 1000
    assert data["by_category"]["transport"] == 2000


def test_trend_returns_n_months(client):
    """GET /api/summary/trend?months=N returns exactly N entries."""
    resp = client.get("/api/summary/trend?months=3")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 3


def test_trend_empty_months_have_zero_values(client):
    """Empty months in trend have total=0, expense_count=0, by_category={}."""
    resp = client.get("/api/summary/trend?months=4")
    data = resp.json()
    # All months should be present; those without expenses have zeros
    for entry in data:
        assert "month" in entry
        assert isinstance(entry["total"], int)
        assert isinstance(entry["expense_count"], int)
        assert isinstance(entry["by_category"], dict)
        # At minimum, check that zero-expense months have zero values
        if entry["expense_count"] == 0:
            assert entry["total"] == 0
            assert entry["by_category"] == {}
