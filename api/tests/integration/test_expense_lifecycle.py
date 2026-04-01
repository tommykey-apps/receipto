"""Integration tests for expense CRUD lifecycle against DynamoDB Local."""

from __future__ import annotations

import pytest


pytestmark = pytest.mark.skipif(
    not pytest.importorskip("boto3", reason="boto3 required"),
    reason="skip guard",
)


def _create_expense(client, amount=500, category="food", store_name="セブン", memo="test"):
    resp = client.post(
        "/api/expenses",
        json={"amount": amount, "category": category, "store_name": store_name, "memo": memo},
    )
    assert resp.status_code == 201
    return resp.json()


class TestExpenseLifecycle:
    """End-to-end expense tests hitting real DynamoDB Local."""

    def test_create_expense_raw_item_has_lowercase_keys(self, client, table):
        """POST creates expense; raw DynamoDB item uses lowercase pk/sk."""
        expense = _create_expense(client)

        # Scan table to find the raw item
        scan = table.scan()
        exp_items = [
            item for item in scan["Items"]
            if item.get("sk", "").startswith("EXP#")
        ]
        assert len(exp_items) == 1

        raw = exp_items[0]
        # Verify lowercase pk/sk keys exist
        assert "pk" in raw
        assert "sk" in raw
        assert raw["pk"] == "USER#integration-test-user"
        assert raw["sk"].startswith("EXP#")
        assert expense["id"] in raw["sk"]

    def test_create_then_get_consistent(self, client, table):
        """POST then GET returns the same data."""
        created = _create_expense(client, amount=1200, category="transport")

        resp = client.get("/api/expenses")
        assert resp.status_code == 200
        expenses = resp.json()
        assert len(expenses) == 1

        fetched = expenses[0]
        assert fetched["id"] == created["id"]
        assert fetched["amount"] == 1200
        assert fetched["category"] == "transport"

    def test_create_update_get_reflects_changes(self, client, table):
        """POST then PUT then GET: updates reflected, unchanged fields preserved."""
        created = _create_expense(client, amount=800, category="food", store_name="ローソン", memo="lunch")

        # Update amount and memo only
        put_resp = client.put(
            f"/api/expenses/{created['id']}",
            json={"amount": 950, "memo": "dinner"},
        )
        assert put_resp.status_code == 200

        resp = client.get("/api/expenses")
        fetched = resp.json()[0]

        assert fetched["amount"] == 950
        assert fetched["memo"] == "dinner"
        # Unchanged fields preserved
        assert fetched["category"] == "food"
        assert fetched["store_name"] == "ローソン"

    def test_create_delete_summary_decremented(self, client, table):
        """POST then DELETE: monthly summary total decremented to 0."""
        created = _create_expense(client, amount=300, category="food")
        month = created["created_at"][:7]

        # Verify summary has the expense
        resp = client.get(f"/api/summary/monthly?month={month}")
        assert resp.status_code == 200
        summary = resp.json()
        assert summary["total"] == 300

        # Delete
        del_resp = client.delete(f"/api/expenses/{created['id']}")
        assert del_resp.status_code == 204

        # Summary should be decremented
        resp = client.get(f"/api/summary/monthly?month={month}")
        summary = resp.json()
        assert summary["total"] == 0
        assert summary["expense_count"] == 0

    def test_multiple_categories_summary(self, client, table):
        """3 expenses in different categories: summary has correct total and by_category."""
        e1 = _create_expense(client, amount=500, category="food")
        e2 = _create_expense(client, amount=1000, category="transport")
        e3 = _create_expense(client, amount=200, category="daily")

        month = e1["created_at"][:7]
        resp = client.get(f"/api/summary/monthly?month={month}")
        summary = resp.json()

        assert summary["total"] == 1700
        assert summary["expense_count"] == 3
        assert summary["by_category"]["food"] == 500
        assert summary["by_category"]["transport"] == 1000
        assert summary["by_category"]["daily"] == 200

    def test_month_isolation(self, client, table):
        """Expenses from different months are isolated by month filter."""
        # Create expense for current month
        created = _create_expense(client, amount=600, category="food")
        current_month = created["created_at"][:7]

        # Query with current month filter
        resp = client.get(f"/api/expenses?month={current_month}")
        assert len(resp.json()) == 1

        # Query with a different month
        resp = client.get("/api/expenses?month=2020-01")
        assert len(resp.json()) == 0
