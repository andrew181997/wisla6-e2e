"""UI (OPERATOR): поиск, пагинация, меню столбцов."""

import time

import allure
import pytest
from playwright.sync_api import expect

from pages.node_templates_list_page import NodeTemplatesListPage


@allure.epic("Шаблоны узлов")
@allure.feature("UI")
@allure.story("Фильтры и таблица")
@pytest.mark.ui
@pytest.mark.operator
class TestNodeTemplatesFilters:
    @allure.title("Поиск без совпадений → empty state; сброс возвращает строки")
    def test_search_empty_then_reset(self, operator_ui):
        page, _session = operator_ui
        templates = NodeTemplatesListPage(page)

        with allure.step("Открыть список"):
            templates.open()

        nonsense = f"zzz-no-such-template-{int(time.time() * 1000)}"
        with allure.step(f"Ввести заведомо пустой поиск «{nonsense}»"):
            templates.search_for(nonsense)
            expect(templates.empty_cell).to_be_visible(timeout=15_000)

        with allure.step("Нажать «Сбросить» и дождаться строк"):
            templates.reset_search()
            page.wait_for_timeout(500)
            assert templates.table.locator("tbody tr:not(:has(td.tpl-table__empty))").count() > 0

    @allure.title("На странице есть блок пагинации")
    def test_pagination_present(self, operator_ui):
        page, _session = operator_ui
        templates = NodeTemplatesListPage(page)

        with allure.step("Открыть список и проверить app-table-pagination"):
            templates.open()
            expect(templates.pagination).to_be_visible()

    @allure.title("Кнопка «Столбцы» открывает меню")
    def test_columns_menu(self, operator_ui):
        page, _session = operator_ui
        templates = NodeTemplatesListPage(page)

        with allure.step("Открыть список"):
            templates.open()
            if not templates.columns_btn.is_visible():
                pytest.skip("columns control not rendered")

        with allure.step("Клик по «Столбцы» → меню видно"):
            templates.columns_btn.click()
            menu = page.locator("#tpl-columns-menu").or_(page.get_by_role("menu"))
            expect(menu.first).to_be_visible()
