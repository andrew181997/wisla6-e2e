"""UI (ADMIN / VIEWER): чтение списка без кнопок записи + API 403."""

import allure
import pytest
from playwright.sync_api import expect

from api import templates_api as tpl
from pages.node_templates_list_page import NodeTemplatesListPage


@allure.epic("Шаблоны узлов")
@allure.feature("UI")
@allure.story("RBAC")
@pytest.mark.ui
@pytest.mark.rbac
@pytest.mark.negative
@pytest.mark.parametrize("ui_fixture", ["admin_ui", "viewer_ui"])
class TestNodeTemplatesRbac:
    @allure.title("Read-only роль: список есть, Create/Import нет, API create → 403")
    def test_read_list_no_write_toolbar(self, ui_fixture, request):
        role_label = "ADMIN" if ui_fixture == "admin_ui" else "VIEWER"
        allure.dynamic.title(
            f"{role_label}: список читается, write-кнопок нет, create API → 403"
        )
        page, session = request.getfixturevalue(ui_fixture)
        templates = NodeTemplatesListPage(page)

        with allure.step(f"Открыть список шаблонов под {role_label}"):
            response = templates.open()
            expect(templates.title).to_be_visible()
            expect(templates.table).to_be_visible()
            if response is not None:
                assert response.status == 200

        with allure.step("Кнопок «Создать» и «Импорт» нет"):
            expect(templates.create_btn).to_have_count(0)
            expect(templates.import_btn).to_have_count(0)

        with allure.step("Прямой API create той же сессией → 403"):
            body = {"name": session.factory.new_name()}
            if session.owner_counterparty_id:
                body["owner_counterparty_id"] = session.owner_counterparty_id
            create_res = tpl.create_template(session.request, session.access_token, body)
            assert create_res.status == 403
