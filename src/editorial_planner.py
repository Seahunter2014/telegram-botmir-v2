from __future__ import annotations

from typing import Any

from .offer_formatter import direct_offer_url
from .rotation_engine import slot_name_ru


def cta_level(topic: str) -> str:
    if topic in {"flight_deal", "tour_offer", "last_minute", "hot_tour", "hotel_post", "premium_hotel"}:
        return "прямой"
    if topic in {"visa_or_residence", "relocation", "payment_abroad", "practical_travel"}:
        return "мягкий"
    if topic in {"inspiration_story", "viral_travel", "discussion_post"}:
        return "без продажи"
    return "редакционный"


def plan_post(signal: dict, topic: str, score: dict, slot: str, bundle: Any) -> dict:
    cfg = next((item for item in bundle.topics["topics"] if item["key"] == topic), {})
    return {
        "topic": topic,
        "genre": cfg.get("name", topic),
        "slot": slot,
        "slot_ru": slot_name_ru(slot),
        "source": signal.get("source_name", ""),
        "source_url": signal.get("url", ""),
        "city": signal.get("city", ""),
        "country": signal.get("country", ""),
        "price": signal.get("price", ""),
        "route_from": signal.get("route_from", ""),
        "route_to": signal.get("route_to", ""),
        "nights": signal.get("nights", ""),
        "event_name": signal.get("event_name", ""),
        "event_date": signal.get("event_date", ""),
        "hotel_name": signal.get("hotel_name", ""),
        "is_direct": signal.get("is_direct", False),
        "direct_offer_url": direct_offer_url({}, signal),
        "has_direct_offer": bool(direct_offer_url({}, signal)),
        "main_fact": signal.get("title", ""),
        "source_text": signal.get("text", ""),
        "target_emotion": "сохранить, переслать или открыть ссылку по смыслу",
        "hook_angle": _hook(topic),
        "practical_value": _value(topic),
        "cta_level": cta_level(topic),
        "allowed_categories": cfg.get("cta_categories", []),
        "max_links": cfg.get("max_links", 2),
        "forbidden_claims": [
            "Не обещать наличие мест.",
            "Не утверждать цену как гарантированную.",
            "Не делать юридические выводы.",
        ],
        "score": score,
    }


def _hook(topic: str) -> str:
    hooks = {
        "flight_deal": "билет как повод быстро собрать поездку",
        "tour_offer": "готовый сценарий отдыха",
        "destination_post": "почему направление актуально сейчас",
        "hotel_post": "отель как самостоятельный повод",
        "event_trip": "событие как причина увидеть город",
        "concert_trip": "конкретное событие + конкретный город + понятные даты",
        "visa_or_residence": "что важно понять заранее",
        "practical_travel": "маленькое решение, которое упрощает поездку",
    }
    return hooks.get(topic, "редакционный travel-повод")


def _value(topic: str) -> str:
    if topic in {"flight_deal", "tour_offer", "hotel_post", "premium_hotel"}:
        return "дать понятный следующий шаг"
    if topic in {"practical_travel", "travel_hack", "visa_or_residence", "payment_abroad"}:
        return "помочь избежать ошибки"
    return "показать, как превратить идею в поездку"
