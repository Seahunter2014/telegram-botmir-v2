from __future__ import annotations

import re

from .config_loader import read_json
from .text_utils import extract_date_text, extract_price

CITY_WORDS = None


def _city_words() -> list[str]:
    global CITY_WORDS
    if CITY_WORDS is None:
        cities = read_json("cities_iata.json", {})
        aliases = read_json("city_aliases.json", {})
        words = set(cities.keys()) | set(aliases.keys())
        CITY_WORDS = sorted(words, key=len, reverse=True)
    return CITY_WORDS


def normalize_city(raw: str) -> str:
    raw_norm = (raw or "").strip().lower().replace("ё", "е")
    raw_norm = re.sub(r"\s+", " ", raw_norm)
    raw_norm = raw_norm.strip(" .,:;!?)('«»\"")
    aliases = read_json("city_aliases.json", {})
    if raw_norm in aliases:
        return aliases[raw_norm]
    cities = read_json("cities_iata.json", {})
    for city in cities:
        if city.lower().replace("ё", "е") == raw_norm:
            return city
    return ""


def extract_route(text: str) -> tuple[str, str]:
    cleaned = (text or "").replace("—", "-").replace("–", "-").replace("→", "-")
    cities = _city_words()

    # Explicit route: Нижний — Минск / Москва - Стамбул.
    for a in cities:
        for b in cities:
            if a == b:
                continue
            pattern = rf"(?<![А-Яа-яЁёA-Za-z]){re.escape(a)}(?![А-Яа-яЁёA-Za-z])\s*-\s*(?<![А-Яа-яЁёA-Za-z]){re.escape(b)}(?![А-Яа-яЁёA-Za-z])"
            if re.search(pattern, cleaned, flags=re.IGNORECASE):
                aa = normalize_city(a)
                bb = normalize_city(b)
                if aa and bb and aa != bb:
                    return aa, bb

    # из Нижнего Новгорода в Минск / из Москвы до Стамбула.
    m = re.search(r"из\s+([А-Яа-яЁё\- ]{3,32})\s+(?:в|до)\s+([А-Яа-яЁё\- ]{3,32})", text or "", re.I)
    if m:
        a = normalize_city(m.group(1))
        b = normalize_city(m.group(2))
        if a and b and a != b:
            return a, b

    return "", ""


def enrich_signal(signal):
    text = f"{signal.title}\n{signal.text}"
    route_from, route_to = extract_route(text)
    return {
        "route_from": route_from,
        "route_to": route_to,
        "price": extract_price(text),
        "date_text": extract_date_text(text),
    }
