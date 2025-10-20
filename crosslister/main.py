"""Entry point for cross-posting listings across multiple marketplaces."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
import json
import logging
import platform
import random
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Tuple

from .modules.base import ListingPayload
from .modules.facebook import FacebookPoster
from .modules.marktplaats import MarktplaatsPoster
from .modules.tweedehands import TweedehandsPoster
from .modules.vinted import VintedPoster
from .rules import (
    CategoryMap,
    DESCRIPTION_MIN_LENGTH,
    TITLE_MAX_LENGTH,
    ensure_currency,
    enforce_image_limit,
    limit_colors,
    map_condition_for_platform,
    normalize_condition_key,
    validate_postcode,
)
from .utils.browser import BrowserConfig, browser_session

LOGGER = logging.getLogger(__name__)

POSTER_REGISTRY = {
    "marktplaats": MarktplaatsPoster,
    "tweedehands": TweedehandsPoster,
    "facebook": FacebookPoster,
    "vinted": VintedPoster,
}

PLATFORMS = tuple(POSTER_REGISTRY.keys())


BOOLEAN_FIELDS = {
    "shipping_pickup",
    "shipping_buyer_pays_shipping",
    "allow_bids",
    "allow_offers",
}

FLOAT_FIELDS = {"price", "original_price"}
INT_FIELDS = {"quantity"}
LIST_FIELDS = {"color", "shipping_carriers", "tags"}
LIST_SEPARATOR = re.compile(r"[|;,]")


def default_cookies_dir() -> Path:
    system_name = platform.system()
    if system_name == "Darwin":
        return Path.home() / "Library/Application Support/Crosslister/cookies"
    if system_name == "Windows":
        return Path.home() / "AppData/Local/Crosslister/cookies"
    return Path.home() / ".cache/crosslister/cookies"


@dataclass
class ListingRecord:
    """Representation of one listing row from the CSV input."""

    identifier: str
    base_payload: ListingPayload
    overrides: Dict[str, ListingPayload] = field(default_factory=dict)

    def for_platform(self, platform: str) -> ListingPayload:
        payload = self.base_payload.clone()
        platform_overrides = self.overrides.get(platform)
        if platform_overrides:
            payload.update(platform_overrides.clone())
        return payload


def load_credentials(path: Path) -> Mapping[str, Mapping[str, str]]:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def cast_value(field: str, value: str) -> object:
    field = field.lower()
    if field in FLOAT_FIELDS:
        try:
            return float(value.replace(",", "."))
        except ValueError:
            LOGGER.warning("Unable to cast %s value '%s' to float", field, value)
            return value
    if field in INT_FIELDS:
        try:
            return int(value)
        except ValueError:
            LOGGER.warning("Unable to cast %s value '%s' to int", field, value)
            return value
    if field in BOOLEAN_FIELDS:
        lowered = value.strip().lower()
        return lowered in {"1", "true", "yes", "y", "ja"}
    if field in LIST_FIELDS:
        return [segment.strip() for segment in LIST_SEPARATOR.split(value) if segment.strip()]
    return value


def normalize_images(value: object, images_dir: Path) -> List[str]:
    if isinstance(value, (list, tuple)):
        return [str(Path(item)) for item in value]
    if not isinstance(value, str):
        return []
    filenames = [segment.strip() for segment in LIST_SEPARATOR.split(value) if segment.strip()]
    resolved: List[str] = []
    for filename in filenames:
        path = Path(filename)
        if path.is_absolute():
            resolved.append(str(path))
        else:
            resolved.append(str((images_dir / filename).resolve()))
    return resolved


def normalize_listing_structure(payload: ListingPayload) -> None:
    """Group flattened columns into structured dictionaries."""

    location_updates: Dict[str, Any] = {}
    shipping_updates: Dict[str, Any] = {}

    for key in list(payload.keys()):
        if key.startswith("location_"):
            location_updates[key.split("_", 1)[1]] = payload.pop(key)
        elif key.startswith("shipping_"):
            shipping_updates[key.split("_", 1)[1]] = payload.pop(key)

    if location_updates:
        location_data = dict(payload.location)
        location_data.update(location_updates)
        payload["location"] = location_data

    if shipping_updates:
        shipping_data = dict(payload.shipping)
        shipping_data.update(shipping_updates)
        payload["shipping"] = shipping_data

    if "color" in payload and isinstance(payload["color"], str):
        payload["color"] = [payload["color"]]

    if "images" in payload:
        payload["images"] = payload.images


def format_location_display(location: Mapping[str, Any]) -> str:
    city = str(location.get("city", "")).strip()
    region = str(location.get("region", "")).strip()
    country = str(location.get("country", "")).strip()

    parts = [part for part in (city, region) if part]
    if country and country not in parts:
        parts.append(country)
    return ", ".join(parts) if parts else country


def prepare_payload_for_platform(
    payload: ListingPayload, platform: str, category_map: CategoryMap
) -> ListingPayload:
    prepared = payload.clone()

    title = str(prepared.get("title", "")).strip()
    if not title:
        raise ValueError("Titel ontbreekt in listing")
    if len(title) > TITLE_MAX_LENGTH:
        LOGGER.warning(
            "Titel is langer dan %s tekens; wordt ingekort", TITLE_MAX_LENGTH
        )
        title = title[:TITLE_MAX_LENGTH].rstrip()
    prepared["title"] = title

    description = str(prepared.get("description", "")).strip()
    if len(description) < DESCRIPTION_MIN_LENGTH:
        raise ValueError("Beschrijving is te kort; voeg meer details toe")
    prepared["description"] = description

    try:
        price_value = float(prepared.get("price", 0))
    except (TypeError, ValueError):
        raise ValueError("Prijs kon niet worden geconverteerd naar getal") from None
    if price_value <= 0:
        raise ValueError("Prijs moet groter zijn dan nul")
    prepared["price"] = round(price_value, 2)

    prepared["currency"] = ensure_currency(str(prepared.get("currency", "EUR")))

    quantity = prepared.get("quantity", 1)
    try:
        quantity_int = int(quantity)
    except (TypeError, ValueError):
        raise ValueError("Aantal (quantity) moet een geheel getal zijn") from None
    if quantity_int < 1:
        raise ValueError("Quantity moet minimaal 1 zijn")
    prepared["quantity"] = quantity_int

    colors = prepared.get("color", [])
    if isinstance(colors, str):
        colors = [colors]
    if isinstance(colors, list):
        prepared["color"] = limit_colors([str(color) for color in colors])

    condition_key = normalize_condition_key(str(prepared.get("condition")))
    prepared["condition_key"] = condition_key
    prepared["condition"] = map_condition_for_platform(condition_key, platform)

    location = prepared.location
    if not location:
        raise ValueError("Locatiegegevens ontbreken")
    country = str(location.get("country", "")).strip().upper()
    postcode = str(location.get("postcode", "")).strip()
    city = str(location.get("city", "")).strip()
    if not country or not postcode or not city:
        raise ValueError("Locatie moet land, postcode en stad bevatten")
    validate_postcode(country, postcode)
    prepared["postal_code"] = postcode.upper() if country == "NL" else postcode
    prepared.setdefault("location_display", format_location_display(location))

    category = prepared.get("category")
    if not category:
        category_hint = prepared.get("category_hint")
        mapped_category = category_map.resolve(category_hint, platform)
        if not mapped_category:
            raise ValueError(
                f"Geen categoriekoppeling gevonden voor hint '{category_hint}' op {platform}"
            )
        prepared["category"] = mapped_category

    images = [str(path) for path in prepared.images if path]
    if not images:
        raise ValueError("Minstens één foto is vereist")
    prepared["images"] = enforce_image_limit(images, platform)

    shipping = dict(prepared.shipping)
    pickup = shipping.get("pickup", True)
    buyer_pays = shipping.get("buyer_pays_shipping", True)
    carriers = shipping.get("carriers", [])
    if isinstance(carriers, str):
        carriers = [carriers]
    prepared["shipping"] = {
        "pickup": bool(pickup),
        "buyer_pays_shipping": bool(buyer_pays),
        "carriers": [carrier for carrier in carriers if carrier],
    }

    if platform == "vinted":
        if not prepared.get("brand"):
            raise ValueError("Vinted vereist een merkwaarde")
        if not prepared.get("size"):
            raise ValueError("Vinted vereist een maat")

    if platform == "facebook":
        if len(prepared["title"]) > 100:
            prepared["title"] = prepared["title"][:100].rstrip()

    return prepared


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
    normalize_listing_structure(base_payload)

    overrides_payload: Dict[str, ListingPayload] = {}
    for platform, data in platform_overrides.items():
        if "images" in data:
            data["images"] = normalize_images(data["images"], images_dir)
        if not data:
            continue
        override_payload = ListingPayload(data)
        normalize_listing_structure(override_payload)
        overrides_payload[platform] = override_payload

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
    platform_cookies_dir = cookies_dir / platform
    platform_cookies_dir.mkdir(parents=True, exist_ok=True)
    config = BrowserConfig(headless=headless, implicit_wait=0, cookies_dir=platform_cookies_dir)
    with browser_session(config) as driver:
        poster = PosterCls(driver, cookies_dir=platform_cookies_dir, credentials=credentials)
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
        "--category-map",
        type=Path,
        default=Path("crosslister/data/category_map.json"),
        help="JSON mapping van category hints naar platformcategorieën",
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
        default=default_cookies_dir(),
        help="Directory to store session cookies",
    )
    def positive_int(value: str) -> int:
        parsed = int(value)
        if parsed < 1:
            raise argparse.ArgumentTypeError("--max-parallel must be at least 1")
        return parsed

    parser.add_argument(
        "--max-parallel",
        type=positive_int,
        default=1,
        metavar="N",
        help="Maximum number of browser sessions to launch simultaneously",
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
    csv_path = args.csv.expanduser()
    credentials_path = args.credentials.expanduser()
    images_dir = args.images_dir.expanduser()
    cookies_dir = args.cookies_dir.expanduser()
    category_map_path = args.category_map.expanduser()

    credentials = load_credentials(credentials_path)
    cookies_dir.mkdir(parents=True, exist_ok=True)
    category_map = CategoryMap.load(category_map_path)

    listings = load_listings(csv_path, images_dir, args.platforms)
    if not listings:
        LOGGER.warning("No listings found in %s", args.csv)
        return 0

    overall_results: Dict[str, Dict[str, str]] = {}
    max_parallel = max(1, args.max_parallel)

    for listing in listings:
        LOGGER.info("Processing listing %s", listing.identifier)
        overall_results[listing.identifier] = {}
        ready: List[Tuple[str, ListingPayload]] = []
        for platform in args.platforms:
            payload = listing.for_platform(platform)
            if platform not in credentials:
                LOGGER.error("Missing credentials for platform %s", platform)
                overall_results[listing.identifier][platform] = "MISSING_CREDENTIALS"
                print(f"[ERROR] {listing.identifier} -> {platform}: missing credentials")
                continue
            try:
                prepared_payload = prepare_payload_for_platform(payload, platform, category_map)
            except ValueError as exc:
                LOGGER.error(
                    "Listing %s ongeldig voor %s: %s", listing.identifier, platform, exc
                )
                overall_results[listing.identifier][platform] = f"INVALID: {exc}"
                print(f"[ERROR] {listing.identifier} -> {platform}: {exc}")
                continue
            ready.append((platform, prepared_payload))

        for index in range(0, len(ready), max_parallel):
            batch = ready[index : index + max_parallel]
            if not batch:
                continue

            with ThreadPoolExecutor(max_workers=len(batch)) as executor:
                future_map = {
                    executor.submit(
                        post_to_platform,
                        platform,
                        payload,
                        credentials[platform],
                        headless=args.headless,
                        cookies_dir=cookies_dir,
                        delay_range=tuple(args.delay),
                    ): platform
                    for platform, payload in batch
                }

                for future in as_completed(future_map):
                    platform = future_map[future]
                    try:
                        listing_url = future.result()
                        overall_results[listing.identifier][platform] = listing_url
                        print(f"[SUCCESS] {listing.identifier} -> {platform}: {listing_url}")
                    except Exception as exc:  # noqa: BLE001
                        LOGGER.exception(
                            "Failed to post %s on %s", listing.identifier, platform
                        )
                        overall_results[listing.identifier][platform] = "ERROR"
                        print(f"[ERROR] {listing.identifier} -> {platform}: {exc}")

    output_path = Path("crosslister_output.json")
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(overall_results, file, ensure_ascii=False, indent=2)
    LOGGER.info("Posting complete. Results saved to %s", output_path.resolve())
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
