import re
from .models import Signal

class TopicClassifier:
    def classify(self, signal: Signal) -> str:
        text = f"{signal.title}\n{signal.text}".lower()
        source_genres = signal.raw.get("genres") or signal.raw.get("source", {}).get("genres", [])
        if "₽" in text or "руб" in text or re.search(r"\b\d[\d\s]+\s*р", text):
            if any(w in text for w in ["рейс", "перел", "билет", "авиа"]):
                return "flight_deal"
            if any(w in text for w in ["тур", "отель", "all inclusive", "все включ"]):
                return "tour_offer"
        if any(w in text for w in ["виза", "внж", "шенген", "паспорт", "граница", "консуль", "документ"]):
            return "visa_or_residence"
        if any(w in text for w in ["карта", "swift", "оплата за границей", "банк", "visa", "mastercard"]):
            return "payment_abroad"
        if any(w in text for w in ["концерт", "фестиваль", "выставк", "матч", "событи"]):
            return "event_trip"
        if any(w in text for w in ["багаж", "страхов", "аэропорт", "пересад", "ручная кладь", "лайфхак"]):
            return "practical_travel"
        if any(w in text for w in ["отель", "гостиниц", "resort", "villa", "вилла"]):
            return "hotel_post"
        if source_genres:
            return source_genres[0]
        if any(w in text for w in ["выходн", "2 дня", "3 дня", "уикенд", "weekend"]):
            return "weekend_trip"
        return "destination_post"
