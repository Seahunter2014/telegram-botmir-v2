from urllib.parse import quote_plus
from .config_loader import read_json, env
from .text_utils import date_to_ddmm

class UrlBuilder:
    def __init__(self):
        self.services = {s["key"]: s for s in read_json("services.json", [])}
        self.cities = read_json("cities_iata.json", {})
        self.marker = env("TRAVELPAYOUTS_MARKER", "98526")

    def service_url(self, key: str) -> str:
        return self.services.get(key, {}).get("url", "")

    def aviasales_route_url(self, route_from: str, route_to: str, date_text: str = "") -> str:
        origin = self.cities.get(route_from, "")
        dest = self.cities.get(route_to, "")
        if origin and dest:
            ddmm = date_to_ddmm(date_text)
            if ddmm:
                return f"https://www.aviasales.ru/search/{origin}{ddmm}{dest}?marker={self.marker}"
            return f"https://www.aviasales.ru/search/{origin}{dest}?marker={self.marker}"
        return self.service_url("aviasales")

    def hotel_search_url(self, city: str = "") -> str:
        # Партнёрская базовая ссылка безопаснее, чем нерабочий динамический deeplink.
        return self.service_url("ostrovok") or self.service_url("trip_hotels")

    def tourjin_url(self) -> str:
        return self.service_url("tourjin_bot")
