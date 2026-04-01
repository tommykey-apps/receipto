"""Tests for budget_checker Lambda function."""

from __future__ import annotations

import importlib


def _make_event(user_id="user-123", month="2026-03", category="food", amount=1500):
    return {
        "user_id": user_id,
        "month": month,
        "category": category,
        "amount": amount,
    }


def test_no_budget_set(ddb_table):
    """No budget item => has_budget=False, budget_exceeded=False."""
    import budget_checker
    importlib.reload(budget_checker)
    budget_checker.table = ddb_table

    result = budget_checker.handler(_make_event(), None)
    assert result["has_budget"] is False
    assert result["budget_exceeded"] is False


def test_50_pct_used_threshold_80(ddb_table):
    """50% used with 80% threshold => budget_exceeded=False."""
    import budget_checker
    importlib.reload(budget_checker)
    budget_checker.table = ddb_table

    # Set budget: 10000, threshold 80%
    ddb_table.put_item(Item={
        "pk": "USER#user-123", "sk": "BDG#2026-03#food",
        "amount": 10000, "alert_threshold_pct": 80, "category": "food",
    })
    # Set summary: spent 5000 on food
    ddb_table.put_item(Item={
        "pk": "USER#user-123", "sk": "SUM#2026-03",
        "month": "2026-03", "total": 5000, "expense_count": 3,
        "by_category": {"food": 5000},
    })

    result = budget_checker.handler(_make_event(), None)
    assert result["budget_exceeded"] is False
    assert result["has_budget"] is True


def test_exactly_80_pct_exceeded(ddb_table):
    """Exactly 80% used with 80% threshold => budget_exceeded=True (>=)."""
    import budget_checker
    importlib.reload(budget_checker)
    budget_checker.table = ddb_table

    ddb_table.put_item(Item={
        "pk": "USER#user-123", "sk": "BDG#2026-03#food",
        "amount": 10000, "alert_threshold_pct": 80, "category": "food",
    })
    ddb_table.put_item(Item={
        "pk": "USER#user-123", "sk": "SUM#2026-03",
        "month": "2026-03", "total": 8000, "expense_count": 5,
        "by_category": {"food": 8000},
    })

    result = budget_checker.handler(_make_event(), None)
    assert result["budget_exceeded"] is True
    assert result["has_budget"] is True


def test_120_pct_exceeded(ddb_table):
    """120% used => budget_exceeded=True, pct_used=120.0."""
    import budget_checker
    importlib.reload(budget_checker)
    budget_checker.table = ddb_table

    ddb_table.put_item(Item={
        "pk": "USER#user-123", "sk": "BDG#2026-03#food",
        "amount": 10000, "alert_threshold_pct": 80, "category": "food",
    })
    ddb_table.put_item(Item={
        "pk": "USER#user-123", "sk": "SUM#2026-03",
        "month": "2026-03", "total": 12000, "expense_count": 8,
        "by_category": {"food": 12000},
    })

    result = budget_checker.handler(_make_event(), None)
    assert result["budget_exceeded"] is True
    assert result["pct_used"] == 120.0
