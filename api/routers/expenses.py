from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from ulid import ULID

from auth import get_user_id
from models.schemas import Expense, ExpenseCreate, ExpenseUpdate
from store.dynamodb import DynamoDBStore

router = APIRouter(tags=["expenses"])
store = DynamoDBStore()


@router.get("/expenses", response_model=list[Expense])
def list_expenses(
    month: str | None = None,
    category: str | None = None,
    user_id: str = Depends(get_user_id),
) -> list[Expense]:
    return store.get_expenses(user_id, month=month, category=category)


@router.post("/expenses", response_model=Expense, status_code=201)
def create_expense(
    body: ExpenseCreate,
    user_id: str = Depends(get_user_id),
) -> Expense:
    expense_id = str(ULID())
    expense = store.put_expense(user_id, expense_id, body)

    # Update monthly summary
    month = expense.created_at[:7]  # YYYY-MM
    store.update_monthly_summary(user_id, month, body.amount, body.category)

    return expense


@router.put("/expenses/{expense_id}", response_model=Expense)
def update_expense(
    expense_id: str,
    body: ExpenseUpdate,
    user_id: str = Depends(get_user_id),
) -> Expense:
    data = body.model_dump(exclude_none=True)
    if not data:
        raise HTTPException(status_code=400, detail="No fields to update")

    expense = store.update_expense(user_id, expense_id, data)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    return expense


@router.delete("/expenses/{expense_id}", status_code=204)
def delete_expense(
    expense_id: str,
    user_id: str = Depends(get_user_id),
) -> None:
    expense = store.delete_expense(user_id, expense_id)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")

    # Decrement monthly summary
    month = expense.created_at[:7]
    store.decrement_monthly_summary(user_id, month, expense.amount, expense.category)
