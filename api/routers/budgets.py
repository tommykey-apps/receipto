from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from auth import get_user_id
from models.schemas import Budget, BudgetUpdate
from store.dynamodb import DynamoDBStore

router = APIRouter(tags=["budgets"])
store = DynamoDBStore()


def _current_month() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


@router.get("/budgets", response_model=list[Budget])
def list_budgets(
    month: str | None = None,
    user_id: str = Depends(get_user_id),
) -> list[Budget]:
    month = month or _current_month()
    return store.get_budgets(user_id, month)


@router.put("/budgets", response_model=list[Budget])
def update_budgets(
    body: BudgetUpdate,
    month: str | None = None,
    user_id: str = Depends(get_user_id),
) -> list[Budget]:
    month = month or _current_month()
    for budget in body.budgets:
        store.put_budget(user_id, month, budget)
    return store.get_budgets(user_id, month)
