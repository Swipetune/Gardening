"""Business rules and value mappings for the crosslister."""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Optional

LOGGER = logging.getLogger(__name__)

TITLE_MAX_LENGTH = 80
DESCRIPTION_MIN_LENGTH = 10
VALID_CURRENCY = {"eur"}
MAX_IMAGES: Mapping[str, int] = {
    "facebook": 10,
    "vinted": 20,
    "marktplaats": 24,
    "tweedehands": 24,
}

NL_POSTCODE_RE = re.compile(r"^[1-9][0-9]{3}[A-Z]{2}$")
BE_POSTCODE_RE = re.compile(r"^[1-9][0-9]{3}$")

STANDARD_CONDITION_KEYS = {
    "nieuw_met_kaartje": "nieuw_met_kaartje",
    "nieuw_met_label": "nieuw_met_kaartje",
    "nieuw_met_tags": "nieuw_met_kaartje",
    "nieuw_met_tag": "nieuw_met_kaartje",
    "nieuw_met_prijskaart": "nieuw_met_kaartje",
    "nieuw_met_labeltje": "nieuw_met_kaartje",
    "nieuw": "nieuw_zonder_kaartje",
    "nieuw_zonder_kaartje": "nieuw_zonder_kaartje",
    "nieuw_zonder_label": "nieuw_zonder_kaartje",
    "nieuw_zonder_tags": "nieuw_zonder_kaartje",
    "zeer_goed": "zeer_goed",
    "zo_goed_als_nieuw": "zeer_goed",
    "als_nieuw": "zeer_goed",
    "used_like_new": "zeer_goed",
    "used - like new": "zeer_goed",
    "used_like-new": "zeer_goed",
    "goed": "goed",
    "used_good": "goed",
    "used - good": "goed",
    "redelijk": "redelijk",
    "satisfactory": "redelijk",
}

CONDITION_PLATFORM_MAP: Mapping[str, Mapping[str, str]] = {
    "nieuw_met_kaartje": {
        "vinted": "Nieuw met kaartje",
        "tweedehands": "Nieuw",
        "marktplaats": "Nieuw",
        "facebook": "New",
    },
    "nieuw_zonder_kaartje": {
        "vinted": "Nieuw zonder kaartje",
        "tweedehands": "Nieuw",
        "marktplaats": "Nieuw",
        "facebook": "New",
    },
    "zeer_goed": {
        "vinted": "Zeer goed",
        "tweedehands": "Zo goed als nieuw",
        "marktplaats": "Zo goed als nieuw",
        "facebook": "Used - Like New",
    },
    "goed": {
        "vinted": "Goed",
        "tweedehands": "Goed",
        "marktplaats": "Gebruikt",
        "facebook": "Used - Good",
    },
    "redelijk": {
        "vinted": "Redelijk",
        "tweedehands": "Redelijk",
        "marktplaats": "Gebruikt",
        "facebook": "Used - Fair",
    },
}


@dataclass
class CategoryMap:
    mapping: Mapping[str, Mapping[str, str]]

    @classmethod
    def load(cls, path: Path) -> "CategoryMap":
        with path.open("r", encoding="utf-8") as file:
            data: Mapping[str, Mapping[str, str]] = json.load(file)
        normalized = {key.lower(): value for key, value in data.items()}
        return cls(mapping=normalized)

    def resolve(self, hint: Optional[str], platform: str) -> Optional[str]:
        if not hint:
            return None
        hint_key = hint.lower().strip()
        direct = self.mapping.get(hint_key)
        if direct:
            category = direct.get(platform)
            if category:
                return category
        # fallback: attempt keyword lookup
        for key, values in self.mapping.items():
            keywords = [kw.strip().lower() for kw in values.get("keywords", [])]
            if hint_key in keywords:
                category = values.get(platform)
                if category:
                    return category
        return None


def normalize_condition_key(raw: Optional[str]) -> str:
    if not raw:
        raise ValueError("Listing mist een conditie-waarde")
    key = raw.strip().lower()
    key = key.replace(" ", "_").replace("-", "_")
    if key in STANDARD_CONDITION_KEYS:
        return STANDARD_CONDITION_KEYS[key]
    if key in CONDITION_PLATFORM_MAP:
        return key
    raise ValueError(f"Onbekende conditie '{raw}'")


def map_condition_for_platform(condition_key: str, platform: str) -> str:
    platform_values = CONDITION_PLATFORM_MAP.get(condition_key)
    if not platform_values:
        raise ValueError(f"Geen mapping gedefinieerd voor conditie '{condition_key}'")
    mapped = platform_values.get(platform)
    if not mapped:
        raise ValueError(
            f"Conditie '{condition_key}' heeft geen waarde voor platform '{platform}'"
        )
    return mapped


def validate_postcode(country: str, postcode: str) -> None:
    country = country.upper()
    if country == "NL":
        if not NL_POSTCODE_RE.match(postcode.upper()):
            raise ValueError("Ongeldige Nederlandse postcode: {postcode}".format(postcode=postcode))
        return
    if country == "BE":
        if not BE_POSTCODE_RE.match(postcode):
            raise ValueError("Ongeldige Belgische postcode: {postcode}".format(postcode=postcode))
        return
    raise ValueError(f"Onbekend land voor postcodevalidatie: {country}")


def ensure_currency(value: Optional[str]) -> str:
    if not value:
        raise ValueError("Valuta ontbreekt; gebruik EUR")
    normalized = value.strip().lower()
    if normalized not in VALID_CURRENCY:
        raise ValueError(f"Valuta '{value}' wordt niet ondersteund; gebruik EUR")
    return "EUR"


def enforce_image_limit(images: list[str], platform: str) -> list[str]:
    maximum = MAX_IMAGES.get(platform)
    if maximum is None:
        return images
    if len(images) > maximum:
        LOGGER.warning(
            "Te veel foto's (%s) voor %s; eerste %s worden gebruikt",
            len(images),
            platform,
            maximum,
        )
        return images[:maximum]
    return images


def limit_colors(colors: list[str]) -> list[str]:
    unique = []
    for color in colors:
        normalized = color.strip()
        if normalized and normalized not in unique:
            unique.append(normalized)
        if len(unique) == 3:
            break
    return unique

