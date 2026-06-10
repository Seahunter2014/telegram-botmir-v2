from __future__ import annotations

from .models import Brief, PostVariant


class EngagementEngine:
    def improve(self, variant: PostVariant, brief: Brief) -> PostVariant:
        text = f"{variant.body}\n{variant.cta_text}".lower()
        if any(x in text for x in ["сохран", "перешл", "комментар", "пишите", "проверь"]):
            return variant
        topic_text = f"{brief.topic} {brief.editorial_angle} {brief.main_fact}".lower()
        price_theme = any(
            x in topic_text
            for x in ["цен", "сезон", "ранн", "брон", "тур", "билет", "отел", "скид", "дат"]
        )
        if brief.genre == "top_list":
            variant.cta_text = "Сохраните пост, чтобы вернуться к этой подборке перед планированием поездки."
        elif brief.genre == "route":
            variant.cta_text = "Сохраните маршрут и проверьте даты заранее — так проще собрать поездку без лишней суеты."
        elif brief.genre in {"flight_deal", "tour_offer", "hotel_post"} or price_theme:
            variant.cta_text = (
                "Перед бронированием сравните соседние даты и 2–3 сервиса: "
                "иногда сдвиг поездки на несколько дней заметно снижает итоговую цену."
            )
        elif brief.genre == "practical_travel":
            variant.cta_text = "Примените этот совет перед следующей поездкой и поделитесь в комментариях своим рабочим лайфхаком."
        else:
            variant.cta_text = "Отправьте пост тому, кому эта идея может пригодиться при планировании поездки."
        return variant
