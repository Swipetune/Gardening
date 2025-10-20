"""Automation flow for Facebook Marketplace."""
from __future__ import annotations

import logging
import random
import time

from selenium.webdriver.common.by import By

from .base import BasePoster, ListingPayload

LOGGER = logging.getLogger(__name__)


class FacebookPoster(BasePoster):
    domain = "https://www.facebook.com"

    def login(self) -> None:  # pragma: no cover
        LOGGER.info("Logging in to Facebook")
        self.driver.get(f"{self.domain}/login")
        email_field = self.wait.visible((By.ID, "email"))
        password_field = self.wait.visible((By.ID, "pass"))
        self.type_with_delay(email_field, self.credentials["username"])
        self.type_with_delay(password_field, self.credentials["password"])
        submit = self.wait.clickable((By.NAME, "login"))
        submit.click()
        time.sleep(6)

    def verify_login(self) -> bool:  # pragma: no cover
        self.driver.get(f"{self.domain}/marketplace/you/selling")
        time.sleep(4)
        return "selling" in self.driver.current_url

    def post_listing(self, payload: ListingPayload) -> str:  # pragma: no cover
        self.ensure_authenticated()
        LOGGER.info("Creating Facebook Marketplace listing for %s", payload.get("title"))
        self.driver.get(f"{self.domain}/marketplace/create/item")
        self._dismiss_modals()
        time.sleep(random.uniform(4, 5))

        self.upload_images("input[type='file'][accept*='image']", payload.images)

        title_field = self.wait.visible((By.CSS_SELECTOR, "input[aria-label='Title']"))
        self.type_with_delay(title_field, str(payload.get("title")))

        price_field = self.wait.visible((By.CSS_SELECTOR, "input[aria-label='Price']"))
        self.type_with_delay(price_field, str(payload.get("price", "")))

        description_field = self.wait.visible((By.CSS_SELECTOR, "textarea[aria-label='Description']"))
        self.type_with_delay(description_field, str(payload.get("description")))

        condition_field = self.wait.clickable((By.CSS_SELECTOR, "[aria-label='Condition']"))
        condition_field.click()
        condition_xpath = "//span[text()='{value}']".format(
            value=payload.get("condition", "Used - like new")
        )
        condition_option = self.wait.clickable((By.XPATH, condition_xpath))
        condition_option.click()

        category_field = self.wait.clickable((By.CSS_SELECTOR, "[aria-label='Category']"))
        category_field.click()
        category_search = self.wait.visible((By.CSS_SELECTOR, "input[aria-label='Search for category']"))
        self.type_with_delay(category_search, str(payload.get("category", "Shoes")))
        time.sleep(2)
        suggestion = self.wait.clickable((By.XPATH, "(//div[@role='option'])[1]"))
        suggestion.click()

        location_field = self.wait.clickable((By.CSS_SELECTOR, "input[aria-label='Location']"))
        location_field.clear()
        self.type_with_delay(location_field, str(payload.get("location", "Amsterdam")))
        time.sleep(2)
        first_location = self.wait.clickable((By.XPATH, "(//ul[contains(@role,'listbox')]//li)[1]"))
        first_location.click()

        next_button = self.wait.clickable((By.XPATH, "//div[@aria-label='Next']/ancestor::div[@role='button']"))
        next_button.click()
        time.sleep(4)

        publish_button = self.wait.clickable((By.XPATH, "//div[@aria-label='Publish']/ancestor::div[@role='button']"))
        publish_button.click()
        time.sleep(6)

        return self._await_confirmation(payload)

    def _dismiss_modals(self) -> None:
        try:
            close_buttons = self.driver.find_elements(By.CSS_SELECTOR, "div[aria-label='Close']")
            for button in close_buttons:
                try:
                    button.click()
                except Exception:  # noqa: BLE001
                    continue
        except Exception:  # noqa: BLE001
            LOGGER.debug("No onboarding modals shown")

    def _await_confirmation(self, payload: ListingPayload) -> str:
        try:
            confirmation = self.long_wait.visible((By.XPATH, "//span[contains(., 'Your listing is now live')]"))
            LOGGER.info("Facebook listing appears live for %s", payload.get("title"))
            self.driver.get(f"{self.domain}/marketplace/you/selling")
            title_xpath = "//span[contains(., '{value}')]".format(value=payload.get("title", ""))
            self.long_wait.visible((By.XPATH, title_xpath))
            return self.driver.current_url
        except Exception:  # noqa: BLE001
            LOGGER.warning("Unable to confirm Facebook listing for %s", payload.get("title"))
            return self.driver.current_url
