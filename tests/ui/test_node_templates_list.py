"""UI (OPERATOR): открытие списка шаблонов узлов."""

import re

import allure
import pytest
from playwright.sync_api import expect

from pages.node_templates_list_page import NodeTemplatesListPage


@allure.epic("Шаблоны узлов")
@allure.feature("UI")
@allure.story("Список")
@pytest.mark.ui
@pytest.mark.smoke
@pytest.mark.operator
class TestNodeTemplatesList:
    @allure.title("Список узлов: таблица, summary и API page 200")
    @allure.description(
        "OPERATOR открывает /templates/nodes. Видны заголовок, таблица, "
        "chip «Всего», кнопка «Создать»; ответ /templates/page = 200."
    )
    def test_opens_list_with_table_and_page_api(self, operator_ui):
        page, _session = operator_ui
        templates = NodeTemplatesListPage(page)

        with allure.step("Открыть /templates/nodes"):
            response = templates.open()

        with allure.step("Проверить основные элементы страницы"):
            expect(templates.title).to_be_visible()
            expect(templates.table).to_be_visible()
            expect(templates.summary_total).to_be_visible()
            expect(templates.create_btn).to_be_visible()

        with allure.step("Если поймали ответ page API — статус 200"):
            if response is not None:
                assert response.status == 200

    @allure.title("Корень /templates редиректит на вкладку узлов")
    def test_shell_lands_on_nodes_from_templates(self, operator_ui):
        page, _session = operator_ui
        templates = NodeTemplatesListPage(page)

        with allure.step("Перейти на /templates"):
            page.goto("/templates")

        with allure.step("URL стал /templates/nodes, заголовок списка виден"):
            expect(page).to_have_url(re.compile(r"/templates/nodes"))
            expect(templates.title).to_be_visible()
