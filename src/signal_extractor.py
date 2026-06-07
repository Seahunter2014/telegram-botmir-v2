import re
from .config_loader import read_json
from .text_utils import extract_price, extract_date_text

CITY_WORDS = None

def _city_words():
    global CITY_WORDS
    if CITY_WORDS is None:
        cities = read_json("cities_iata.json", {})
        CITY_WORDS = sorted(cities.keys(), key=len, reverse=True)
    return CITY_WORDS


def extract_route(text: str) -> tuple[str, str]:
    cities = _city_words()
    cleaned = text.replace("—", "-").replace("–", "-")
    # explicit route Москва - Стамбул
    for a in cities:
        for b in cities:
            if a == b:
                continue
            pattern = rf"\b{re.escape(a)}\b\s*(?:-|→|—|–|в|до)\s*\b{re.escape(b)}\b"
            if re.search(pattern, cleaned, flags=re.IGNORECASE):
                return a, b
    # из Москвы в Стамбул
    m = re.search(r"из\s+([А-Яа-яЁё\- ]{3,24})\s+в\s+([А-Яа-яЁё\- ]{3,24})", text, re.I)
    if m:
        a = normalize_city(m.group(1))
        b = normalize_city(m.group(2))
        if a and b:
            return a, b
    return "", ""


def normalize_city(raw: str) -> str:
    raw = raw.strip().lower().replace("ё", "е")
    aliases = read_json("city_aliases.json", {})
    if raw in aliases:
        return aliases[raw]
    for city in _city_words():
        if city.lower().replace("ё", "е") == raw:
            return city
    return ""


def enrich_signal(signal):
    text = f"{signal.title}\n{signal.text}"
    route_from, route_to = extract_route(text)
    return {
        "route_from": route_from,
        "route_to": route_to,
        "price": extract_price(text),
        "date_text": extract_date_text(text),
    }
