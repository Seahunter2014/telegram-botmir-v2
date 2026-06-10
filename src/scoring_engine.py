from __future__ import annotations

from .models import Signal


class ScoringEngine:
    def score(self, signal: Signal, current_slot: str = "") -> Signal:
        text = f"{signal.title} {signal.text}"
        score = 20  # свежесть по умолчанию для свежего источника/fallback
        score += min(20, 5 + len(text) // 80)
        if signal.city or signal.country:
            score += 10
        if signal.price or signal.dates:
            score += 8
        if any(x in text.lower() for x in ["россиян", "из моск", "виза", "карты", "руб", "прям", "стыков"]):
            score += 15
        else:
            score += 7
        if any(x in text.lower() for x in ["море", "пляж", "горы", "город", "музей", "еда", "вид", "марокко", "европ"]):
            score += 10
        else:
            score += 5
        if signal.genre in {"practical_travel", "travel_hack", "visa_or_residence", "payment_abroad", "top_list", "route"}:
            score += 10
        else:
            score += 6
        if signal.genre in {"top_list", "route", "inspiration_story", "destination_post", "discussion_post"}:
            score += 10
        else:
            score += 6
        if signal.genre in {"flight_deal", "tour_offer", "hotel_post", "event_trip", "destination_post", "weekend_trip"}:
            score += 10
        else:
            score += 3
        if current_slot and signal.slot == current_slot:
            score += 5
        signal.score = max(0, min(100, score))
        return signal
