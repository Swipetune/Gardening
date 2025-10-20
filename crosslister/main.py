"""Entry point for cross-posting listings across multiple marketplaces."""
from __future__ import annotations

import argparse
import csv
import json
import logging
import random
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, MutableMapping, Tuple

from .modules.base import ListingPayload
from .modules.facebook import FacebookPoster
from .modules.marktplaats import MarktplaatsPoster
from .modules.tweedehands import TweedehandsPoster
from .modules.vinted import VintedPoster
from .utils.browser import BrowserConfig, browser_session

LOGGER = logging.getLogger(__name__)

POSTER_REGISTRY = {
    "marktplaats": MarktplaatsPoster,
    "tweedehands": TweedehandsPoster,
    "facebook": FacebookPoster,
    "vinted": VintedPoster,
}

PLATFORMS = tuple(POSTER_REGISTRY.keys())


@dataclass
class ListingRecord:
    """Representation of one listing row from the CSV input."""

    identifier: str
    base_payload: ListingPayload
    overrides: Dict[str, ListingPayload] = field(default_factory=dict)

    def for_platform(self, platform: str) -> ListingPayload:
        payload = ListingPayload(self.base_payload)
        platform_overrides = self.overrides.get(platform)
        if platform_overrides:
            payload.update(platform_overrides)
        return payload


def load_credentials(path: Path) -> Mapping[str, Mapping[str, str]]:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def cast_value(field: str, value: str) -> object:
    field = field.lower()
    if field == "price":
        try:
            return float(value.replace(",", "."))
        except ValueError:
            LOGGER.warning("Unable to cast price value '%s' to float", value)
            return value
    return value


def normalize_images(value: object, images_dir: Path) -> List[str]:
    if isinstance(value, (list, tuple)):
        return [str(Path(item)) for item in value]
    if not isinstance(value, str):
        return []
    filenames = [segment.strip() for segment in re.split(r"[|;,]", value) if segment.strip()]
    return [str((images_dir / filename).resolve()) for filename in filenames]


def extract_listing_identifier(data: Mapping[str, object], fallback: str) -> str:
    for key in ("id", "sku", "identifier", "title"):
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return fallback


def build_listing(
    row_index: int,
    row: Mapping[str, str],
    images_dir: Path,
    platforms: Iterable[str],
) -> ListingRecord:
    base: MutableMapping[str, object] = {}
    platform_overrides: Dict[str, MutableMapping[str, object]] = {platform: {} for platform in platforms}
    images_value: object | None = None

    for raw_key, raw_value in row.items():
        if raw_key is None:
            continue
        key = raw_key.strip()
        if not key:
            continue
        value = (raw_value or "").strip()
        if value == "":
            continue

        key_lower = key.lower()
        if key_lower == "images":
            images_value = value
            continue

        handled = False
        for platform in platforms:
            prefix = f"{platform}_"
            if key_lower.startswith(prefix):
                field_name = key_lower[len(prefix) :]
                platform_overrides[platform][field_name] = cast_value(field_name, value)
                handled = True
                break
        if handled:
            continue

        base[key_lower] = cast_value(key_lower, value)

    base_payload = ListingPayload(base)
    if images_value is not None:
        base_payload["images"] = normalize_images(images_value, images_dir)

    for platform, overrides in platform_overrides.items():
        if "images" in overrides:
            overrides["images"] = normalize_images(overrides["images"], images_dir)

    overrides_payload = {platform: ListingPayload(data) for platform, data in platform_overrides.items() if data}

    identifier = extract_listing_identifier(base_payload, fallback=f"listing_{row_index}")
    return ListingRecord(identifier=identifier, base_payload=base_payload, overrides=overrides_payload)


def load_listings(csv_path: Path, images_dir: Path, platforms: Iterable[str]) -> List[ListingRecord]:
    listings: List[ListingRecord] = []
    with csv_path.open("r", encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        for index, row in enumerate(reader, start=1):
            listing = build_listing(index, row, images_dir, platforms)
            listings.append(listing)
            LOGGER.debug("Loaded listing %s with overrides %s", listing.identifier, listing.overrides)
    return listings


def configure_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


def post_to_platform(
    platform: str,
    payload: ListingPayload,
    credentials: Mapping[str, str],
    *,
    headless: bool,
    cookies_dir: Path,
    delay_range: Tuple[float, float],
) -> str:
    LOGGER.info("Posting to %s", platform)
    PosterCls = POSTER_REGISTRY[platform]
    config = BrowserConfig(headless=headless, implicit_wait=0)
    with browser_session(config) as driver:
        poster = PosterCls(driver, cookies_dir=cookies_dir, credentials=credentials)
        listing_url = poster.post_listing(payload)
        sleep_min, sleep_max = delay_range
        pause = random.uniform(sleep_min, max(sleep_min, sleep_max))
        LOGGER.debug("Sleeping %.2f seconds before next platform", pause)
        time.sleep(max(0.0, pause))
        return listing_url


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", type=Path, help="Path to the listings CSV file")
    parser.add_argument(
        "--credentials",
        type=Path,
        default=Path("crosslister/config/credentials.json"),
        help="Path to the credentials JSON file",
    )
    parser.add_argument(
        "--images-dir",
        type=Path,
        default=Path("crosslister/data/images"),
        help="Directory that contains listing images",
    )
    parser.add_argument(
        "--platforms",
        nargs="+",
        choices=list(PLATFORMS),
        default=list(PLATFORMS),
        help="Limit posting to a subset of platforms",
    )
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")
    parser.add_argument(
        "--cookies-dir",
        type=Path,
        default=Path(".cookies"),
        help="Directory to store session cookies",
    )
    parser.add_argument(
        "--delay",
        nargs=2,
        type=float,
        default=(5.0, 10.0),
        metavar=("MIN", "MAX"),
        help="Delay range (seconds) between platform postings",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    return parser.parse_args(argv)


def main(argv: List[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    configure_logging(args.verbose)
    credentials = load_credentials(args.credentials)
    cookies_dir = args.cookies_dir
    cookies_dir.mkdir(parents=True, exist_ok=True)

    listings = load_listings(args.csv, args.images_dir, args.platforms)
    if not listings:
        LOGGER.warning("No listings found in %s", args.csv)
        return 0

    overall_results: Dict[str, Dict[str, str]] = {}
    for listing in listings:
        LOGGER.info("Processing listing %s", listing.identifier)
        overall_results[listing.identifier] = {}
        for platform in args.platforms:
            payload = listing.for_platform(platform)
            if platform not in credentials:
                LOGGER.error("Missing credentials for platform %s", platform)
                overall_results[listing.identifier][platform] = "MISSING_CREDENTIALS"
                print(f"[ERROR] {listing.identifier} -> {platform}: missing credentials")
                continue

            try:
                listing_url = post_to_platform(
                    platform,
                    payload,
                    credentials[platform],
                    headless=args.headless,
                    cookies_dir=cookies_dir,
                    delay_range=tuple(args.delay),
                )
                overall_results[listing.identifier][platform] = listing_url
                print(f"[SUCCESS] {listing.identifier} -> {platform}: {listing_url}")
            except Exception as exc:  # noqa: BLE001
                LOGGER.exception("Failed to post %s on %s", listing.identifier, platform)
                overall_results[listing.identifier][platform] = "ERROR"
                print(f"[ERROR] {listing.identifier} -> {platform}: {exc}")

    output_path = Path("crosslister_output.json")
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(overall_results, file, ensure_ascii=False, indent=2)
    LOGGER.info("Posting complete. Results saved to %s", output_path.resolve())
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
