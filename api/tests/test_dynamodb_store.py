"""Tests for DynamoDBStore — 20 tests covering all methods."""

from __future__ import annotations

from models.schemas import Budget, Category, ExpenseCreate


USER = "test-user"


# ── Expenses ──

def test_put_and_get_expense(store):
    """put_expense creates an expense retrievable by get_expense."""
    data = ExpenseCreate(amount=1200, category="food", store_name="Lawson", memo="lunch")
    expense = store.put_expense(USER, "exp-001", data)

    assert expense.id == "exp-001"
    assert expense.amount == 1200
    assert expense.category == "food"
    assert expense.store_name == "Lawson"
    assert expense.memo == "lunch"
    assert expense.created_at  # non-empty ISO string

    fetched = store.get_expense(USER, "exp-001")
    assert fetched is not None
    assert fetched.id == "exp-001"
    assert fetched.amount == 1200


def test_get_expenses_all(store):
    """get_expenses returns all expenses for a user."""
    store.put_expense(USER, "e1", ExpenseCreate(amount=100, category="food"))
    store.put_expense(USER, "e2", ExpenseCreate(amount=200, category="transport"))

    expenses = store.get_expenses(USER)
    assert len(expenses) == 2
    ids = {e.id for e in expenses}
    assert ids == {"e1", "e2"}


def test_get_expenses_month_filter(store):
    """get_expenses with month filter only returns matching expenses."""
    e1 = store.put_expense(USER, "e1", ExpenseCreate(amount=100, category="food"))
    # The created_at is auto-generated with current time; we'll filter by its month
    month = e1.created_at[:7]

    result = store.get_expenses(USER, month=month)
    assert len(result) >= 1
    assert all(r.created_at.startswith(month) for r in result)

    # A different month should return nothing
    result_empty = store.get_expenses(USER, month="1999-01")
    assert len(result_empty) == 0


def test_get_expenses_category_filter(store):
    """get_expenses with category filter only returns matching category."""
    store.put_expense(USER, "e1", ExpenseCreate(amount=100, category="food"))
    store.put_expense(USER, "e2", ExpenseCreate(amount=200, category="transport"))

    food_only = store.get_expenses(USER, category="food")
    assert len(food_only) == 1
    assert food_only[0].category == "food"


def test_get_expense_not_found(store):
    """get_expense returns None for non-existent expense."""
    assert store.get_expense(USER, "nonexistent") is None


def test_update_expense(store):
    """update_expense modifies fields and returns updated expense."""
    store.put_expense(USER, "e1", ExpenseCreate(amount=100, category="food"))

    updated = store.update_expense(USER, "e1", {"amount": 999, "memo": "changed"})
    assert updated is not None
    assert updated.amount == 999
    assert updated.memo == "changed"
    assert updated.category == "food"  # unchanged field preserved


def test_delete_expense(store):
    """delete_expense removes the expense and returns it."""
    store.put_expense(USER, "e1", ExpenseCreate(amount=100, category="food"))

    deleted = store.delete_expense(USER, "e1")
    assert deleted is not None
    assert deleted.id == "e1"

    # Should be gone now
    assert store.get_expense(USER, "e1") is None


# ── Receipts ──

def test_put_and_get_receipt(store):
    """put_receipt stores a receipt retrievable by get_receipt."""
    receipt = store.put_receipt(USER, "rcpt-001", "uploads/test-user/rcpt-001/photo.jpg", "photo.jpg")

    assert receipt["id"] == "rcpt-001"
    assert receipt["s3_key"] == "uploads/test-user/rcpt-001/photo.jpg"
    assert receipt["status"] == "processing"

    fetched = store.get_receipt(USER, "rcpt-001")
    assert fetched is not None
    assert fetched["id"] == "rcpt-001"


def test_get_receipt_not_found(store):
    """get_receipt returns None for non-existent receipt."""
    assert store.get_receipt(USER, "nonexistent") is None


# ── Categories ──

def test_put_and_get_category(store):
    """put_category stores a category retrievable by get_categories."""
    cat = Category(name="custom", display_name="Custom Cat", icon="star", sort_order=5)
    store.put_category(USER, cat)

    cats = store.get_categories(USER)
    assert len(cats) == 1
    assert cats[0].name == "custom"
    assert cats[0].display_name == "Custom Cat"
    assert cats[0].icon == "star"
    assert cats[0].sort_order == 5


def test_init_default_categories_creates_10(store):
    """init_default_categories creates exactly 10 categories."""
    defaults = store.init_default_categories(USER)
    assert len(defaults) == 10

    stored = store.get_categories(USER)
    assert len(stored) == 10


def test_init_default_categories_idempotent(store):
    """Calling init_default_categories twice does not duplicate."""
    store.init_default_categories(USER)
    store.init_default_categories(USER)

    stored = store.get_categories(USER)
    assert len(stored) == 10


# ── Budgets ──

def test_put_and_get_budget(store):
    """put_budget stores a budget retrievable by get_budgets."""
    budget = Budget(category="food", amount=50000, alert_threshold_pct=90)
    store.put_budget(USER, "2026-04", budget)

    budgets = store.get_budgets(USER, "2026-04")
    assert len(budgets) == 1
    assert budgets[0].category == "food"
    assert budgets[0].amount == 50000
    assert budgets[0].alert_threshold_pct == 90


def test_budget_month_isolation(store):
    """Budgets for different months are isolated."""
    store.put_budget(USER, "2026-04", Budget(category="food", amount=50000))
    store.put_budget(USER, "2026-05", Budget(category="food", amount=60000))

    apr = store.get_budgets(USER, "2026-04")
    may = store.get_budgets(USER, "2026-05")
    assert len(apr) == 1
    assert apr[0].amount == 50000
    assert len(may) == 1
    assert may[0].amount == 60000


# ── Monthly Summary ──

def test_monthly_summary_not_found(store):
    """get_monthly_summary returns None when no summary exists."""
    assert store.get_monthly_summary(USER, "2026-04") is None


def test_update_monthly_summary_creates_new(store):
    """update_monthly_summary creates a new summary if none exists."""
    store.update_monthly_summary(USER, "2026-04", 1000, "food")

    summary = store.get_monthly_summary(USER, "2026-04")
    assert summary is not None
    assert summary.total == 1000
    assert summary.expense_count == 1
    assert summary.by_category == {"food": 1000}


def test_update_monthly_summary_increments(store):
    """update_monthly_summary increments existing totals."""
    store.update_monthly_summary(USER, "2026-04", 1000, "food")
    store.update_monthly_summary(USER, "2026-04", 500, "food")

    summary = store.get_monthly_summary(USER, "2026-04")
    assert summary is not None
    assert summary.total == 1500
    assert summary.expense_count == 2
    assert summary.by_category["food"] == 1500


def test_update_monthly_summary_multiple_categories(store):
    """update_monthly_summary tracks multiple categories independently."""
    store.update_monthly_summary(USER, "2026-04", 1000, "food")
    store.update_monthly_summary(USER, "2026-04", 2000, "transport")

    summary = store.get_monthly_summary(USER, "2026-04")
    assert summary is not None
    assert summary.total == 3000
    assert summary.expense_count == 2
    assert summary.by_category["food"] == 1000
    assert summary.by_category["transport"] == 2000


def test_increment_then_decrement_nets_zero(store):
    """Incrementing then decrementing the same amount nets to zero."""
    store.update_monthly_summary(USER, "2026-04", 1000, "food")
    store.decrement_monthly_summary(USER, "2026-04", 1000, "food")

    summary = store.get_monthly_summary(USER, "2026-04")
    assert summary is not None
    assert summary.total == 0
    assert summary.expense_count == 0
    assert summary.by_category["food"] == 0


def test_decrement_nonexistent_is_noop(store):
    """Decrementing a non-existent summary is a no-op (no error)."""
    # Should not raise
    store.decrement_monthly_summary(USER, "2026-04", 1000, "food")
    # Summary should still not exist
    assert store.get_monthly_summary(USER, "2026-04") is None
