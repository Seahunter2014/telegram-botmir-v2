from .models import Signal
from .text_utils import extract_price, extract_date_text

class ScoringEngine:
    def score(self, signal: Signal, genre: str, slot: str) -> tuple[int, list[str]]:
        text = f"{signal.title}\n{signal.text}"
        warnings = []
        score = 40
        if signal.url:
            score += 8
        if len(text) > 120:
            score += 8
        if extract_price(text):
            score += 12
        if extract_date_text(text):
            score += 8
        if any(w in text.lower() for w in ["море", "пляж", "город", "маршрут", "отель", "рейс", "билет", "виза", "багаж"]):
            score += 10
        if genre in self.slot_genres(slot):
            score += 10
        else:
            warnings.append("Жанр не идеален для текущего слота, но может быть использован при отсутствии лучшей темы.")
        return min(score, 100), warnings

    def slot_genres(self, slot: str) -> list[str]:
        if slot == "morning":
            return ["destination_post", "hidden_places", "city_break", "weekend_trip", "beach_trip", "mountain_trip", "gastronomy_trip", "inspiration_story"]
        if slot == "day":
            return ["flight_deal", "tour_offer", "hotel_post", "premium_hotel", "last_minute", "family_trip", "event_trip", "weekend_activity"]
        return ["practical_travel", "travel_hack", "visa_or_residence", "relocation", "payment_abroad", "airport_lounge", "insurance_tip", "concert_trip", "discussion_post"]
