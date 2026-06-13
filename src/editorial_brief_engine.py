from __future__ import annotations

from .config_loader import CONFIG_DIR, load_json
from .models import Brief, Signal


class EditorialBriefEngine:
    def __init__(self):
        self.link_rules = load_json(CONFIG_DIR / "link_rules.json", default={})

    def build(self, signal: Signal) -> Brief:
        rule = self.link_rules.get(signal.genre, self.link_rules.get("default", {}))
        topic = signal.title
        city_country = " ".join(x for x in [signal.city, signal.country] if x)
        media_ru = city_country or topic
        media_en = self._translate_media_query(media_ru or topic)
        angle = signal.angle or self._angle_for_genre(signal)
        return Brief(
            source_key=signal.source_key,
            source_name=signal.source_name,
            source_url=signal.url or signal.source_url,
            topic=topic,
            genre=signal.genre,
            slot=signal.slot,
            city=signal.city,
            country=signal.country,
            price=signal.price,
            dates=signal.dates,
            editorial_angle=angle,
            target_emotion=self._emotion(signal.genre),
            main_fact=signal.text[:500],
            practical_value=self._value(signal.genre),
            cta_level="direct" if signal.genre in {"flight_deal", "tour_offer", "hotel_post"} else "soft",
            allowed_services=rule.get("categories", []),
            forbidden_claims=["не утверждать непроверенные цены", "не выдумывать визовые правила"],
            media_query_ru=media_ru,
            media_query_en=media_en,
        )

    def _angle_for_genre(self, signal: Signal) -> str:
        mapping = {
            "flight_deal": "короткий конкретный оффер: маршрут, цена, даты, что проверить перед покупкой",
            "tour_offer": "готовая поездка: кому подходит, что включено, почему стоит проверить",
            "practical_travel": "полезный гайд с конкретными шагами и сохранением в закладки",
            "top_list": "подборка с понятным принципом отбора и практическими подсказками",
            "route": "готовый маршрут с логикой дней, сезона и бюджета",
            "event_trip": "событие как повод для поездки",
        }
        return mapping.get(signal.genre, "авторский travel-пост с пользой, эмоцией и понятным CTA")

    def _emotion(self, genre: str) -> str:
        if genre in {"inspiration_story", "destination_post", "hidden_places"}:
            return "вдохновение и желание сохранить"
        if genre in {"flight_deal", "tour_offer", "hotel_post"}:
            return "быстро проверить предложение"
        if genre in {"practical_travel", "visa_or_residence", "payment_abroad"}:
            return "польза и уверенность"
        return "интерес и вовлечение"

    def _value(self, genre: str) -> str:
        if genre in {"flight_deal", "tour_offer", "hotel_post"}:
            return "экономия времени на поиске и проверка условий"
        if genre in {"practical_travel", "travel_hack"}:
            return "готовая инструкция"
        if genre in {"top_list", "route"}:
            return "готовая подборка для сохранения"
        return "идея для следующей поездки"

    def _translate_media_query(self, query: str) -> str:
        repl = {"Марокко":"Morocco","Турция":"Turkey","Анталья":"Antalya","Европа":"Europe","Москва":"Moscow","Сочи":"Sochi","Грузия":"Georgia","Италия":"Italy","Франция":"France","Испания":"Spain","море":"sea","пляж":"beach","горы":"mountains","еда":"street food"}
        out = query
        for ru, en in repl.items():
            out = out.replace(ru, en)
        return out if out != query else f"{query} travel"
