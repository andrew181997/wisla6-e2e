from __future__ import annotations

from playwright.sync_api import APIRequestContext

from .auth_api import bearer_headers


def resolve_owner_counterparty_id(request: APIRequestContext, access_token: str) -> str:
    res = request.get(
        "/api/v1/counterparties/owner-options",
        headers=bearer_headers(access_token),
    )
    if not res.ok:
        raise RuntimeError(f"owner-options failed: {res.status} {res.text()}")
    body = res.json()
    items = body.get("items") or []
    non_system = next((i for i in items if i.get("system") is not True), None)
    if non_system and non_system.get("id"):
        return non_system["id"]
    if body.get("default_id"):
        return body["default_id"]
    raise RuntimeError("No non-system counterparty in owner-options")
