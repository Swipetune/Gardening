"""Convenience wrappers for Selenium explicit waits."""
from __future__ import annotations

import logging
from typing import Callable, Optional

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

LOGGER = logging.getLogger(__name__)


class Waiter:
    """Helper for waiting on DOM conditions with logging."""

    def __init__(self, driver: WebDriver, timeout: float = 20.0, poll_frequency: float = 0.5) -> None:
        self.driver = driver
        self.timeout = timeout
        self.poll_frequency = poll_frequency

    def until(self, condition, *, message: Optional[str] = None):
        try:
            return WebDriverWait(self.driver, self.timeout, self.poll_frequency).until(condition)
        except TimeoutException as exc:  # noqa: BLE001
            LOGGER.error("Timeout waiting for condition: %s", message or condition)
            raise exc

    def visible(self, locator, *, message: Optional[str] = None):
        return self.until(EC.visibility_of_element_located(locator), message=message)

    def clickable(self, locator, *, message: Optional[str] = None):
        return self.until(EC.element_to_be_clickable(locator), message=message)

    def presence(self, locator, *, message: Optional[str] = None):
        return self.until(EC.presence_of_element_located(locator), message=message)


def short_wait(driver: WebDriver, timeout: float = 5.0) -> Waiter:
    return Waiter(driver, timeout=timeout)


def long_wait(driver: WebDriver, timeout: float = 30.0) -> Waiter:
    return Waiter(driver, timeout=timeout)
