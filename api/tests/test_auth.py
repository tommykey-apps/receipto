"""Tests for auth.get_user_id — 4 tests."""

from __future__ import annotations

import os

import pytest
from fastapi import HTTPException
from starlette.testclient import TestClient


def _make_request(scope_extras: dict | None = None, headers: dict | None = None):
    """Build a minimal Request-like object for get_user_id."""
    from starlette.requests import Request

    scope = {"type": "http", "headers": []}
    if scope_extras:
        scope.update(scope_extras)
    if headers:
        scope["headers"] = [
            (k.lower().encode(), v.encode()) for k, v in headers.items()
        ]
    return Request(scope)


def test_dev_user_id_env_var(monkeypatch):
    """When DEV_USER_ID is set, get_user_id returns it."""
    monkeypatch.setenv("DEV_USER_ID", "dev-abc")
    from auth import get_user_id

    request = _make_request()
    assert get_user_id(request) == "dev-abc"


def test_lambda_jwt_claims(monkeypatch):
    """When AWS Lambda context contains JWT claims, extracts 'sub'."""
    monkeypatch.delenv("DEV_USER_ID", raising=False)
    from auth import get_user_id

    aws_event = {
        "requestContext": {
            "authorizer": {
                "jwt": {
                    "claims": {"sub": "cognito-user-123"}
                }
            }
        }
    }
    request = _make_request(scope_extras={"aws.event": aws_event})
    assert get_user_id(request) == "cognito-user-123"


def test_x_user_id_header_fallback(monkeypatch):
    """When no env var or JWT, falls back to x-user-id header."""
    monkeypatch.delenv("DEV_USER_ID", raising=False)
    from auth import get_user_id

    request = _make_request(headers={"x-user-id": "header-user-456"})
    assert get_user_id(request) == "header-user-456"


def test_no_auth_raises_401(monkeypatch):
    """When no auth source is available, raises 401 HTTPException."""
    monkeypatch.delenv("DEV_USER_ID", raising=False)
    from auth import get_user_id

    request = _make_request()
    with pytest.raises(HTTPException) as exc_info:
        get_user_id(request)
    assert exc_info.value.status_code == 401
