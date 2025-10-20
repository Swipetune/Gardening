"""Automation flow for Vinted."""
from __future__ import annotations

import logging
import random
import time

from selenium.webdriver.common.by import By

from .base import BasePoster, ListingPayload

LOGGER = logging.getLogger(__name__)


class VintedPoster(BasePoster):
    domain = "https://www.vinted.nl"

    def login(self) -> None:  # pragma: no cover
        LOGGER.info("Logging in to Vinted")
        self.driver.get(f"{self.domain}/member/login")
        email_field = self.wait.visible((By.NAME, "username"))
        password_field = self.wait.visible((By.NAME, "password"))
        self.type_with_delay(email_field, self.credentials["username"])
        self.type_with_delay(password_field, self.credentials["password"])
        submit = self.wait.clickable((By.CSS_SELECTOR, "button[type='submit']"))
        submit.click()
        time.sleep(5)

    def verify_login(self) -> bool:  # pragma: no cover
        self.driver.get(f"{self.domain}/member/items")
        time.sleep(3)
        return "items" in self.driver.current_url

    def post_listing(self, payload: ListingPayload) -> str:  # pragma: no cover
        self.ensure_authenticated()
        LOGGER.info("Creating Vinted listing for %s", payload.get("title"))
        self.driver.get(f"{self.domain}/items/new")
        self._dismiss_cookie_banner()
        time.sleep(random.uniform(3, 4))

        self.upload_images("input[type='file']", payload.images)

        title_field = self.wait.visible((By.NAME, "title"))
        self.type_with_delay(title_field, str(payload.get("title")))

        description_field = self.wait.visible((By.NAME, "description"))
        self.type_with_delay(description_field, str(payload.get("description")))

        brand_field = self.wait.clickable((By.CSS_SELECTOR, "input[name='brand']"))
        self.type_with_delay(brand_field, str(payload.get("brand", "Nike")))
        time.sleep(2)
        brand_option = self.wait.clickable((By.XPATH, "(//div[@role='option'])[1]"))
        brand_option.click()

        size_field = self.wait.clickable((By.CSS_SELECTOR, "input[name='size']"))
        self.type_with_delay(size_field, str(payload.get("size", "42")))
        time.sleep(2)
        size_option = self.wait.clickable((By.XPATH, "(//div[@role='option'])[1]"))
        size_option.click()

        condition_field = self.wait.clickable((By.CSS_SELECTOR, "div[data-testid='condition-dropdown']"))
        condition_field.click()
        condition_xpath = "//li[contains(@role, 'option') and contains(., '{value}')]".format(
            value=payload.get("condition", "Uitstekend")
        )
        condition_option = self.wait.clickable((By.XPATH, condition_xpath))
        condition_option.click()

        category_field = self.wait.clickable((By.CSS_SELECTOR, "div[data-testid='category-dropdown']"))
        category_field.click()
        category_search = self.wait.visible((By.CSS_SELECTOR, "input[placeholder='Zoeken']"))
        self.type_with_delay(category_search, str(payload.get("category", "Schoenen")))
        time.sleep(2)
        category_option = self.wait.clickable((By.XPATH, "(//div[@role='option'])[1]"))
        category_option.click()

        price_field = self.wait.visible((By.NAME, "price"))
        self.type_with_delay(price_field, str(payload.get("price", "")))

        delivery_switch = self.wait.clickable((By.CSS_SELECTOR, "input[name='shipping_options']"))
        if payload.get("shipping"):
            if not delivery_switch.is_selected():
                delivery_switch.click()
        else:
            if delivery_switch.is_selected():
                delivery_switch.click()

        publish_button = self.wait.clickable((By.CSS_SELECTOR, "button[data-testid='submit-button']"))
        publish_button.click()
        time.sleep(5)

        return self._await_confirmation(payload)

    def _dismiss_cookie_banner(self) -> None:
        try:
            accept_button = self.short_wait.clickable((By.CSS_SELECTOR, "button[data-testid='accept-privacy']"))
            accept_button.click()
        except Exception:  # noqa: BLE001
            LOGGER.debug("No cookie banner displayed")

    def _await_confirmation(self, payload: ListingPayload) -> str:
        try:
            success_banner = self.long_wait.visible((By.CSS_SELECTOR, "div[data-testid='success-banner']"))
            link = success_banner.find_element(By.TAG_NAME, "a")
            LOGGER.info("Vinted listing created: %s", link.get_attribute("href"))
            return link.get_attribute("href")
        except Exception:  # noqa: BLE001
            LOGGER.warning("Unable to confirm Vinted listing for %s", payload.get("title"))
            return self.driver.current_url
