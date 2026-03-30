from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

import boto3
from boto3.dynamodb.conditions import Key

from models.schemas import (
    Budget,
    Category,
    Expense,
    ExpenseCreate,
    MonthlySummary,
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class DynamoDBStore:
    def __init__(self) -> None:
        table_name = os.environ.get("DYNAMODB_TABLE", "expense-tracker")
        endpoint_url = os.environ.get("DYNAMODB_ENDPOINT")
        kwargs: dict[str, Any] = {}
        if endpoint_url:
            kwargs["endpoint_url"] = endpoint_url
        dynamodb = boto3.resource("dynamodb", **kwargs)
        self.table = dynamodb.Table(table_name)

    # ── Expenses ──

    def put_expense(self, user_id: str, expense_id: str, data: ExpenseCreate) -> Expense:
        now = _now_iso()
        expense = Expense(
            id=expense_id,
            amount=data.amount,
            category=data.category,
            store_name=data.store_name,
            memo=data.memo,
            created_at=now,
        )
        self.table.put_item(
            Item={
                "pk": f"USER#{user_id}",
                "sk": f"EXP#{now}#{expense_id}",
                **expense.model_dump(),
            }
        )
        return expense

    def get_expenses(self, user_id: str, month: str | None = None, category: str | None = None) -> list[Expense]:
        pk = f"USER#{user_id}"
        if month:
            sk_prefix = f"EXP#{month}"
        else:
            sk_prefix = "EXP#"

        resp = self.table.query(
            KeyConditionExpression=Key("pk").eq(pk) & Key("sk").begins_with(sk_prefix),
            ScanIndexForward=False,
        )
        expenses = [Expense(**{k: v for k, v in item.items() if k not in ("pk", "sk")}) for item in resp.get("Items", [])]
        if category:
            expenses = [e for e in expenses if e.category == category]
        return expenses

    def get_expense(self, user_id: str, expense_id: str) -> Expense | None:
        # Need to query since SK contains timestamp
        resp = self.table.query(
            KeyConditionExpression=Key("pk").eq(f"USER#{user_id}") & Key("sk").begins_with("EXP#"),
            FilterExpression="id = :eid",
            ExpressionAttributeValues={":eid": expense_id},
        )
        items = resp.get("Items", [])
        if not items:
            return None
        item = items[0]
        return Expense(**{k: v for k, v in item.items() if k not in ("pk", "sk")})

    def _find_expense_sk(self, user_id: str, expense_id: str) -> str | None:
        resp = self.table.query(
            KeyConditionExpression=Key("pk").eq(f"USER#{user_id}") & Key("sk").begins_with("EXP#"),
            FilterExpression="id = :eid",
            ExpressionAttributeValues={":eid": expense_id},
            ProjectionExpression="sk",
        )
        items = resp.get("Items", [])
        return items[0]["sk"] if items else None

    def update_expense(self, user_id: str, expense_id: str, data: dict[str, Any]) -> Expense | None:
        sk = self._find_expense_sk(user_id, expense_id)
        if not sk:
            return None

        update_parts: list[str] = []
        attr_names: dict[str, str] = {}
        attr_values: dict[str, Any] = {}
        for i, (key, val) in enumerate(data.items()):
            placeholder = f"#k{i}"
            value_placeholder = f":v{i}"
            update_parts.append(f"{placeholder} = {value_placeholder}")
            attr_names[placeholder] = key
            attr_values[value_placeholder] = val

        resp = self.table.update_item(
            Key={"pk": f"USER#{user_id}", "sk": sk},
            UpdateExpression="SET " + ", ".join(update_parts),
            ExpressionAttributeNames=attr_names,
            ExpressionAttributeValues=attr_values,
            ReturnValues="ALL_NEW",
        )
        item = resp["Attributes"]
        return Expense(**{k: v for k, v in item.items() if k not in ("pk", "sk")})

    def delete_expense(self, user_id: str, expense_id: str) -> Expense | None:
        expense = self.get_expense(user_id, expense_id)
        if not expense:
            return None
        sk = self._find_expense_sk(user_id, expense_id)
        if sk:
            self.table.delete_item(Key={"pk": f"USER#{user_id}", "sk": sk})
        return expense

    # ── Receipts ──

    def put_receipt(self, user_id: str, receipt_id: str, s3_key: str, filename: str) -> dict[str, Any]:
        now = _now_iso()
        item = {
            "pk": f"USER#{user_id}",
            "sk": f"RCV#{receipt_id}",
            "id": receipt_id,
            "s3_key": s3_key,
            "filename": filename,
            "status": "processing",
            "created_at": now,
        }
        self.table.put_item(Item=item)
        return {k: v for k, v in item.items() if k not in ("pk", "sk")}

    def get_receipt(self, user_id: str, receipt_id: str) -> dict[str, Any] | None:
        resp = self.table.get_item(Key={"pk": f"USER#{user_id}", "sk": f"RCV#{receipt_id}"})
        item = resp.get("Item")
        if not item:
            return None
        return {k: v for k, v in item.items() if k not in ("pk", "sk")}

    # ── Categories ──

    def get_categories(self, user_id: str) -> list[Category]:
        resp = self.table.query(
            KeyConditionExpression=Key("pk").eq(f"USER#{user_id}") & Key("sk").begins_with("CAT#"),
        )
        return [
            Category(**{k: v for k, v in item.items() if k not in ("pk", "sk")})
            for item in resp.get("Items", [])
        ]

    def put_category(self, user_id: str, category: Category) -> Category:
        self.table.put_item(
            Item={
                "pk": f"USER#{user_id}",
                "sk": f"CAT#{category.name}",
                **category.model_dump(),
            }
        )
        return category

    def init_default_categories(self, user_id: str) -> list[Category]:
        defaults = [
            Category(name="food", display_name="食費", icon="utensils", sort_order=0),
            Category(name="transport", display_name="交通費", icon="train", sort_order=1),
            Category(name="daily", display_name="日用品", icon="shopping-bag", sort_order=2),
            Category(name="entertainment", display_name="娯楽", icon="gamepad", sort_order=3),
            Category(name="utility", display_name="光熱費", icon="bolt", sort_order=4),
            Category(name="telecom", display_name="通信費", icon="wifi", sort_order=5),
            Category(name="medical", display_name="医療費", icon="hospital", sort_order=6),
            Category(name="clothing", display_name="衣服", icon="shirt", sort_order=7),
            Category(name="education", display_name="教育", icon="book", sort_order=8),
            Category(name="other", display_name="その他", icon="tag", sort_order=9),
        ]
        for cat in defaults:
            self.put_category(user_id, cat)
        return defaults

    # ── Budgets ──

    def get_budgets(self, user_id: str, month: str) -> list[Budget]:
        resp = self.table.query(
            KeyConditionExpression=Key("pk").eq(f"USER#{user_id}") & Key("sk").begins_with(f"BDG#{month}"),
        )
        return [
            Budget(**{k: v for k, v in item.items() if k not in ("pk", "sk", "month")})
            for item in resp.get("Items", [])
        ]

    def put_budget(self, user_id: str, month: str, budget: Budget) -> Budget:
        self.table.put_item(
            Item={
                "pk": f"USER#{user_id}",
                "sk": f"BDG#{month}#{budget.category}",
                "month": month,
                **budget.model_dump(),
            }
        )
        return budget

    # ── Monthly Summary ──

    def get_monthly_summary(self, user_id: str, month: str) -> MonthlySummary | None:
        resp = self.table.get_item(Key={"pk": f"USER#{user_id}", "sk": f"SUM#{month}"})
        item = resp.get("Item")
        if not item:
            return None
        return MonthlySummary(**{k: v for k, v in item.items() if k not in ("pk", "sk")})

    def update_monthly_summary(self, user_id: str, month: str, amount: int, category: str) -> None:
        """Atomically increment monthly summary totals."""
        pk = f"USER#{user_id}"
        sk = f"SUM#{month}"

        # Try update first; create if not exists
        try:
            self.table.update_item(
                Key={"pk": pk, "sk": sk},
                UpdateExpression=(
                    "SET #total = if_not_exists(#total, :zero) + :amt, "
                    "#cnt = if_not_exists(#cnt, :zero) + :one, "
                    "#month = :month, "
                    "#bycat.#cat = if_not_exists(#bycat.#cat, :zero) + :amt"
                ),
                ExpressionAttributeNames={
                    "#total": "total",
                    "#cnt": "expense_count",
                    "#month": "month",
                    "#bycat": "by_category",
                    "#cat": category,
                },
                ExpressionAttributeValues={
                    ":amt": amount,
                    ":one": 1,
                    ":zero": 0,
                    ":month": month,
                },
            )
        except self.table.meta.client.exceptions.ClientError:
            # by_category map might not exist yet
            self.table.put_item(
                Item={
                    "pk": pk,
                    "sk": sk,
                    "month": month,
                    "total": amount,
                    "expense_count": 1,
                    "by_category": {category: amount},
                }
            )

    def decrement_monthly_summary(self, user_id: str, month: str, amount: int, category: str) -> None:
        """Decrement monthly summary when an expense is deleted."""
        pk = f"USER#{user_id}"
        sk = f"SUM#{month}"
        try:
            self.table.update_item(
                Key={"pk": pk, "sk": sk},
                UpdateExpression=(
                    "SET #total = #total - :amt, "
                    "#cnt = #cnt - :one, "
                    "#bycat.#cat = #bycat.#cat - :amt"
                ),
                ExpressionAttributeNames={
                    "#total": "total",
                    "#cnt": "expense_count",
                    "#bycat": "by_category",
                    "#cat": category,
                },
                ExpressionAttributeValues={
                    ":amt": amount,
                    ":one": 1,
                },
            )
        except Exception:
            pass  # Summary doesn't exist or already zero
