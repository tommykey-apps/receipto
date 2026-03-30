from __future__ import annotations

from fastapi import APIRouter, Depends

from auth import get_user_id
from models.schemas import Category
from store.dynamodb import DynamoDBStore

router = APIRouter(tags=["categories"])
store = DynamoDBStore()


@router.get("/categories", response_model=list[Category])
def list_categories(
    user_id: str = Depends(get_user_id),
) -> list[Category]:
    categories = store.get_categories(user_id)
    if not categories:
        # First access: create defaults
        categories = store.init_default_categories(user_id)
    return sorted(categories, key=lambda c: c.sort_order)


@router.post("/categories", response_model=Category, status_code=201)
def create_category(
    body: Category,
    user_id: str = Depends(get_user_id),
) -> Category:
    return store.put_category(user_id, body)
