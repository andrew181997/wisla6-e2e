from __future__ import annotations

import re
import time
from typing import Any

from playwright.sync_api import APIRequestContext

from api.templates_api import create_template, delete_template

_SLUG_SAFE = re.compile(r"[^\w]+", re.UNICODE)


def test_slug_of(request_or_name: Any) -> str:
    """Build a short slug from pytest request or a raw test/function name.

    ``test_clone_from_system_catalog`` → ``clone_from_system_catalog``
    ``test_can_get_page_but_cannot_create[admin]`` → ``can_get_page_but_cannot_create_admin``
    """
    if hasattr(request_or_name, "node"):
        raw = request_or_name.node.name
    else:
        raw = str(request_or_name)
    if raw.startswith("test_"):
        raw = raw[5:]
    slug = _SLUG_SAFE.sub("_", raw).strip("_").lower()
    return slug or "unnamed"


def entity_name(kind: str, request_or_slug: Any, *, unique: bool = True) -> str:
    """``{kind}_{test_slug}[_<ms>]`` — e.g. ``template_clone_from_system_catalog_482913``.

    Pass a pytest ``request`` fixture or an already-resolved slug string.
    """
    slug = (
        test_slug_of(request_or_slug)
        if hasattr(request_or_slug, "node")
        else str(request_or_slug).removeprefix("test_").strip("_") or "unnamed"
    )
    base = f"{kind}_{slug}"
    if not unique:
        return base
    suffix = f"{int(time.time() * 1000) % 1_000_000:06d}"
    return f"{base}_{suffix}"


def unique_template_name(test_slug: str | None = None) -> str:
    """Unique template name: ``template_<test_slug>_<suffix>``."""
    return entity_name("template", test_slug or "unnamed")


class TemplateFactory:
    def __init__(
        self,
        request: APIRequestContext,
        access_token: str,
        owner_counterparty_id: str,
        test_slug: str = "unnamed",
    ) -> None:
        self.request = request
        self.access_token = access_token
        self.owner_counterparty_id = owner_counterparty_id
        self.test_slug = test_slug
        self._ids: list[str] = []

    def new_name(self, *, unique: bool = True) -> str:
        return entity_name("template", self.test_slug, unique=unique)

    def create(self, **overrides: Any) -> dict[str, Any]:
        name = overrides.get("name") or self.new_name()
        body = {
            "name": name,
            "description": overrides.get("description", "Playwright e2e template"),
            "vendor": "E2E",
            "version": "0.1.0",
            "groups": ["Templates"],
            "owner_counterparty_id": self.owner_counterparty_id,
        }
        res = create_template(self.request, self.access_token, body)
        if not res.ok:
            raise RuntimeError(f"factory create failed: {res.status} {res.text()}")
        tpl = res.json()
        self._ids.append(tpl["id"])
        tpl["name"] = tpl.get("name") or name
        return tpl

    def track(self, template_id: str) -> None:
        self._ids.append(template_id)

    def cleanup(self) -> None:
        for template_id in reversed(self._ids):
            res = delete_template(self.request, self.access_token, template_id)
            if res.status not in (204, 404, 409):
                print(f"[e2e cleanup] DELETE {template_id} → {res.status}")
        self._ids.clear()
