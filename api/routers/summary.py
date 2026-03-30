from __future__ import annotations

from datetime import datetime, timezone

from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, Depends

from auth import get_user_id
from models.schemas import MonthlySummary
from store.dynamodb import DynamoDBStore

router = APIRouter(tags=["summary"])
store = DynamoDBStore()


def _current_month() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


def _empty_summary(month: str) -> MonthlySummary:
    return MonthlySummary(month=month, total=0, by_category={}, expense_count=0)


@router.get("/summary/monthly", response_model=MonthlySummary)
def monthly_summary(
    month: str | None = None,
    user_id: str = Depends(get_user_id),
) -> MonthlySummary:
    month = month or _current_month()
    summary = store.get_monthly_summary(user_id, month)
    return summary or _empty_summary(month)


@router.get("/summary/trend", response_model=list[MonthlySummary])
def trend(
    months: int = 6,
    user_id: str = Depends(get_user_id),
) -> list[MonthlySummary]:
    now = datetime.now(timezone.utc)
    results: list[MonthlySummary] = []
    for i in range(months):
        dt = now - relativedelta(months=i)
        m = dt.strftime("%Y-%m")
        summary = store.get_monthly_summary(user_id, m)
        results.append(summary or _empty_summary(m))
    return results
