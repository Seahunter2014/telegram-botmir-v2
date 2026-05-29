from __future__ import annotations

from typing import Any

from .models import Signal, Topic

KEYWORDS: dict[str, list[str]] = {
    "cheap_flight": ["билет", "перелет", "перелёт", "авиабилет", "рейс", "руб", "₽", "из москвы", "из сочи"],
    "tour_offer": ["тур", "вылет", "all inclusive", "отель", "ночей", "горящий"],
    "last_minute": ["горящий", "сегодня", "завтра", "последние места"],
    "hotel_post": ["отель", "гостиница", "номер", "вид", "завтрак", "resort"],
    "premium_hotel": ["люкс", "премиум", "5*", "spa", "вилла", "бутик"],
    "event_trip": ["фестиваль", "выставка", "событие", "афиша", "билеты на", "шоу"],
    "concert_trip": ["концерт", "артист", "мировые звезды", "звёзды", "стадион"],
    "visa_news": ["виза", "шенген", "въезд", "паспорт", "консульство", "правила"],
    "relocation": ["внж", "пмж", "переезд", "релокация", "налоги", "резидент"],
    "practical_travel": ["как", "что проверить", "ошибка", "совет", "правила", "багаж", "доставка багажа", "ржд"],
    "weekend_activity": ["выходные", "куда сходить", "спектакль", "музей", "парк"],
    "activities_post": ["экскурсия", "впечатление", "маршрут", "прогулка", "гид"],
    "family_trip": ["дети", "семь", "семей", "аквапарк"],
    "beach_trip": ["море", "пляж", "курорт", "анталья", "египет"],
    "mountain_trip": ["горы", "каньон", "ущелье", "тропа", "водопад"],
    "gastronomy_trip": ["еда", "ресторан", "вино", "кухня", "гастро"],
    "hidden_places": ["необыч", "секрет", "неочевид", "маленький город", "деревня"],
}


def load_topics(configs: dict[str, Any]) -> dict[str, Topic]:
    result: dict[str, Topic] = {}
    for item in configs["topics"]["topics"]:
        result[item["key"]] = Topic(**item)
    return result


def classify_signal(signal: Signal, configs: dict[str, Any]) -> Topic:
    topics = load_topics(configs)
    if signal.topic_hint and signal.topic_hint in topics:
        return topics[signal.topic_hint]
    text = f"{signal.title} {signal.summary}".lower()
    source_roles = signal.raw.get("roles") or []
    best_key = None
    best_score = -1
    for key, words in KEYWORDS.items():
        score = sum(1 for word in words if word.lower() in text)
        if key in source_roles:
            score += 2
        if score > best_score:
            best_score = score
            best_key = key
    if best_key and best_key in topics and best_score > 0:
        return topics[best_key]
    for role in source_roles:
        if role in topics:
            return topics[role]
    return topics["destination_post"]
