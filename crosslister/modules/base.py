"""Base classes shared by platform implementations."""
from __future__ import annotations

import json
import logging
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional

from selenium.webdriver.remote.webdriver import WebDriver

from ..utils.wait import Waiter, long_wait, short_wait

LOGGER = logging.getLogger(__name__)


class ListingPayload(Dict[str, object]):
    """Dictionary subclass representing a listing payload."""

    @property
    def images(self) -> List[str]:
        return list(self.get("images", []))


class BasePoster(ABC):
    """Abstract poster responsible for creating listings on a platform."""

    domain: str

    def __init__(self, driver: WebDriver, *, cookies_dir: Path, credentials: Mapping[str, str]):
        self.driver = driver
        self.cookies_dir = cookies_dir
        self.credentials = credentials
        self.wait = Waiter(driver)
        self.short_wait = short_wait(driver)
        self.long_wait = long_wait(driver)

    @abstractmethod
    def login(self) -> None:  # pragma: no cover - Selenium callouts
        """Perform the interactive login flow."""

    @abstractmethod
    def verify_login(self) -> bool:  # pragma: no cover - Selenium callouts
        """Return ``True`` if the session is authenticated."""

    @abstractmethod
    def post_listing(self, payload: ListingPayload) -> str:  # pragma: no cover - Selenium callouts
        """Create a listing and return the resulting URL."""

    def ensure_authenticated(self) -> None:
        from ..utils.browser import ensure_login

        LOGGER.info("Ensuring authenticated session for %s", self.domain)
        ensure_login(
            self.driver,
            self.login,
            self.verify_login,
            cookies_dir=self.cookies_dir,
            domain=self.domain,
        )

    def upload_images(self, input_selector: str, images: Iterable[str]) -> None:
        input_el = self.wait.visible(("css selector", input_selector))
        for image_path in images:
            LOGGER.debug("Uploading image %s", image_path)
            input_el.send_keys(image_path)
            time.sleep(2)

    @staticmethod
    def type_with_delay(element, value: str, delay: float = 0.1) -> None:
        element.clear()
        for char in value:
            element.send_keys(char)
            time.sleep(delay)


def load_listing(path: Path) -> ListingPayload:
    with path.open("r", encoding="utf-8") as file:
        return ListingPayload(json.load(file))


def parse_directory(listing_dir: Path) -> ListingPayload:
    info_file = listing_dir / "info.txt"
    if not info_file.exists():
        raise FileNotFoundError(f"Missing info.txt in {listing_dir}")

    lines = info_file.read_text(encoding="utf-8").splitlines()
    if len(lines) < 3:
        raise ValueError("info.txt requires at least three lines (title, price, description)")

    title = lines[0].strip()
    price = float(lines[1].strip())
    description = "\n".join(line.strip() for line in lines[2:]).strip()

    images = sorted(
        str(path)
        for path in listing_dir.iterdir()
        if path.suffix.lower() in {".jpg", ".jpeg", ".png"}
    )

    payload = ListingPayload(
        title=title,
        price=price,
        description=description,
        images=images,
    )
    LOGGER.debug("Parsed directory %s into payload %s", listing_dir, payload)
    return payload
