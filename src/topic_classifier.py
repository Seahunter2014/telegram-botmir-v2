from __future__ import annotations

from datetime import datetime

from .config_loader import CONFIG_DIR, load_json
from .models import Signal


class TopicClassifier:
    def __init__(self):
        self.policy = load_json(CONFIG_DIR / "editorial_policy.json", default={})

    def classify(self, signal: Signal, forced_slot: str = "") -> Signal:
        text = f"{signal.title} {signal.text}".lower()
        genre = signal.genre or "destination_post"
        if any(x in text for x in ["₽", "руб", "билет", "рейс", "перелёт", "перелет", "туда-обратно"]):
            genre = "flight_deal"
        if any(x in text for x in ["тур", "all inclusive", "горящ", "пакет"]):
            genre = "tour_offer"
        if any(x in text for x in ["отель", "гостиниц", "апартамент", "вилла"]):
            genre = "hotel_post"
        if any(x in text for x in ["виза", "внж", "правила въезда", "документ"]):
            genre = "visa_or_residence"
        if any(x in text for x in ["карта", "наличные", "оплата", "swift"]):
            genre = "payment_abroad"
        if any(x in text for x in ["фестиваль", "концерт", "выставк", "ярмарк", "событ"]):
            genre = "event_trip"
        if any(x in text for x in ["топ", "10 ", "5 ", "подборк", "лучших"]):
            genre = "top_list"
        if any(x in text for x in ["маршрут", "дня", "неделю", "24 часа"]):
            genre = "route"
        if any(x in text for x in ["лайфхак", "что взять", "инструкция", "чек-лист", "совет"]):
            genre = "practical_travel"
        if any(x in text for x in ["еда", "кухня", "кофе", "рынок", "вино", "гастр"]):
            genre = "gastronomy_trip"
        signal.genre = genre
        signal.slot = forced_slot or self.slot_for_genre(genre)
        return signal

    def current_slot(self) -> str:
        hour = datetime.now().hour
        if hour < 12:
            return "morning"
        if hour < 17:
            return "day"
        return "evening"

    def slot_for_genre(self, genre: str) -> str:
        slots = self.policy.get("slots", {})
        for slot, genres in slots.items():
            if genre in genres:
                return slot
        if genre in {"flight_deal", "tour_offer", "hotel_post"}:
            return "day"
        if genre in {"practical_travel", "visa_or_residence", "payment_abroad"}:
            return "evening"
        return "morning"
