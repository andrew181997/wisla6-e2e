from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import allure
import pytest
from playwright.sync_api import APIRequestContext, Browser, Page, Playwright

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api.auth_api import login
from api.counterparties_api import resolve_owner_counterparty_id
from api.users_api import create_user, find_user_by_username
from data.template_factory import TemplateFactory, test_slug_of
from env_config import api_url, base_url, creds, set_creds
from pages.login_page import LoginPage
from pages.node_templates_list_page import NodeTemplatesListPage

# Fixed setup account (not a per-test entity) — created once if E2E_VIEWER_* unset.
DEFAULT_VIEWER_USER = "e2e_viewer"
DEFAULT_VIEWER_PASS = "Forvard18!?"


@dataclass
class ApiSession:
    request: APIRequestContext
    access_token: str
    owner_counterparty_id: str
    factory: TemplateFactory


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {
        **browser_context_args,
        "base_url": base_url(),
        "ignore_https_errors": True,
    }


@pytest.fixture(scope="session", autouse=True)
def _ensure_health_and_viewer(playwright: Playwright) -> None:
    api = playwright.request.new_context(base_url=api_url())
    try:
        health = api.get("/actuator/health")
        if not health.ok:
            raise RuntimeError(
                f"API health check failed: {health.status}. Start local stack first."
            )
        _ensure_viewer(api)
    finally:
        api.dispose()


def _ensure_viewer(api: APIRequestContext) -> None:
    username, password = creds("viewer")
    if username and password:
        return
    admin_user, admin_pass = creds("admin")
    if not admin_user or not admin_pass:
        raise RuntimeError("VIEWER and ADMIN creds missing in e2e/.env.local")
    username = username or DEFAULT_VIEWER_USER
    password = password or DEFAULT_VIEWER_PASS
    admin = login(api, admin_user, admin_pass)
    token = admin["access_token"]
    found = find_user_by_username(api, token, username)
    if not found:
        org_id = resolve_owner_counterparty_id(api, token)
        create_user(
            api,
            token,
            {
                "username": username,
                "password": password,
                "email": f"{username}@example.com",
                "display_name": "E2E",
                "surname": "Viewer",
                "related_organization_id": org_id,
                "role": "VIEWER",
            },
        )
        print(f"[e2e] Created VIEWER user {username}")
    set_creds("viewer", username, password)


def _api_session(
    playwright: Playwright, role: str, *, test_slug: str = "unnamed"
) -> ApiSession:
    username, password = creds(role)
    if not username or not password:
        raise RuntimeError(f"Missing creds for {role} in e2e/.env.local")
    request_ctx = playwright.request.new_context(base_url=api_url())
    body = login(request_ctx, username, password)
    token = body["access_token"]
    owner_id = ""
    if role in ("operator", "admin"):
        try:
            owner_id = resolve_owner_counterparty_id(request_ctx, token)
        except Exception:
            if role == "operator":
                raise
    factory = TemplateFactory(
        request_ctx,
        token,
        owner_id or "00000000-0000-4000-8000-000000000099",
        test_slug=test_slug,
    )
    return ApiSession(
        request=request_ctx,
        access_token=token,
        owner_counterparty_id=owner_id,
        factory=factory,
    )


@pytest.fixture
def operator_api(playwright: Playwright, request):
    session = _api_session(playwright, "operator", test_slug=test_slug_of(request))
    yield session
    session.factory.cleanup()
    session.request.dispose()


@pytest.fixture
def admin_api(playwright: Playwright, request):
    session = _api_session(playwright, "admin", test_slug=test_slug_of(request))
    yield session
    session.factory.cleanup()
    session.request.dispose()


@pytest.fixture
def api_as(playwright: Playwright, request):
    sessions: list[ApiSession] = []
    slug = test_slug_of(request)

    def _as(role: str) -> ApiSession:
        session = _api_session(playwright, role, test_slug=slug)
        sessions.append(session)
        return session

    yield _as
    for session in reversed(sessions):
        session.factory.cleanup()
        session.request.dispose()


def _role_ui(
    browser: Browser, playwright: Playwright, role: str, *, test_slug: str = "unnamed"
):
    username, password = creds(role)
    context = browser.new_context(base_url=base_url())
    login_res = context.request.post(
        "/api/v1/auth/login", data={"username": username, "password": password}
    )
    if not login_res.ok:
        context.close()
        raise RuntimeError(f"{role} UI login failed: {login_res.status} {login_res.text()[:300]}")
    token = login_res.json()["access_token"]
    api = playwright.request.new_context(base_url=api_url())
    owner_id = ""
    if role in ("operator", "admin"):
        try:
            owner_id = resolve_owner_counterparty_id(api, token)
        except Exception:
            owner_id = ""
    factory = TemplateFactory(
        api,
        token,
        owner_id or "00000000-0000-4000-8000-000000000099",
        test_slug=test_slug,
    )
    page = context.new_page()
    session = ApiSession(
        request=api, access_token=token, owner_counterparty_id=owner_id, factory=factory
    )
    yield page, session
    factory.cleanup()
    api.dispose()
    context.close()


@pytest.fixture
def operator_ui(browser: Browser, playwright: Playwright, request):
    yield from _role_ui(browser, playwright, "operator", test_slug=test_slug_of(request))


@pytest.fixture
def admin_ui(browser: Browser, playwright: Playwright, request):
    yield from _role_ui(browser, playwright, "admin", test_slug=test_slug_of(request))


@pytest.fixture
def viewer_ui(browser: Browser, playwright: Playwright, request):
    yield from _role_ui(browser, playwright, "viewer", test_slug=test_slug_of(request))


@pytest.fixture
def login_page(page: Page) -> LoginPage:
    return LoginPage(page)


@pytest.fixture
def node_templates_page(page: Page) -> NodeTemplatesListPage:
    return NodeTemplatesListPage(page)


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    """При падении UI-теста прикрепляем скриншот в Allure."""
    outcome = yield
    report = outcome.get_result()
    if report.when != "call" or not report.failed:
        return
    page = item.funcargs.get("page")
    if page is None:
        for key in ("operator_ui", "admin_ui", "viewer_ui"):
            pair = item.funcargs.get(key)
            if isinstance(pair, tuple) and pair:
                page = pair[0]
                break
    if page is None:
        return
    try:
        png = page.screenshot(full_page=True)
        allure.attach(png, name="failure_screenshot", attachment_type=allure.attachment_type.PNG)
        allure.attach(page.url, name="page_url", attachment_type=allure.attachment_type.TEXT)
    except Exception:
        pass
