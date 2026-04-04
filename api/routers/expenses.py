from __future__ import annotations

import logging
import os

import boto3
from fastapi import APIRouter, Depends, HTTPException
from ulid import ULID

from auth import get_user_id
from models.schemas import Expense, ExpenseCreate, ExpenseUpdate
from store.dynamodb import DynamoDBStore

router = APIRouter(tags=["expenses"])
store = DynamoDBStore()
logger = logging.getLogger(__name__)


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

    # Budget check + alert (best-effort, don't fail the request)
    try:
        _check_budget_alert(user_id, month, body.category)
    except Exception:
        logger.exception("Budget alert check failed")

    return expense


def _check_budget_alert(user_id: str, month: str, category: str) -> None:
    """Check if spending exceeds budget threshold and send SNS alert."""
    budget = store.get_budgets(user_id, month)
    matching = [b for b in budget if b.category == category]
    if not matching:
        return

    b = matching[0]
    summary = store.get_monthly_summary(user_id, month)
    if not summary:
        return

    current_spent = summary.by_category.get(category, 0)
    if b.amount <= 0:
        return

    pct_used = current_spent / b.amount * 100
    if pct_used < b.alert_threshold_pct:
        return

    topic_arn = os.environ.get("SNS_TOPIC_ARN", "")
    if not topic_arn:
        return

    sns = boto3.client("sns")
    sns.publish(
        TopicArn=topic_arn,
        Subject=f"【家計簿】予算超過アラート - {category} ({month})",
        Message=(
            f"予算超過のお知らせ\n\n"
            f"カテゴリ: {category}\n"
            f"対象月: {month}\n"
            f"予算額: ¥{b.amount:,}\n"
            f"利用額: ¥{current_spent:,}\n"
            f"利用率: {pct_used:.1f}%\n\n"
            f"予算を見直すか、支出を抑えることをご検討ください。"
        ),
    )


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
