from __future__ import annotations

import os

from fastapi import Request


def get_user_id(request: Request) -> str:
    """Extract user ID from Cognito JWT claims or DEV_USER_ID env var."""
    dev_user_id = os.environ.get("DEV_USER_ID")
    if dev_user_id:
        return dev_user_id

    # Lambda + API Gateway with JWT authorizer
    context = request.scope.get("aws.event", {})
    try:
        return context["requestContext"]["authorizer"]["jwt"]["claims"]["sub"]
    except (KeyError, TypeError):
        pass

    # Fallback: check header (for ALB or custom auth proxy)
    user_id = request.headers.get("x-user-id")
    if user_id:
        return user_id

    from fastapi import HTTPException

    raise HTTPException(status_code=401, detail="Unauthorized")
