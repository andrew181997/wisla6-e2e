from __future__ import annotations

from typing import Any

from playwright.sync_api import APIRequestContext


def login(request: APIRequestContext, username: str, password: str) -> dict[str, Any]:
    res = request.post("/api/v1/auth/login", data={"username": username, "password": password})
    if not res.ok:
        raise RuntimeError(f"login failed for {username}: {res.status} {res.text()[:400]}")
    body = res.json()
    if body.get("mfa_required"):
        raise RuntimeError(f"login for {username} requires MFA")
    if not body.get("access_token"):
        raise RuntimeError(f"login for {username} returned no access_token")
    return body


def bearer_headers(access_token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
