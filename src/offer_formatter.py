from __future__ import annotations

from html import escape


OFFER_TOPICS = {
    "flight_deal",
    "last_minute",
    "tour_offer",
    "hot_tour",
    "seasonal_offer",
    "hotel_post",
    "premium_hotel",
    "event_trip",
    "concert_trip",
    "weekend_activity",
    "activities_post",
}


def direct_offer_url(plan: dict, signal: dict) -> str:
    url = (signal.get("url") or "").strip()
    source_url = (signal.get("source_url") or "").strip()
    if url and url != source_url:
        return url
    return url or source_url


def build_offer_line(plan: dict, signal: dict) -> str:
    topic = plan.get("topic", "")
    url = direct_offer_url(plan, signal)
    if topic not in OFFER_TOPICS or not url:
        return ""

    price = (plan.get("price") or signal.get("price") or "").strip()
    route_from = (plan.get("route_from") or signal.get("route_from") or "").strip()
    route_to = (plan.get("route_to") or signal.get("route_to") or "").strip()
    city = (plan.get("city") or signal.get("city") or "").strip()
    country = (plan.get("country") or signal.get("country") or "").strip()
    nights = (plan.get("nights") or signal.get("nights") or "").strip()
    hotel_name = (plan.get("hotel_name") or signal.get("hotel_name") or "").strip()
    event_name = (plan.get("event_name") or signal.get("event_name") or "").strip()
    event_date = (plan.get("event_date") or signal.get("event_date") or "").strip()
    direct = bool(plan.get("is_direct") or signal.get("is_direct"))

    if topic in {"flight_deal", "last_minute"} and route_from and route_to and price:
        anchor = f"{route_from} -> {route_to} {'есть прямые рейсы' if direct else 'есть билеты'} от {price}"
        tail = " в одну сторону" if direct else ""
        return f'Сейчас по направлению <a href="{escape(url, quote=True)}">{escape(anchor)}</a>{escape(tail)}.'

    if topic in {"tour_offer", "hot_tour", "seasonal_offer"} and price:
        subject = f"туры {f'в {country}' if country else 'по направлению'}"
        if city:
            subject = f"туры в {city}"
        if nights:
            anchor = f"{subject} на {nights} — от {price}"
        else:
            anchor = f"{subject} — от {price}"
        return f'Сейчас <a href="{escape(url, quote=True)}">{escape(anchor)}</a>.'

    if topic in {"hotel_post", "premium_hotel"} and hotel_name:
        anchor = f"{hotel_name}{f' — от {price}' if price else ''}"
        return f'По этой теме в источнике есть конкретный оффер: <a href="{escape(url, quote=True)}">{escape(anchor)}</a>.'

    if topic in {"event_trip", "concert_trip", "weekend_activity", "activities_post"} and event_name:
        date_part = f" — {event_date}" if event_date else ""
        location = f" в {city}" if city else ""
        anchor = f"{event_name}{location}{date_part}"
        return f'Если хотите идти от повода, вот он: <a href="{escape(url, quote=True)}">{escape(anchor)}</a>.'

    if price and city:
        anchor = f"{city} — от {price}"
        return f'Сейчас <a href="{escape(url, quote=True)}">{escape(anchor)}</a>.'

    return ""
