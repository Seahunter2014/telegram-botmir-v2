from .models import Signal, EditorialBrief
from .signal_extractor import enrich_signal
from .config_loader import read_json

GENRE_SERVICES = {
    "flight_deal": ["aviasales", "ostrovok", "trip_hotels", "tourjin_bot"],
    "tour_offer": ["travelata", "onlinetours", "cherehapa", "tourjin_bot"],
    "destination_post": ["aviasales", "ostrovok", "sputnik8", "trip_activities", "tourjin_bot"],
    "weekend_trip": ["aviasales", "ostrovok", "sputnik8", "tourjin_bot"],
    "city_break": ["aviasales", "ostrovok", "sputnik8", "tourjin_bot"],
    "event_trip": ["ticketnetwork", "aviasales", "ostrovok"],
    "hotel_post": ["ostrovok", "trip_hotels", "aviasales", "tourjin_bot"],
    "visa_or_residence": ["five_cards", "ppl_visa_platinum", "cherehapa"],
    "payment_abroad": ["five_cards", "ppl_visa_platinum", "ppl_visa_gold"],
    "practical_travel": ["cherehapa", "vip_zal", "tourjin_bot"],
}

class EditorialBriefEngine:
    def build(self, signal: Signal, genre: str, slot: str, score: int, warnings: list[str]) -> EditorialBrief:
        enriched = enrich_signal(signal)
        return EditorialBrief(
            signal=signal,
            genre=genre,
            slot=slot,
            score=score,
            city=enriched.get("city", ""),
            country=enriched.get("country", ""),
            route_from=enriched.get("route_from", ""),
            route_to=enriched.get("route_to", ""),
            price=enriched.get("price", ""),
            date_text=enriched.get("date_text", ""),
            editorial_angle=self.angle_for_genre(genre),
            target_emotion=self.emotion_for_genre(genre),
            allowed_services=GENRE_SERVICES.get(genre, ["tourjin_bot"]),
            warnings=warnings,
        )

    def angle_for_genre(self, genre: str) -> str:
        return {
            "flight_deal": "короткий конкретный оффер: маршрут, цена, дата, что проверить перед покупкой",
            "tour_offer": "готовый отдых: кому подходит, что важно проверить, мягкий коммерческий CTA",
            "destination_post": "идея поездки: почему место интересно сейчас и что там почувствует читатель",
            "event_trip": "событие как повод для поездки, а не пересказ афиши",
            "practical_travel": "практическая боль путешественника и короткое решение",
            "visa_or_residence": "осторожная полезная заметка без лишней продажи",
        }.get(genre, "travel-повод, который нужно превратить в живой Telegram-пост")

    def emotion_for_genre(self, genre: str) -> str:
        return {
            "flight_deal": "быстрая выгода и желание проверить даты",
            "tour_offer": "ощущение готового решения",
            "destination_post": "желание сохранить место",
            "event_trip": "интерес и желание собрать поездку вокруг события",
            "practical_travel": "польза и желание сохранить",
        }.get(genre, "интерес, польза, желание сохранить")
