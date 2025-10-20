"""Automation flow for Marktplaats.nl."""
from __future__ import annotations

import logging
import random
import time

from selenium.webdriver.common.by import By

from .base import BasePoster, ListingPayload

LOGGER = logging.getLogger(__name__)


class MarktplaatsPoster(BasePoster):
    domain = "https://www.marktplaats.nl"

    def login(self) -> None:  # pragma: no cover - Selenium interaction
        LOGGER.info("Logging in to Marktplaats")
        self.driver.get(f"{self.domain}/login")
        email_field = self.wait.visible((By.ID, "email"), message="Email field")
        password_field = self.wait.visible((By.ID, "password"), message="Password field")
        self.type_with_delay(email_field, self.credentials["username"])
        self.type_with_delay(password_field, self.credentials["password"])
        submit = self.wait.clickable((By.CSS_SELECTOR, "button[type='submit']"))
        submit.click()
        time.sleep(5)

    def verify_login(self) -> bool:  # pragma: no cover
        self.driver.get(f"{self.domain}/mijn-marktplaats")
        time.sleep(3)
        return "mijn-marktplaats" in self.driver.current_url

    def post_listing(self, payload: ListingPayload) -> str:  # pragma: no cover
        self.ensure_authenticated()
        LOGGER.info("Creating Marktplaats listing for %s", payload.get("title"))
        self.driver.get(f"{self.domain}/plaatsadvertentie")
        self._dismiss_cookie_banner()
        time.sleep(2)

        title_field = self.wait.visible((By.NAME, "title"))
        self.type_with_delay(title_field, str(payload.get("title")))
        time.sleep(random.uniform(1, 2))

        self._select_category(payload)

        self.upload_images("input[type='file']", payload.images)

        description_field = self.wait.visible((By.NAME, "description"))
        self.type_with_delay(description_field, str(payload.get("description")))

        price_field = self.wait.visible((By.NAME, "price"))
        self.type_with_delay(price_field, str(payload.get("price", "")))

        condition_field = self.wait.visible((By.NAME, "condition"))
        condition_field.click()
        condition_xpath = "//li[contains(@role, 'option') and contains(., '{value}')]".format(
            value=payload.get("condition", "Zo goed als nieuw")
        )
        condition_option = self.wait.clickable((By.XPATH, condition_xpath))
        condition_option.click()

        postal_code_field = self.wait.visible((By.NAME, "postalCode"))
        self.type_with_delay(postal_code_field, str(payload.get("postal_code", "1011")))

        delivery_toggle = self.wait.clickable((By.CSS_SELECTOR, "label[for='delivery-method-pickup']"))
        if payload.get("shipping"):
            delivery_toggle.click()

        self._submit_form()
        return self._await_confirmation(payload)

    # Helper methods -----------------------------------------------------
    def _dismiss_cookie_banner(self) -> None:
        try:
            accept_button = self.short_wait.clickable((By.CSS_SELECTOR, "button[aria-label='Akkoord']"))
            accept_button.click()
        except Exception:  # noqa: BLE001
            LOGGER.debug("No cookie banner displayed")

    def _select_category(self, payload: ListingPayload) -> None:
        try:
            manual_category = payload.get("category")
            if manual_category:
                category_button = self.wait.clickable((By.CSS_SELECTOR, "button[data-testid='category-selector']"))
                category_button.click()
                search_box = self.wait.visible((By.CSS_SELECTOR, "input[data-testid='category-search']"))
                self.type_with_delay(search_box, manual_category)
                time.sleep(2)
                suggestion = self.wait.clickable((By.XPATH, "//li[@role='option'][1]"))
                suggestion.click()
        except Exception as exc:  # noqa: BLE001
            LOGGER.warning("Unable to auto-select category: %s", exc)

    def _submit_form(self) -> None:
        publish = self.wait.clickable((By.CSS_SELECTOR, "button[type='submit'][data-testid='publish']"))
        publish.click()
        time.sleep(3)

    def _await_confirmation(self, payload: ListingPayload) -> str:
        try:
            confirmation = self.long_wait.visible((By.CSS_SELECTOR, "[data-testid='listing-confirmation']"))
            link = confirmation.find_element(By.TAG_NAME, "a")
            LOGGER.info("Marktplaats listing created: %s", link.get_attribute("href"))
            return link.get_attribute("href")
        except Exception:  # noqa: BLE001
            LOGGER.warning("Unable to capture confirmation URL for %s", payload.get("title"))
            return self.driver.current_url
