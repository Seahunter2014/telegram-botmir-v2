from __future__ import annotations

from .models import Brief, PostVariant


class EngagementEngine:
    def improve(self, variant: PostVariant, brief: Brief) -> PostVariant:
        # Главный CTA пишет OpenAI по master prompt. Код добавляет финал только если OpenAI его не дал.
        if variant.cta_text and variant.cta_text.strip():
            return variant
        topic_text = f"{brief.topic} {brief.editorial_angle} {brief.main_fact}".lower()
        price_theme = any(
            x in topic_text
            for x in ["цен", "сезон", "ранн", "брон", "тур", "билет", "отел", "скид", "дат"]
        )
        if brief.genre == "top_list":
            variant.cta_text = "Сохраните пост и вернитесь к нему, когда будете выбирать направление под свои даты."
        elif brief.genre == "route":
            variant.cta_text = "Сохраните маршрут и заранее проверьте сезон, переезды и даты — так проще понять реальный бюджет поездки."
        elif brief.genre in {"flight_deal", "tour_offer", "hotel_post"} or price_theme:
            variant.cta_text = (
                "Перед бронированием сравните соседние даты и 2–3 сервиса: "
                "иногда сдвиг поездки на несколько дней заметно снижает итоговую цену."
            )
        elif brief.genre == "practical_travel":
            variant.cta_text = "Проверьте этот совет на своих датах и поделитесь в комментариях, какой приём реально сработал у вас."
        else:
            variant.cta_text = "Отправьте пост тому, кому эта идея пригодится при планировании следующей поездки."
        return variant
