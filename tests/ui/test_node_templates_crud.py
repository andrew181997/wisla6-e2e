"""UI (OPERATOR): появление строки, карточка, bulk delete, мастер создания."""

import allure
import pytest
from playwright.sync_api import expect

from pages.node_template_detail_page import NodeTemplateDetailPage
from pages.node_template_editor_page import NodeTemplateEditorPage
from pages.node_templates_list_page import NodeTemplatesListPage


@allure.epic("Шаблоны узлов")
@allure.feature("UI")
@allure.story("CRUD")
@pytest.mark.ui
@pytest.mark.operator
class TestNodeTemplatesCrud:
    @allure.title("Шаблон из API виден в таблице; карточка; bulk delete убирает строку")
    @allure.description(
        "API-first: создаём шаблон токеном OPERATOR, ищем в UI, открываем detail-modal, "
        "удаляем через bulk danger и проверяем отсутствие строки."
    )
    def test_api_created_appears_detail_bulk_delete(self, operator_ui):
        page, session = operator_ui
        templates = NodeTemplatesListPage(page)
        name = session.factory.new_name()

        with allure.step(f"Создать шаблон через API: {name}"):
            session.factory.create(name=name)

        with allure.step("Найти строку в таблице по имени"):
            templates.open()
            templates.search_for(name)
            row = templates.row_by_name(name)
            expect(row).to_be_visible(timeout=20_000)

        with allure.step("Открыть карточку (detail modal) и закрыть"):
            row.click()
            detail = NodeTemplateDetailPage(page)
            expect(detail.modal).to_be_visible(timeout=10_000)
            expect(detail.title).to_be_visible()
            detail.close_modal()

        with allure.step("Выбрать строку и удалить через bulk delete"):
            templates.row_checkbox(row).check()
            expect(templates.bulk_delete).to_be_visible()
            page.once("dialog", lambda d: d.accept())
            templates.bulk_delete.click()

        with allure.step("Строка больше не находится поиском"):
            for _ in range(20):
                templates.search_for(name)
                if templates.row_by_name(name).count() == 0:
                    break
                page.wait_for_timeout(500)
            assert templates.row_by_name(name).count() == 0

    @allure.title("Кнопка «Создать» открывает Редактор шаблона (мастер)")
    def test_create_editor_opens(self, operator_ui):
        page, _session = operator_ui
        templates = NodeTemplatesListPage(page)

        with allure.step("Открыть список и нажать «Создать»"):
            templates.open()
            templates.create_btn.click()

        with allure.step("Модалка Редактора шаблона и wizard видны"):
            editor = NodeTemplateEditorPage(page)
            editor.wait_open()
            expect(editor.shell).to_be_visible()
            expect(page.locator(".tpl-create-wizard")).to_be_visible()
