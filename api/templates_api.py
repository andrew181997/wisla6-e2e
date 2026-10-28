from __future__ import annotations

from typing import Any

from playwright.sync_api import APIRequestContext, APIResponse

from .auth_api import bearer_headers

BASE = "/api/v1/templates"


def _headers(token: str | None) -> dict[str, str] | None:
    return bearer_headers(token) if token else None


def list_page(
    request: APIRequestContext, token: str | None, params: dict[str, Any] | None = None
) -> APIResponse:
    return request.get(f"{BASE}/page", headers=_headers(token), params=params or {})


def get_template(request: APIRequestContext, token: str | None, template_id: str) -> APIResponse:
    return request.get(f"{BASE}/{template_id}", headers=_headers(token))


def get_template_editor(
    request: APIRequestContext, token: str | None, template_id: str
) -> APIResponse:
    """Содержимое «Редактор шаблона» (backend path …/builder)."""
    return request.get(f"{BASE}/{template_id}/builder", headers=_headers(token))


def create_template(request: APIRequestContext, token: str | None, body: dict[str, Any]) -> APIResponse:
    return request.post(BASE, headers=_headers(token), data=body)


def update_template_editor(
    request: APIRequestContext, token: str | None, template_id: str, body: dict[str, Any]
) -> APIResponse:
    """Сохранить «Редактор шаблона» (PUT …/builder)."""
    return request.put(f"{BASE}/{template_id}/builder", headers=_headers(token), data=body)


def validate_template_editor(
    request: APIRequestContext, token: str | None, template_id: str, body: dict[str, Any]
) -> APIResponse:
    """Провалидировать «Редактор шаблона» без сохранения (POST …/builder/validate)."""
    return request.post(
        f"{BASE}/{template_id}/builder/validate", headers=_headers(token), data=body
    )


def clone_template(
    request: APIRequestContext, token: str | None, template_id: str, body: dict[str, Any] | None = None
) -> APIResponse:
    return request.post(f"{BASE}/{template_id}/clone", headers=_headers(token), data=body or {})


def delete_template(request: APIRequestContext, token: str | None, template_id: str) -> APIResponse:
    return request.delete(f"{BASE}/{template_id}", headers=_headers(token))


def import_template(request: APIRequestContext, token: str | None, body: dict[str, Any]) -> APIResponse:
    return request.post(f"{BASE}/import", headers=_headers(token), data=body)


def export_templates(request: APIRequestContext, token: str | None, body: dict[str, Any]) -> APIResponse:
    return request.post(f"{BASE}/export", headers=_headers(token), data=body)


def list_system_catalog(request: APIRequestContext, token: str) -> APIResponse:
    return request.get(f"{BASE}/system-catalog", headers=bearer_headers(token))
