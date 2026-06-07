from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

CITY_HINTS = {
    "стамбул": ("Стамбул", "Турция"),
    "анталь": ("Анталья", "Турция"),
    "ереван": ("Ереван", "Армения"),
    "тбилис": ("Тбилиси", "Грузия"),
    "баку": ("Баку", "Азербайджан"),
    "белград": ("Белград", "Сербия"),
    "дубай": ("Дубай", "ОАЭ"),
    "рим": ("Рим", "Италия"),
    "париж": ("Париж", "Франция"),
    "барселон": ("Барселона", "Испания"),
    "прага": ("Прага", "Чехия"),
    "сочи": ("Сочи", "Россия"),
    "москв": ("Москва", "Россия"),
}
MONTHS = "января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря"


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").replace("\xa0", " ")).strip()


def extract_price(text: str) -> str:
    match = re.search(r"\d[\d\s]{1,8}\s?(?:₽|руб\.?|рублей|€|евро|\$)", text or "", flags=re.I)
    return clean_text(match.group(0)) if match else ""


def _nice_case(value: str) -> str:
    value = clean_text(value).strip(" ,.-")
    if not value:
        return ""
    return " ".join(part.capitalize() for part in value.split())


def extract_route(text: str) -> tuple[str, str]:
    raw = clean_text(text)
    patterns = [
        r"из\s+([А-ЯA-ZЁ][А-Яа-яA-Za-zЁё\- ]{1,40}?)\s+в\s+([А-ЯA-ZЁ][А-Яа-яA-Za-zЁё\- ]{1,40}?)(?:\s|,|\.|$)",
        r"([А-ЯA-ZЁ][А-Яа-яA-Za-zЁё\- ]{1,40}?)\s*[-–—>]+\s*([А-ЯA-ZЁ][А-Яа-яA-Za-zЁё\- ]{1,40}?)(?:\s|,|\.|$)",
    ]
    for pattern in patterns:
        match = re.search(pattern, raw, flags=re.I)
        if not match:
            continue
        origin = _nice_case(match.group(1))
        destination = _nice_case(match.group(2))
        if origin and destination and origin.lower() != destination.lower():
            return origin, destination
    return "", ""


def extract_nights(text: str) -> str:
    match = re.search(r"(\d{1,2}\s*(?:ноч[ейи]|дн(?:я|ей)))", text or "", flags=re.I)
    return clean_text(match.group(1)) if match else ""


def extract_event_date(text: str) -> str:
    match = re.search(rf"(\d{{1,2}}(?:\s*[-–]\s*\d{{1,2}})?\s+(?:{MONTHS})(?:\s+\d{{4}})?)", text or "", flags=re.I)
    return clean_text(match.group(1)) if match else ""


def extract_hotel_name(text: str) -> str:
    patterns = [
        r"отель\s+([A-ZА-ЯЁ0-9][A-Za-zА-Яа-яЁё0-9&'\-\s]{2,80})",
        r"hotel\s+([A-Z0-9][A-Za-z0-9&'\-\s]{2,80})",
    ]
    for pattern in patterns:
        match = re.search(pattern, text or "", flags=re.I)
        if match:
            return clean_text(match.group(1)).strip(" ,.-")
    return ""


def detect_direct_flight(text: str) -> bool:
    low = (text or "").lower()
    return "прям" in low or "без пересад" in low


def extract_event_name(title: str, text: str, source: dict[str, Any]) -> str:
    role = (source.get("role") or "").lower()
    title = clean_text(title)
    if role in {"events", "events_and_routes", "activities"}:
        if ":" in title:
            tail = clean_text(title.split(":", 1)[1])
            if len(tail) >= 6:
                return tail[:120]
        return title[:120]
    return ""


def detect_geo(text: str) -> tuple[str, str]:
    low = (text or "").lower()
    for key, value in CITY_HINTS.items():
        if key in low:
            return value
    return "", ""


def make_signal(
    source: dict[str, Any],
    title: str,
    url: str,
    text: str,
    published_at: str = "",
) -> dict[str, Any]:
    title = clean_text(title)[:220]
    text = clean_text(text)[:2800]
    base_text = f"{title} {text}".strip()
    city, country = detect_geo(base_text)
    route_from, route_to = extract_route(base_text)
    return {
        "source_key": source["key"],
        "source_name": source["name"],
        "source_url": source["endpoint"],
        "title": title or text[:120] or source["name"],
        "text": text,
        "url": url or source["endpoint"],
        "published_at": published_at,
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "price": extract_price(base_text),
        "city": city,
        "country": country,
        "route_from": route_from,
        "route_to": route_to,
        "nights": extract_nights(base_text),
        "event_date": extract_event_date(base_text),
        "hotel_name": extract_hotel_name(base_text),
        "event_name": extract_event_name(title, text, source),
        "is_direct": detect_direct_flight(base_text),
        "raw_role": source.get("role", ""),
    }
