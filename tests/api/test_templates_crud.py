"""API: позитивные сценарии жизненного цикла шаблона узла."""

import allure
import pytest

from api import templates_api as tpl


@allure.epic("Шаблоны узлов")
@allure.feature("API")
@allure.story("CRUD")
@pytest.mark.api
@pytest.mark.smoke
class TestTemplatesCrud:
    @allure.title("Список шаблонов: страница каталога отдаёт корректную структуру")
    @allure.description(
        "OPERATOR запрашивает GET /api/v1/templates/page. "
        "Ожидаем 200 и поля items / total_elements / page / size."
    )
    def test_get_page_returns_catalog_shape(self, operator_api):
        with allure.step("Запросить первую страницу каталога (size=25)"):
            res = tpl.list_page(
                operator_api.request, operator_api.access_token, {"page": 0, "size": 25}
            )
            allure.attach(res.text(), name="response", attachment_type=allure.attachment_type.JSON)

        with allure.step("Проверить статус 200 и форму ответа"):
            assert res.status == 200, res.text()
            body = res.json()
            assert isinstance(body.get("items"), list)
            assert isinstance(body.get("total_elements"), int)
            assert body.get("size") == 25
            assert body.get("page") == 0

    @allure.title("Системный шаблон: чтение карточки и Редактора шаблона")
    @allure.description(
        "ADMIN видит системные шаблоны в обычном GET /templates/page. "
        "Если есть — открываем карточку и Редактор шаблона. "
        "Иначе тест пропускается (локальная БД без системных шаблонов)."
    )
    def test_get_seeded_template_and_editor(self, admin_api):
        with allure.step("Найти системный шаблон в каталоге ADMIN"):
            page_res = tpl.list_page(
                admin_api.request, admin_api.access_token, {"page": 0, "size": 50}
            )
            assert page_res.ok
            page = page_res.json()
            seeded = next((t for t in page.get("items", []) if t.get("seeded") is True), None)
            if not seeded:
                pytest.skip("нет системного шаблона в каталоге ADMIN (локальная БД без seed)")

        with allure.step(f"GET шаблона id={seeded['id']}"):
            get_res = tpl.get_template(
                admin_api.request, admin_api.access_token, seeded["id"]
            )
            assert get_res.status == 200

        with allure.step("GET Редактора шаблона того же id"):
            editor_res = tpl.get_template_editor(
                admin_api.request, admin_api.access_token, seeded["id"]
            )
            assert editor_res.status == 200
            assert editor_res.json()["id"] == seeded["id"]

    @allure.title("Создать → валидировать Редактор шаблона → сохранить → прочитать → удалить")
    @allure.description(
        "Полный happy-path OPERATOR: create 201, validate Редактора шаблона, "
        "PUT Редактора 200, GET подтверждает имя, DELETE 204."
    )
    def test_create_validate_update_delete(self, operator_api):
        name = operator_api.factory.new_name()

        with allure.step(f"Создать шаблон «{name}»"):
            create_res = tpl.create_template(
                operator_api.request,
                operator_api.access_token,
                {
                    "name": name,
                    "description": "e2e crud",
                    "vendor": "E2E",
                    "version": "0.1.0",
                    "owner_counterparty_id": operator_api.owner_counterparty_id,
                },
            )
            assert create_res.status == 201, create_res.text()
            created = create_res.json()
            operator_api.factory.track(created["id"])
            allure.attach(created["id"], name="template_id", attachment_type=allure.attachment_type.TEXT)

        editor_body = {
            "name": name,
            "description": "e2e crud updated",
            "vendor": "E2E",
            "version": "0.1.0",
            "groups": ["Templates"],
            "macros": [{"macro": "{$E2E.MACRO}", "value": "1", "description": "e2e"}],
            "items": [],
            "triggers": [],
            "owner_counterparty_id": operator_api.owner_counterparty_id,
        }

        with allure.step("Провалидировать Редактор шаблона (допускаем 200 или 422)"):
            validate_res = tpl.validate_template_editor(
                operator_api.request, operator_api.access_token, created["id"], editor_body
            )
            assert validate_res.status in (200, 422)

        with allure.step("Сохранить Редактор шаблона (PUT)"):
            put_res = tpl.update_template_editor(
                operator_api.request, operator_api.access_token, created["id"], editor_body
            )
            assert put_res.status == 200, put_res.text()

        with allure.step("Перечитать шаблон и убедиться, что имя сохранилось"):
            get_res = tpl.get_template(
                operator_api.request, operator_api.access_token, created["id"]
            )
            assert get_res.status == 200
            assert get_res.json()["name"] == name

        with allure.step("Удалить шаблон (ожидаем 204)"):
            del_res = tpl.delete_template(
                operator_api.request, operator_api.access_token, created["id"]
            )
            assert del_res.status == 204
