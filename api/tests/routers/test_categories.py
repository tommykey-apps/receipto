"""Tests for /api/categories endpoints — 3 tests."""

from __future__ import annotations


def test_get_categories_auto_initializes_defaults(client):
    """GET /api/categories on first access auto-initializes 10 default categories."""
    resp = client.get("/api/categories")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 10


def test_get_categories_sorted_by_sort_order(client):
    """GET /api/categories returns categories sorted by sort_order ascending."""
    resp = client.get("/api/categories")
    data = resp.json()
    sort_orders = [c["sort_order"] for c in data]
    assert sort_orders == sorted(sort_orders)
    # First should be food (0), last should be other (9)
    assert data[0]["name"] == "food"
    assert data[-1]["name"] == "other"


def test_post_category_appears_in_subsequent_get(client):
    """POST /api/categories creates a new category that appears in GET."""
    # Initialize defaults first
    client.get("/api/categories")

    resp = client.post("/api/categories", json={
        "name": "pet",
        "display_name": "ペット",
        "icon": "paw",
        "sort_order": 10,
    })
    assert resp.status_code == 201
    assert resp.json()["name"] == "pet"

    # Should now have 11 categories
    get_resp = client.get("/api/categories")
    names = [c["name"] for c in get_resp.json()]
    assert "pet" in names
    assert len(get_resp.json()) == 11
