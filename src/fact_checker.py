from .models import EditorialBrief, PostVariant


class FactChecker:
    def review(self, brief: EditorialBrief, variant: PostVariant) -> list[str]:
        warnings: list[str] = []
        combined = f"{variant.title}\n{variant.body}\n{variant.cta_text}".lower()

        if brief.genre == "flight_deal":
            if brief.price and brief.price not in f"{variant.title} {variant.body} {variant.cta_text}":
                warnings.append("В тексте потерялась цена из сигнала — оффер стал слабее.")
            if brief.date_text and brief.date_text.lower() not in combined:
                warnings.append("В тексте нет даты/периода из сигнала — читателю сложнее проверить оффер.")

        if brief.genre in {"event_trip", "concert_trip"} and brief.date_text and brief.date_text.lower() not in combined:
            warnings.append("Событие описано без даты/периода — это снижает полезность поста.")

        if brief.genre in {"visa_or_residence", "payment_abroad"}:
            if "билет" in combined or "отел" in combined:
                warnings.append("Для визовой/платёжной темы всплыли нерелевантные travel-offer слова.")

        return warnings
