from __future__ import annotations

from playwright.sync_api import Page


class LoginPage:
    def __init__(self, page: Page) -> None:
        self.page = page
        self.form = page.locator("form.login-form")
        self.username = page.locator('input[name="login"]')
        self.password = page.locator('input[name="password"]')
        self.submit = page.locator("button.login-form__submit")
        self.error = page.locator(".login-form__error")

    def goto(self) -> None:
        self.page.goto("/login")
        self.form.wait_for(state="visible")

    def login(self, user: str, password: str) -> None:
        self.username.fill(user)
        self.password.fill(password)
        self.submit.click()
