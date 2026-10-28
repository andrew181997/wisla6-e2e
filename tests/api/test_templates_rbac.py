"""API: права ADMIN и VIEWER — читать можно, менять нельзя."""

import allure
import pytest

from api import templates_api as tpl


@allure.epic("Шаблоны узлов")
@allure.feature("API")
@allure.story("RBAC")
@pytest.mark.api
@pytest.mark.negative
@pytest.mark.rbac
@pytest.mark.parametrize("role", ["admin", "viewer"])
class TestTemplatesRbac:
    @allure.title("Роль {role}: GET /page разрешён, create запрещён (403)")
    def test_can_get_page_but_cannot_create(self, api_as, operator_api, role):
        allure.dynamic.title(f"Роль {role}: чтение списка ок, создание → 403")

        with allure.step(f"Логин как {role} и GET /page"):
            session = api_as(role)
            get_res = tpl.list_page(session.request, session.access_token, {"page": 0, "size": 10})
            assert get_res.status == 200

        with allure.step(f"Попытка CREATE от {role} → 403"):
            create_res = tpl.create_template(
                session.request,
                session.access_token,
                {
                    "name": session.factory.new_name(),
                    "owner_counterparty_id": operator_api.owner_counterparty_id,
                },
            )
            assert create_res.status == 403

    @allure.title("Роль {role}: нельзя удалить шаблон оператора (403)")
    def test_cannot_delete_operator_owned(self, api_as, operator_api, role):
        allure.dynamic.title(f"Роль {role}: DELETE чужого шаблона → 403")

        with allure.step("OPERATOR создаёт шаблон"):
            created = operator_api.factory.create()

        with allure.step(f"{role} пытается удалить → 403"):
            session = api_as(role)
            del_res = tpl.delete_template(session.request, session.access_token, created["id"])
            assert del_res.status == 403

        with allure.step("Шаблон всё ещё виден оператору"):
            page_res = tpl.list_page(
                operator_api.request,
                operator_api.access_token,
                {"q": created["name"], "page": 0, "size": 10},
            )
            page = page_res.json()
            assert any(t["id"] == created["id"] for t in page.get("items", []))
