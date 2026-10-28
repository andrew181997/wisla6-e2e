# Playwright e2e (Python) — Node templates

Локальные автотесты для **Шаблоны узлов** (`/templates/nodes`): API + UI, роли OPERATOR / ADMIN / VIEWER.

## Требования

1. Стек: UI `http://localhost:4300`, API `http://localhost:8088`.
2. Python 3.11+.
3. Зависимости:

```bash
cd e2e
python -m venv .venv
# Windows:
.venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

4. Скопировать env:

```bash
copy .env.example .env.local
```

Заполнить пароли. Не коммитить `.env.local`.

## Запуск

```bash
cd e2e
pytest                         # всё (+ пишет allure-results/)
pytest -m api                  # только API
pytest -m ui                   # только UI
pytest -m smoke
pytest -m negative
pytest tests/api -q
pytest tests/ui -q --headed    # с окном браузера
```

### Allure-отчёт

По умолчанию `pytest` пишет сырые результаты в `e2e/allure-results/` (шаги, title, скриншоты при падении UI).

```bash
# нужен Allure CLI: https://docs.qameta.io/allure/#_installing_a_commandline
allure serve allure-results          # временный HTML-сервер
allure generate allure-results -o allure-report --clean
```

В отчёте: epic/feature/story, человекочитаемые title, `allure.step(...)` внутри кейсов.

## Структура

- `api/` — HTTP-клиенты
- `pages/` — Page Objects
- `data/` — factory + фикстуры импорта
- `tests/api`, `tests/ui` — сценарии (`test_*.py`)
- `conftest.py` — фикстуры ролей, health, auto-create VIEWER

Имена создаваемых шаблонов: `template_<test_slug>_<suffix>` через `factory.new_name()` / `entity_name("template", request)` (см. `docs/dev/playwright-e2e.md`).

UI логинится **на каждый тест** (cookie + Bearer), чтобы ротация refresh не ломала следующие кейсы.
