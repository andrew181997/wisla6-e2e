"""API: клонирование, импорт и экспорт шаблонов."""

from pathlib import Path

import allure
import pytest

from api import templates_api as tpl

DATA = Path(__file__).resolve().parents[2] / "data"


@allure.epic("Шаблоны узлов")
@allure.feature("API")
@allure.story("Clone / Import / Export")
@pytest.mark.api
class TestCloneImportExport:
    @allure.title("Клонировать шаблон из системного каталога")
    @allure.description(
        "Берём первый системный шаблон и создаём копию с уникальным именем. "
        "Копия не должна быть системной."
    )
    def test_clone_from_system_catalog(self, operator_api):
        with allure.step("Загрузить системный каталог"):
            catalog_res = tpl.list_system_catalog(operator_api.request, operator_api.access_token)
            assert catalog_res.status == 200, catalog_res.text()
            catalog = catalog_res.json()
            if not catalog:
                pytest.skip("системный каталог пуст")

        source = catalog[0]
        clone_name = operator_api.factory.new_name()

        with allure.step(f"Клонировать «{source.get('name')}» → «{clone_name}»"):
            clone_res = tpl.clone_template(
                operator_api.request,
                operator_api.access_token,
                source["id"],
                {
                    "name": clone_name,
                    "owner_counterparty_id": operator_api.owner_counterparty_id,
                },
            )
            assert clone_res.status == 201, clone_res.text()
            cloned = clone_res.json()
            operator_api.factory.track(cloned["id"])

        with allure.step("Проверить, что копия не системная и имя совпадает"):
            assert not cloned.get("seeded")
            assert cloned.get("name") == clone_name

    @allure.title("Импорт валидного JSON и последующий экспорт")
    @allure.description(
        "Импортируем фикстуру sample-import.json с уникальным именем/uuid, "
        "затем экспортируем созданные id."
    )
    def test_import_valid_json_then_export(self, operator_api):
        with allure.step("Подготовить уникальный payload импорта"):
            content = (DATA / "sample-import.json").read_text(encoding="utf-8")
            unique = operator_api.factory.new_name()
            uuid = "".join(c for c in unique if c.isalnum())[:32].ljust(32, "a")
            content = content.replace("cccccccccccccccccccccccccccccccc", uuid).replace(
                "E2E Import Sample", unique
            )
            allure.attach(unique, name="import_name", attachment_type=allure.attachment_type.TEXT)

        with allure.step("POST /import"):
            import_res = tpl.import_template(
                operator_api.request,
                operator_api.access_token,
                {
                    "content": content,
                    "format": "json",
                    "owner_counterparty_id": operator_api.owner_counterparty_id,
                },
            )
            assert import_res.status == 200, import_res.text()
            imported = import_res.json()
            assert imported.get("blocked") is not True
            templates = imported.get("templates") or []
            assert len(templates) > 0
            for t in templates:
                operator_api.factory.track(t["id"])

        with allure.step("POST /export выбранных id"):
            export_res = tpl.export_templates(
                operator_api.request,
                operator_api.access_token,
                {"ids": [t["id"] for t in templates], "format": "yaml"},
            )
            assert export_res.ok, export_res.text()
