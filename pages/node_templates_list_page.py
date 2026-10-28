from __future__ import annotations

import re

from playwright.sync_api import Locator, Page, Response


class NodeTemplatesListPage:
    def __init__(self, page: Page) -> None:
        self.page = page
        self.title = page.locator(".page-tpl-list__title")
        self.search = page.locator("#tpl-search")
        self.reset_filters = page.locator("button.tpl-filters__reset")
        self.table = page.locator("table.tpl-table")
        self.empty_cell = page.locator("td.tpl-table__empty")
        self.create_btn = page.locator("button.page-tpl-list__btn--primary")
        self.import_btn = page.locator("button.page-tpl-list__btn--ghost").filter(
            has_text=re.compile(r"импорт|import", re.I)
        )
        self.columns_btn = page.locator("button.tpl-table-card__columns")
        self.bulk_delete = page.locator("button.tpl-bulk__btn--danger")
        self.summary_total = page.locator(".tpl-summary__item--total strong")
        self.pagination = page.locator("app-table-pagination")

    def open(self) -> Response | None:
        response: Response | None = None
        try:
            with self.page.expect_response(
                lambda r: "/api/v1/templates/page" in r.url and r.request.method == "GET",
                timeout=45_000,
            ) as waiting:
                self.page.goto("/templates/nodes")
            response = waiting.value
        except Exception:
            if "/templates/nodes" not in self.page.url:
                self.page.goto("/templates/nodes")
        self.page.wait_for_url("**/templates/nodes**", timeout=45_000)
        self.title.wait_for(state="visible", timeout=45_000)
        return response

    def row_by_name(self, name: str) -> Locator:
        return self.table.locator("tbody tr").filter(has_text=name)

    def search_for(self, query: str) -> None:
        self.search.fill(query)

    def reset_search(self) -> None:
        self.reset_filters.click()

    def seeded_badge_in_row(self, row: Locator) -> Locator:
        return row.locator(".tpl-table__seeded")

    def row_checkbox(self, row: Locator) -> Locator:
        return row.locator('input[type="checkbox"]')
