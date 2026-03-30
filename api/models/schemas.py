from __future__ import annotations

from pydantic import BaseModel


class Expense(BaseModel):
    id: str
    amount: int  # 円 (整数)
    category: str
    store_name: str = ""
    memo: str = ""
    receipt_id: str | None = None
    created_at: str  # ISO8601


class ExpenseCreate(BaseModel):
    amount: int
    category: str
    store_name: str = ""
    memo: str = ""


class ExpenseUpdate(BaseModel):
    amount: int | None = None
    category: str | None = None
    store_name: str | None = None
    memo: str | None = None


class Category(BaseModel):
    name: str
    display_name: str
    icon: str = "tag"
    sort_order: int = 0


class Budget(BaseModel):
    category: str
    amount: int
    alert_threshold_pct: int = 80


class BudgetUpdate(BaseModel):
    budgets: list[Budget]


class MonthlySummary(BaseModel):
    month: str  # YYYY-MM
    total: int
    by_category: dict[str, int]
    expense_count: int


class PresignedUrlResponse(BaseModel):
    upload_url: str
    receipt_id: str
    s3_key: str


class UploadRequest(BaseModel):
    filename: str
    content_type: str = "image/jpeg"
