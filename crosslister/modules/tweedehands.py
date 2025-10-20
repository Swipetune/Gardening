"""Automation flow for 2dehands.be."""
from __future__ import annotations

import logging
import random
import time

from selenium.webdriver.common.by import By

from .base import BasePoster, ListingPayload

LOGGER = logging.getLogger(__name__)


class TweedehandsPoster(BasePoster):
    domain = "https://www.2dehands.be"

    def login(self) -> None:  # pragma: no cover
        LOGGER.info("Logging in to 2dehands")
        self.driver.get(f"{self.domain}/login")
        email_field = self.wait.visible((By.ID, "email"))
        password_field = self.wait.visible((By.ID, "password"))
        self.type_with_delay(email_field, self.credentials["username"])
        self.type_with_delay(password_field, self.credentials["password"])
        submit = self.wait.clickable((By.CSS_SELECTOR, "button[type='submit']"))
        submit.click()
        time.sleep(5)

    def verify_login(self) -> bool:  # pragma: no cover
        self.driver.get(f"{self.domain}/mijn-2dehands")
        time.sleep(3)
        return "mijn-2dehands" in self.driver.current_url

    def post_listing(self, payload: ListingPayload) -> str:  # pragma: no cover
        self.ensure_authenticated()
        LOGGER.info("Creating 2dehands listing for %s", payload.get("title"))
        self.driver.get(f"{self.domain}/plaats-zoekertje")
        self._dismiss_cookie_banner()
        time.sleep(random.uniform(2, 3))

        self.upload_images("input[type='file']", payload.images)

        title_field = self.wait.visible((By.NAME, "title"))
        self.type_with_delay(title_field, str(payload.get("title")))

        description_field = self.wait.visible((By.NAME, "description"))
        self.type_with_delay(description_field, str(payload.get("description")))

        price_field = self.wait.visible((By.NAME, "price"))
        self.type_with_delay(price_field, str(payload.get("price", "")))

        self._select_category(payload.get("category"))

        condition_field = self.wait.clickable((By.CSS_SELECTOR, "button[data-testid='condition-selector']"))
        condition_field.click()
        condition_xpath = "//li[contains(@role, 'option') and contains(., '{value}')]".format(
            value=payload.get("condition", "Zo goed als nieuw")
        )
        condition_option = self.wait.clickable((By.XPATH, condition_xpath))
        condition_option.click()

        location_field = self.wait.visible((By.NAME, "location"))
        self.type_with_delay(location_field, str(payload.get("location", "Antwerpen")))

        delivery_field = self.wait.clickable((By.CSS_SELECTOR, "button[data-testid='delivery-selector']"))
        delivery_field.click()
        time.sleep(1)
        pickup_option = self.wait.clickable((By.XPATH, "//li[contains(., 'Ophalen')]"))
        pickup_option.click()

        self._submit_form()
        return self._await_confirmation(payload)

    def _dismiss_cookie_banner(self) -> None:
        try:
            accept_button = self.short_wait.clickable((By.CSS_SELECTOR, "button[aria-label='Akkoord']"))
            accept_button.click()
        except Exception:  # noqa: BLE001
            LOGGER.debug("No cookie banner displayed")

    def _select_category(self, category: str | None) -> None:
        if not category:
            return
        try:
            selector = self.wait.clickable((By.CSS_SELECTOR, "button[data-testid='category-selector']"))
            selector.click()
            search_box = self.wait.visible((By.CSS_SELECTOR, "input[data-testid='category-search']"))
            self.type_with_delay(search_box, category)
            time.sleep(2)
            suggestion = self.wait.clickable((By.XPATH, "//li[@role='option'][1]"))
            suggestion.click()
        except Exception as exc:  # noqa: BLE001
            LOGGER.warning("Unable to select category: %s", exc)

    def _submit_form(self) -> None:
        publish = self.wait.clickable((By.CSS_SELECTOR, "button[type='submit'][data-testid='publish']"))
        publish.click()
        time.sleep(3)

    def _await_confirmation(self, payload: ListingPayload) -> str:
        try:
            confirmation = self.long_wait.visible((By.CSS_SELECTOR, "[data-testid='listing-confirmation']"))
            link = confirmation.find_element(By.TAG_NAME, "a")
            LOGGER.info("2dehands listing created: %s", link.get_attribute("href"))
            return link.get_attribute("href")
        except Exception:  # noqa: BLE001
            LOGGER.warning("Unable to capture confirmation URL for %s", payload.get("title"))
            return self.driver.current_url
