from __future__ import annotations

from .models import Brief, PostVariant


class EngagementEngine:
    def improve(self, variant: PostVariant, brief: Brief) -> PostVariant:
        text = f"{variant.body}\n{variant.cta_text}".lower()
        if any(x in text for x in ["сохран", "перешл", "комментар", "пишите", "проверь"]):
            return variant
        if brief.genre in {"top_list", "route", "practical_travel"}:
            variant.cta_text = "Сохраните пост — такие подборки обычно нужны внезапно."
        elif brief.genre in {"flight_deal", "tour_offer", "hotel_post"}:
            variant.cta_text = "Проверьте актуальные условия под свои даты — цены могут быстро меняться."
        else:
            variant.cta_text = "Отправьте другу, с которым давно пора выбраться в новую поездку."
        return variant
