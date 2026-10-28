from __future__ import annotations

from playwright.sync_api import Page


class NodeTemplateEditorPage:
    """Page Object модалки «Редактор шаблона» (UI create/edit)."""

    def __init__(self, page: Page) -> None:
        self.page = page
        self.shell = page.locator("app-tpl-modal-shell")

    def wait_open(self) -> None:
        self.shell.wait_for(state="visible", timeout=20_000)
