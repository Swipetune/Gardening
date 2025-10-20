"""Utility helpers for Selenium WebDriver management and cookie persistence."""
from __future__ import annotations

import json
import logging
import platform
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Optional

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.webdriver import WebDriver as ChromeDriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.remote.webdriver import WebDriver
from webdriver_manager.chrome import ChromeDriverManager

LOGGER = logging.getLogger(__name__)


@dataclass
class BrowserConfig:
    """Configuration for creating a WebDriver instance."""

    headless: bool = False
    implicit_wait: float = 0
    download_path: Optional[Path] = None
    user_data_dir: Optional[Path] = None
    cookies_dir: Optional[Path] = None


class BrowserManager:
    """Factory responsible for creating and configuring Selenium drivers."""

    def __init__(self, config: Optional[BrowserConfig] = None) -> None:
        self.config = config or BrowserConfig()

    def _create_options(self) -> ChromeOptions:
        options = ChromeOptions()
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-infobars")
        system_name = platform.system()

        if system_name == "Windows":
            options.add_argument("--start-maximized")
        elif system_name == "Darwin":
            # macOS prefers fullscreen to mimic natural browser usage.
            options.add_argument("--start-fullscreen")
            default_binary = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
            if default_binary.exists():
                options.binary_location = str(default_binary)
        else:
            options.add_argument("--start-maximized")

        if self.config.headless:
            options.add_argument("--headless=new")
            if system_name in {"Linux", "Darwin"}:
                # Prevent rendering glitches for headless Chrome on Unix systems.
                options.add_argument("--disable-gpu")
                options.add_argument("--no-sandbox")
        if self.config.user_data_dir:
            options.add_argument(f"--user-data-dir={self.config.user_data_dir}")
        if self.config.download_path:
            prefs = {"download.default_directory": str(self.config.download_path)}
            options.add_experimental_option("prefs", prefs)
        options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
        return options

    def create(self) -> WebDriver:
        options = self._create_options()
        capabilities = DesiredCapabilities.CHROME.copy()
        capabilities["goog:loggingPrefs"] = {"performance": "ALL"}
        LOGGER.debug("Launching Chrome WebDriver with options: %s", options.arguments)
        driver = webdriver.Chrome(
            service=ChromeService(ChromeDriverManager().install()),
            options=options,
            desired_capabilities=capabilities,
        )
        if self.config.implicit_wait:
            driver.implicitly_wait(self.config.implicit_wait)
        return driver


def cookie_store_path(base_dir: Path, domain: str) -> Path:
    """Return the expected cookie file path for a domain."""

    sanitized = domain.replace("https://", "").replace("http://", "").replace("/", "_")
    return base_dir / f"{sanitized}.cookies.json"


def save_cookies(driver: WebDriver, storage_dir: Path, domain: Optional[str] = None) -> None:
    """Persist cookies from the driver into a JSON file."""

    storage_dir.mkdir(parents=True, exist_ok=True)
    domain = domain or driver.current_url
    path = cookie_store_path(storage_dir, domain)
    cookies = driver.get_cookies()
    with path.open("w", encoding="utf-8") as file:
        json.dump(cookies, file, ensure_ascii=False, indent=2)
    LOGGER.info("Saved %s cookies for %s to %s", len(cookies), domain, path)


def load_cookies(driver: WebDriver, storage_dir: Path, domain: str) -> bool:
    """Load cookies from the JSON file into the driver."""

    path = cookie_store_path(storage_dir, domain)
    if not path.exists():
        LOGGER.debug("No cookies found for domain %s", domain)
        return False

    with path.open("r", encoding="utf-8") as file:
        cookies: Iterable[Dict[str, str]] = json.load(file)

    driver.get(domain)
    time.sleep(1)
    for cookie in cookies:
        cookie_dict = {k: v for k, v in cookie.items() if k in {"name", "value", "domain", "path", "expiry", "secure"}}
        try:
            driver.add_cookie(cookie_dict)
        except Exception as exc:  # noqa: BLE001
            LOGGER.debug("Failed to add cookie %s: %s", cookie_dict.get("name"), exc)
    driver.get(domain)
    LOGGER.info("Loaded cookies for %s", domain)
    return True


@contextmanager
def browser_session(config: Optional[BrowserConfig] = None) -> Iterable[WebDriver]:
    """Context manager that yields a configured WebDriver and ensures teardown."""

    manager = BrowserManager(config)
    driver = manager.create()
    try:
        yield driver
    finally:
        try:
            cookies_dir = (config and config.cookies_dir) or Path(".cookies")
            save_cookies(driver, cookies_dir, driver.current_url)
        except Exception as exc:  # noqa: BLE001
            LOGGER.debug("Unable to persist cookies on shutdown: %s", exc)
        driver.quit()


def ensure_login(driver: WebDriver, login_callable, verification_callable, *, cookies_dir: Path, domain: str) -> bool:
    """Ensure that a user is logged in for a domain.

    Parameters
    ----------
    driver:
        Active Selenium driver.
    login_callable:
        Callable performing the interactive login. Should raise on failure.
    verification_callable:
        Callable returning ``True`` when the user is considered logged in.
    cookies_dir:
        Base path where cookies are stored.
    domain:
        Domain URL used for navigation and cookie-scoping.
    """

    if load_cookies(driver, cookies_dir, domain):
        if verification_callable():
            LOGGER.info("Authenticated session restored from cookies for %s", domain)
            return True
        LOGGER.info("Stored cookies for %s invalid, falling back to manual login", domain)

    login_callable()
    if not verification_callable():
        raise RuntimeError(f"Unable to verify login for {domain}")
    save_cookies(driver, cookies_dir, domain)
    return True
