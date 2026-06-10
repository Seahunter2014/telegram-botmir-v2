from __future__ import annotations

from urllib.parse import quote_plus, urlencode

from .config_loader import CONFIG_DIR, load_json
from .models import Brief


class UrlBuilder:
    def __init__(self):
        self.iata = load_json(CONFIG_DIR / "cities_iata.json", default={})

    def build_flight_url(self, base_url: str, brief: Brief) -> str:
        destination = brief.city or brief.country or brief.topic
        params = {"utm_source": "mir_na_ladoni_bot", "destination": destination}
        if brief.city in self.iata:
            params["destination_iata"] = self.iata[brief.city]
        return base_url + ("&" if "?" in base_url else "?") + urlencode(params, doseq=True)

    def build_generic_url(self, base_url: str, brief: Brief) -> str:
        return base_url + ("&" if "?" in base_url else "?") + "utm_source=mir_na_ladoni_bot&utm_content=" + quote_plus(brief.genre)
