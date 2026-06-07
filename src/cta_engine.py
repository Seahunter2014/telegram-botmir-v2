from .models import EditorialBrief, PostVariant, Button
from .url_builder import UrlBuilder

class CTAEngine:
    def __init__(self):
        self.urls = UrlBuilder()

    def apply(self, brief: EditorialBrief, variant: PostVariant) -> PostVariant:
        # Пересобираем кнопки по смыслу ТЗ, чтобы GPT не вставил случайные ссылки.
        genre = brief.genre
        buttons: list[Button] = []
        source_url = brief.signal.url or brief.signal.source_url
        if genre == "flight_deal":
            if source_url:
                buttons.append(Button("🔎 Открыть предложение", source_url, "source"))
            buttons.append(Button("✈️ Проверить билеты", self.urls.aviasales_route_url(brief.route_from, brief.route_to, brief.date_text), "aviasales"))
            if brief.route_to:
                buttons.append(Button("🏨 Отели на даты", self.urls.hotel_search_url(brief.route_to), "ostrovok"))
        elif genre in ["destination_post", "weekend_trip", "city_break", "beach_trip", "family_trip"]:
            buttons.append(Button("✈️ Билеты", self.urls.service_url("aviasales"), "aviasales"))
            buttons.append(Button("🏨 Отели", self.urls.service_url("ostrovok"), "ostrovok"))
            if genre in ["destination_post", "weekend_trip", "family_trip"]:
                # TourJin — мягкая внутренняя реклама, только когда не перегружает CTA.
                buttons.append(Button("🧞 Подобрать в TourJin", self.urls.tourjin_url(), "tourjin_bot"))
        elif genre in ["tour_offer", "hot_tour", "last_minute", "seasonal_offer"]:
            buttons.append(Button("🌴 Посмотреть туры", self.urls.service_url("travelata"), "travelata"))
            buttons.append(Button("🧞 Подобрать в TourJin", self.urls.tourjin_url(), "tourjin_bot"))
        elif genre in ["hotel_post", "premium_hotel"]:
            buttons.append(Button("🏨 Посмотреть отели", self.urls.service_url("ostrovok"), "ostrovok"))
            buttons.append(Button("✈️ Билеты", self.urls.service_url("aviasales"), "aviasales"))
        elif genre in ["event_trip", "concert_trip", "activities_post", "weekend_activity"]:
            if source_url:
                buttons.append(Button("🎟 Открыть событие", source_url, "source"))
            buttons.append(Button("✈️ Билеты в город", self.urls.service_url("aviasales"), "aviasales"))
            buttons.append(Button("🏨 Отели рядом", self.urls.service_url("ostrovok"), "ostrovok"))
        elif genre in ["visa_or_residence", "payment_abroad", "relocation"]:
            buttons.append(Button("💳 Карта для поездки", self.urls.service_url("five_cards"), "five_cards"))
            if genre != "payment_abroad":
                buttons.append(Button("🛡 Страховка", self.urls.service_url("cherehapa"), "cherehapa"))
        elif genre in ["practical_travel", "travel_hack", "insurance_tip"]:
            buttons.append(Button("🛡 Проверить страховку", self.urls.service_url("cherehapa"), "cherehapa"))
        # Убираем пустые ссылки и ограничиваем количество.
        variant.buttons = [b for b in buttons if b.url][:3]
        return variant
