"""UI: негативы входа — неверный пароль и доступ без сессии."""

import re

import allure
import pytest
from playwright.sync_api import Page, expect

from pages.login_page import LoginPage


@allure.epic("Авторизация")
@allure.feature("UI")
@allure.story("Негативы логина")
@pytest.mark.ui
@pytest.mark.negative
@pytest.mark.anon
class TestAuthLoginNegative:
    @allure.title("Неверный пароль: ошибка на форме, остаёмся на /login")
    def test_wrong_password_shows_error(self, page: Page):
        login = LoginPage(page)

        with allure.step("Открыть страницу входа"):
            login.goto()

        with allure.step("Ввести demidov и заведомо неверный пароль"):
            login.login("demidov", "definitely-wrong-password")

        with allure.step("Увидеть сообщение об ошибке и URL /login"):
            expect(login.error).to_be_visible(timeout=10_000)
            expect(page).to_have_url(re.compile(r"/login"))

    @allure.title("Без сессии /templates/nodes редиректит на логин")
    def test_unauthenticated_templates_redirects(self, page: Page):
        with allure.step("Перейти на /templates/nodes анонимно"):
            page.goto("/templates/nodes")

        with allure.step("Ожидать редирект на /login"):
            expect(page).to_have_url(re.compile(r"/login"))
