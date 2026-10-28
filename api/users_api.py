from __future__ import annotations

from typing import Any

from playwright.sync_api import APIRequestContext

from .auth_api import bearer_headers


def create_user(request: APIRequestContext, access_token: str, body: dict[str, Any]) -> dict[str, Any]:
    res = request.post("/api/v1/users", headers=bearer_headers(access_token), data=body)
    if not res.ok:
        raise RuntimeError(f"create user failed: {res.status} {res.text()}")
    return res.json()


def find_user_by_username(
    request: APIRequestContext, access_token: str, username: str
) -> dict[str, Any] | None:
    res = request.get("/api/v1/users", headers=bearer_headers(access_token))
    if not res.ok:
        return None
    items = res.json()
    if not isinstance(items, list):
        return None
    return next((u for u in items if u.get("username") == username), None)
