"""Integration tests for budget and summary endpoints against DynamoDB Local."""

from __future__ import annotations

from datetime import datetime, timezone

from dateutil.relativedelta import relativedelta

import pytest


def _current_month() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


class TestBudgetSummary:
    """Budget + summary integration tests."""

    def test_put_budgets_then_get(self, client, table):
        """PUT budgets then GET returns them."""
        month = _current_month()
        put_resp = client.put(
            f"/api/budgets?month={month}",
            json={
                "budgets": [
                    {"category": "food", "amount": 50000, "alert_threshold_pct": 80},
                    {"category": "transport", "amount": 10000, "alert_threshold_pct": 90},
                ]
            },
        )
        assert put_resp.status_code == 200
        budgets = put_resp.json()
        assert len(budgets) == 2

        get_resp = client.get(f"/api/budgets?month={month}")
        assert get_resp.status_code == 200
        fetched = get_resp.json()
        categories = {b["category"] for b in fetched}
        assert categories == {"food", "transport"}

    def test_budget_month_isolation(self, client, table):
        """Budgets in one month are not visible in another."""
        client.put(
            "/api/budgets?month=2025-01",
            json={"budgets": [{"category": "food", "amount": 30000}]},
        )
        client.put(
            "/api/budgets?month=2025-02",
            json={"budgets": [{"category": "transport", "amount": 15000}]},
        )

        jan = client.get("/api/budgets?month=2025-01").json()
        feb = client.get("/api/budgets?month=2025-02").json()

        assert len(jan) == 1
        assert jan[0]["category"] == "food"
        assert len(feb) == 1
        assert feb[0]["category"] == "transport"

    def test_expense_updates_summary_not_budget(self, client, table):
        """Creating an expense updates monthly summary but does NOT change budget."""
        month = _current_month()

        # Set budget
        client.put(
            f"/api/budgets?month={month}",
            json={"budgets": [{"category": "food", "amount": 50000}]},
        )

        # Create expense
        client.post(
            "/api/expenses",
            json={"amount": 1500, "category": "food", "store_name": "test"},
        )

        # Summary should reflect expense
        summary = client.get(f"/api/summary/monthly?month={month}").json()
        assert summary["total"] == 1500
        assert summary["by_category"]["food"] == 1500

        # Budget should NOT change
        budgets = client.get(f"/api/budgets?month={month}").json()
        assert budgets[0]["amount"] == 50000

    def test_trend_returns_correct_months(self, client, table):
        """Trend endpoint returns the requested number of months."""
        resp = client.get("/api/summary/trend?months=3")
        assert resp.status_code == 200
        trend = resp.json()
        assert len(trend) == 3

        # Should include current month and 2 previous
        now = datetime.now(timezone.utc)
        expected_months = []
        for i in range(3):
            dt = now - relativedelta(months=i)
            expected_months.append(dt.strftime("%Y-%m"))

        actual_months = [s["month"] for s in trend]
        assert actual_months == expected_months
