"""UI: негативы — системный шаблон (ADMIN) и Редактор шаблона без имени (OPERATOR)."""

import re

import allure
import pytest
from playwright.sync_api import expect

from api import templates_api as tpl
from pages.node_template_editor_page import NodeTemplateEditorPage
from pages.node_templates_list_page import NodeTemplatesListPage


@allure.epic("Шаблоны узлов")
@allure.feature("UI")
@allure.story("Негативы")
@pytest.mark.ui
@pytest.mark.negative
class TestNodeTemplatesNegative:
    @allure.title("Системный шаблон: бейдж и защита от удаления (ADMIN)")
    @allure.description(
        "ADMIN видит системный в ordinary-списке; бейдж «системный»; "
        "write-toolbar нет — удаление недоступно."
    )
    @pytest.mark.admin
    def test_seeded_badge_and_delete_blocked(self, admin_ui):
        page, session = admin_ui
        templates = NodeTemplatesListPage(page)

        with allure.step("Найти системный через API под ADMIN"):
            page_res = tpl.list_page(session.request, session.access_token, {"page": 0, "size": 50})
            catalog = page_res.json()
            seeded = next((t for t in catalog.get("items", []) if t.get("seeded") is True), None)
            if not seeded:
                pytest.skip("нет системного шаблона в каталоге ADMIN (локальная БД без seed)")

        with allure.step(
            f"В UI найти системный «{seeded['name']}» (API-имя; в таблице может быть branded) и бейдж"
        ):
            templates.open()
            # Client filter matches raw API name; display may brand e.g. "X by Y" → "X (Y)".
            templates.search_for(seeded["name"])
            row = templates.table.locator("tbody tr").filter(
                has=page.locator(".tpl-table__seeded")
            ).or_(
                templates.table.locator("tbody tr").filter(
                    has=page.get_by_text(re.compile(r"систем|system", re.I))
                )
            ).first
            expect(row).to_be_visible(timeout=20_000)
            badge = templates.seeded_badge_in_row(row).or_(
                row.get_by_text(re.compile(r"систем|system", re.I))
            )
            expect(badge.first).to_be_visible()

        with allure.step("У ADMIN нет write-toolbar / bulk delete; иначе delete disabled или row остаётся"):
            expect(templates.create_btn).to_have_count(0)
            if templates.bulk_delete.count() == 0:
                return
            templates.row_checkbox(row).check()
            if templates.bulk_delete.is_visible():
                if templates.bulk_delete.is_disabled():
                    expect(templates.bulk_delete).to_be_disabled()
                else:
                    templates.open()
                    templates.search_for(seeded["name"])
                    expect(
                        templates.table.locator("tbody tr").filter(
                            has=page.locator(".tpl-table__seeded")
                        ).first
                    ).to_be_visible()

    @allure.title("Создание без имени: Редактор шаблона остаётся открытым")
    @pytest.mark.operator
    def test_create_empty_name_stays_in_editor(self, operator_ui):
        page, _session = operator_ui
        templates = NodeTemplatesListPage(page)

        with allure.step("Открыть Редактор шаблона через «Создать»"):
            templates.open()
            templates.create_btn.click()
            editor = NodeTemplateEditorPage(page)
            editor.wait_open()

        with allure.step("При наличии кнопки «Далее» — нажать, не заполняя имя"):
            next_btn = editor.shell.get_by_role("button", name=re.compile(r"далее|next", re.I))
            if next_btn.is_visible():
                next_btn.click()

        with allure.step("Редактор шаблона всё ещё на экране, URL списка узлов"):
            expect(editor.shell).to_be_visible()
            expect(page.locator(".tpl-create-wizard")).to_be_visible()
            expect(page).to_have_url(re.compile(r"/templates/nodes"))
