from __future__ import annotations

from urllib.parse import urlparse

from .models import EditorialBrief, PostVariant, Button
from .url_builder import UrlBuilder


class CTAEngine:
    """
    Builds buttons ONLY by editorial meaning.

    Critical rules from TZ:
    - do not advertise чужие Telegram-каналы;
    - source links are not affiliate links and must not be used for flight deals;
    - flight deals must lead to concrete ticket search when route is known;
    - TourJin is allowed only as a soft internal promo where it is relevant.
    """

    def __init__(self):
        self.urls = UrlBuilder()

    def apply(self, brief: EditorialBrief, variant: PostVariant) -> PostVariant:
        genre = brief.genre
        buttons: list[Button] = []

        if genre == "flight_deal":
            ticket_url = self.urls.aviasales_route_url(
                brief.route_from,
                brief.route_to,
                brief.date_text,
            )
            buttons.append(Button("✈️ Проверить билеты", ticket_url, "aviasales"))

            if brief.route_to:
                hotel_url = self.urls.hotel_search_url(brief.route_to)
                if hotel_url:
                    buttons.append(Button("🏨 Отели на даты", hotel_url, "ostrovok"))

        elif genre in ["destination_post", "weekend_trip", "city_break", "beach_trip", "family_trip"]:
            buttons.append(Button("✈️ Билеты", self.urls.service_url("aviasales"), "aviasales"))
            buttons.append(Button("🏨 Отели", self.urls.service_url("ostrovok"), "ostrovok"))
            if genre in ["destination_post", "weekend_trip", "family_trip"]:
                buttons.append(Button("🧞 Подобрать поездку в TourJin", self.urls.tourjin_url(), "tourjin_bot"))

        elif genre in ["tour_offer", "hot_tour", "last_minute", "seasonal_offer"]:
            buttons.append(Button("🌴 Посмотреть туры", self.urls.service_url("travelata"), "travelata"))
            buttons.append(Button("🧞 Подобрать в TourJin", self.urls.tourjin_url(), "tourjin_bot"))

        elif genre in ["hotel_post", "premium_hotel"]:
            buttons.append(Button("🏨 Посмотреть отели", self.urls.service_url("ostrovok"), "ostrovok"))
            if brief.city or brief.route_to:
                buttons.append(Button("✈️ Билеты в город", self.urls.service_url("aviasales"), "aviasales"))

        elif genre in ["event_trip", "concert_trip", "activities_post", "weekend_activity"]:
            official = self._official_non_telegram_source(brief)
            if official:
                buttons.append(Button("🎟 Открыть событие", official, "source"))
            buttons.append(Button("🗺 Экскурсии и активности", self.urls.service_url("trip_activities") or self.urls.service_url("sputnik8"), "activities"))
            if brief.city or brief.route_to:
                buttons.append(Button("✈️ Билеты в город", self.urls.service_url("aviasales"), "aviasales"))

        elif genre in ["visa_or_residence", "payment_abroad", "relocation"]:
            buttons.append(Button("💳 Карта для поездки", self.urls.service_url("five_cards"), "five_cards"))
            if genre != "payment_abroad":
                buttons.append(Button("🛡 Страховка", self.urls.service_url("cherehapa"), "cherehapa"))

        elif genre in ["practical_travel", "travel_hack", "insurance_tip"]:
            # Practical posts should not be overloaded with sales links.
            if "страх" in (brief.signal.text + brief.signal.title).lower():
                buttons.append(Button("🛡 Проверить страховку", self.urls.service_url("cherehapa"), "cherehapa"))
            else:
                buttons.append(Button("🧞 Задать вопрос TourJin", self.urls.tourjin_url(), "tourjin_bot"))

        variant.buttons = self._clean_buttons(buttons, genre)
        return variant

    def _official_non_telegram_source(self, brief: EditorialBrief) -> str:
        """Allow source button only if it is NOT a Telegram channel/post."""
        url = brief.signal.url or brief.signal.source_url or ""
        if not url:
            return ""
        parsed = urlparse(url)
        host = (parsed.netloc or "").lower()
        if host in {"t.me", "telegram.me", "web.telegram.org"} or host.endswith(".t.me"):
            return ""
        return url

    def _clean_buttons(self, buttons: list[Button], genre: str) -> list[Button]:
        result: list[Button] = []
        seen: set[str] = set()
        for b in buttons:
            if not b.url:
                continue
            # Absolute ban: do not send channel readers to other Telegram channels,
            # except our own TourJin bot.
            parsed = urlparse(b.url)
            host = (parsed.netloc or "").lower()
            is_telegram = host in {"t.me", "telegram.me", "web.telegram.org"} or host.endswith(".t.me")
            if is_telegram and b.service_key != "tourjin_bot":
                continue
            key = b.text + "|" + b.url
            if key in seen:
                continue
            seen.add(key)
            result.append(b)
        return result[:3]
