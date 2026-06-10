from __future__ import annotations

from .models import Signal


class TopicGuard:
    REJECT = ["крипт", "airdrop", "эйрдроп", "ваканс", "карьер", "программист", "it ", "вебинар", "эфир", "политик", "выборы", "войн", "санкц", "казино", "ставки"]
    TRAVEL = ["тур", "путеше", "рейс", "билет", "отель", "виза", "пляж", "маршрут", "город", "курорт", "аэропорт", "музей", "еда", "гастр", "поезд", "багаж", "страхов", "экскурс", "море", "горы", "travel"]

    def allow(self, signal: Signal) -> tuple[bool, str]:
        if signal.is_fallback:
            return True, "fallback-тема"
        text = f"{signal.title} {signal.text}".lower()
        for bad in self.REJECT:
            if bad in text:
                return False, f"запрещённая/не travel тема: {bad}"
        if any(good in text for good in self.TRAVEL):
            return True, "travel-сигнал"
        if signal.genre in {"destination_post", "flight_deal", "tour_offer", "hotel_post", "event_trip", "visa_or_residence"}:
            return True, "жанр источника travel"
        return False, "не хватает travel-ценности"
