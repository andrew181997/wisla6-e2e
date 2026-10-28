"""API: негативные сценарии (401/403/404/400/409 и битые данные)."""

from pathlib import Path

import allure
import pytest
from playwright.sync_api import Playwright

from api import templates_api as tpl
from api.auth_api import bearer_headers
from env_config import api_url

DATA = Path(__file__).resolve().parents[2] / "data"


@allure.epic("Шаблоны узлов")
@allure.feature("API")
@allure.story("Негативы")
@pytest.mark.api
@pytest.mark.negative
class TestTemplatesNegative:
    @allure.title("Без токена список шаблонов недоступен (401)")
    def test_unauthenticated_get_page_401(self, playwright: Playwright):
        with allure.step("GET /page без Authorization"):
            anon = playwright.request.new_context(base_url=api_url())
            try:
                res = tpl.list_page(anon, None, {"page": 0, "size": 10})
                assert res.status == 401
            finally:
                anon.dispose()

    @allure.title("Битый Bearer → 401")
    def test_garbage_bearer_401(self, playwright: Playwright):
        with allure.step("GET /page с заведомо неверным токеном"):
            anon = playwright.request.new_context(base_url=api_url())
            try:
                res = tpl.list_page(anon, "not-a-real-token", {"page": 0, "size": 10})
                assert res.status == 401
            finally:
                anon.dispose()

    @allure.title("Несуществующий id шаблона → 404")
    def test_get_unknown_id_404(self, operator_api):
        with allure.step("GET случайного UUID"):
            res = tpl.get_template(
                operator_api.request,
                operator_api.access_token,
                "00000000-0000-4000-8000-000000000099",
            )
            assert res.status == 404

    @allure.title("Создание с пустым именем → 400")
    def test_create_blank_name_400(self, operator_api):
        with allure.step("POST create с name из пробелов"):
            res = tpl.create_template(
                operator_api.request,
                operator_api.access_token,
                {"name": "   ", "owner_counterparty_id": operator_api.owner_counterparty_id},
            )
            assert res.status == 400

    @allure.title("Системный шаблон нельзя удалить или править в Редакторе шаблона (409)")
    @allure.description(
        "Системный ищем в каталоге ADMIN (OPERATOR их в ordinary /page не видит). "
        "Мутации — от OPERATOR по id: DELETE и PUT Редактора → 409."
    )
    def test_seeded_delete_and_editor_put_409(self, admin_api, operator_api):
        with allure.step("Найти системный в каталоге ADMIN"):
            page_res = tpl.list_page(
                admin_api.request, admin_api.access_token, {"page": 0, "size": 50}
            )
            page = page_res.json()
            seeded = next((t for t in page.get("items", []) if t.get("seeded") is True), None)
            if not seeded:
                pytest.skip("нет системного шаблона в каталоге ADMIN (локальная БД без seed)")

        with allure.step("DELETE системного от OPERATOR → 409"):
            assert (
                tpl.delete_template(
                    operator_api.request, operator_api.access_token, seeded["id"]
                ).status
                == 409
            )

        with allure.step("PUT Редактора шаблона для системного от OPERATOR → 409"):
            put = tpl.update_template_editor(
                operator_api.request,
                operator_api.access_token,
                seeded["id"],
                {"name": seeded["name"], "description": "should fail"},
            )
            assert put.status == 409

    @allure.title("Битый YAML-импорт не создаёт шаблон")
    def test_invalid_import_yaml(self, operator_api):
        with allure.step("Отправить invalid-import.yaml"):
            content = (DATA / "invalid-import.yaml").read_text(encoding="utf-8")
            res = tpl.import_template(
                operator_api.request,
                operator_api.access_token,
                {
                    "content": content,
                    "format": "yaml",
                    "owner_counterparty_id": operator_api.owner_counterparty_id,
                },
            )
            allure.attach(str(res.status), name="status", attachment_type=allure.attachment_type.TEXT)

        with allure.step("Ожидать отказ: 400/422/500 или blocked/imported=0"):
            if res.status == 200:
                body = res.json()
                assert body.get("blocked") is True or (body.get("imported") or 0) == 0
            else:
                assert res.status in (400, 422, 500)

    @allure.title("Экспорт с пустым списком id → 400")
    def test_export_empty_ids_400(self, operator_api):
        with allure.step("POST /export с ids=[]"):
            res = operator_api.request.post(
                "/api/v1/templates/export",
                headers=bearer_headers(operator_api.access_token),
                data={"ids": []},
            )
            assert res.status == 400

    @allure.title("Повторное удаление уже удалённого → 404")
    def test_delete_already_deleted_404(self, operator_api):
        with allure.step("Создать и удалить шаблон"):
            created = operator_api.factory.create()
            first = tpl.delete_template(
                operator_api.request, operator_api.access_token, created["id"]
            )
            assert first.status == 204

        with allure.step("Повторный DELETE того же id"):
            second = tpl.delete_template(
                operator_api.request, operator_api.access_token, created["id"]
            )
            assert second.status == 404

    @allure.title("Редактор шаблона с дублирующимися ключами item → ошибка валидации")
    def test_editor_duplicate_item_keys(self, operator_api):
        with allure.step(
            "Создать шаблон и отправить Редактор шаблона с двумя одинаковыми key"
        ):
            created = operator_api.factory.create()
            body = {
                "name": created["name"],
                "items": [
                    {"key": "e2e.dup", "name": "A", "type": "ZABBIX_AGENT", "value_type": "FLOAT"},
                    {"key": "e2e.dup", "name": "B", "type": "ZABBIX_AGENT", "value_type": "FLOAT"},
                ],
                "triggers": [],
                "macros": [],
            }
            res = tpl.update_template_editor(
                operator_api.request, operator_api.access_token, created["id"], body
            )
            assert res.status in (400, 422)
