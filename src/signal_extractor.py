from __future__ import annotations

import re

from .config_loader import CONFIG_DIR, load_json
from .models import Signal
from .text_utils import extract_dates, extract_price, semantic_fingerprint


class SignalExtractor:
    def __init__(self):
        self.cities = load_json(CONFIG_DIR / "cities_iata.json", default={})
        self.aliases = load_json(CONFIG_DIR / "city_aliases.json", default={})
        self.countries = ["Турция", "Грузия", "Армения", "ОАЭ", "Марокко", "Италия", "Франция", "Испания", "Греция", "Кипр", "Таиланд", "Вьетнам", "Россия", "Европа", "Сербия", "Азербайджан"]

    def enrich(self, signal: Signal) -> Signal:
        text = f"{signal.title}\n{signal.text}"
        signal.price = signal.price or extract_price(text)
        signal.dates = signal.dates or extract_dates(text)
        signal.city = signal.city or self._find_city(text)
        signal.country = signal.country or self._find_country(text)
        signal.semantic_hash = signal.semantic_hash or semantic_fingerprint(signal.title, signal.city, signal.country, signal.genre)
        return signal

    def _find_city(self, text: str) -> str:
        lower = text.lower()
        for alias, city in self.aliases.items():
            if alias.lower() in lower:
                return city
        for city in self.cities:
            if re.search(rf"\b{re.escape(city)}\b", text, re.I):
                return city
        return ""

    def _find_country(self, text: str) -> str:
        for country in self.countries:
            if re.search(rf"\b{re.escape(country)}\b", text, re.I):
                return country
        if "европ" in text.lower():
            return "Европа"
        return ""
