from __future__ import annotations

from playwright.sync_api import Page


class NodeTemplateDetailPage:
    def __init__(self, page: Page) -> None:
        self.page = page
        self.modal = page.locator("app-tpl-modal-shell")
        self.title = page.locator("#tpl-modal-title")
        self.close = page.locator("button.ui-modal-close").first

    def close_modal(self) -> None:
        if self.close.is_visible():
            self.close.click()
        else:
            self.page.keyboard.press("Escape")
