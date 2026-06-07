from __future__ import annotations

from typing import Any

RULES = {
    "flight_deal": ["билет", "авиабилет", "перелёт", "перелет", "рейс", "туда-обратно"],
    "tour_offer": ["тур", "путёвка", "путевка", "пакет", "all inclusive"],
    "hotel_post": ["отель", "гостиница", "проживание"],
    "event_trip": ["событие", "фестиваль", "выставка", "матч"],
    "concert_trip": ["концерт", "артист", "звезда", "турне"],
    "visa_or_residence": ["виза", "внж", "гражданство", "правила въезда", "вид на жительство"],
    "relocation": ["релокация", "переезд", "экспат"],
    "payment_abroad": ["карта", "swift", "оплата за границей", "зарубежная карта"],
    "insurance_tip": ["страховка", "полис"],
    "rail_trip": ["поезд", "жд"],
    "road_trip": ["аренда авто", "машина", "авто"],
    "beach_trip": ["море", "пляж", "остров", "курорт"],
    "mountain_trip": ["горы", "каньон", "озеро"],
}


def classify_signal(signal: dict[str, Any], bundle: Any, slot: str = "day") -> str:
    text = f"{signal.get('title', '')} {signal.get('text', '')} {signal.get('raw_role', '')}".lower()
    source_key = signal.get("source_key", "")
    if source_key == "travelata_telegram":
        return "tour_offer"
    if source_key in {"gorbilet_events", "psgr_concerts"}:
        return "concert_trip" if "концерт" in text else "event_trip"
    if source_key in {"imigrata", "relocate_easy", "ekspat_info"}:
        return "payment_abroad" if any(word in text for word in ["карта", "swift", "оплата"]) else "visa_or_residence"
    if source_key == "trip_activities":
        return "weekend_activity"
    if signal.get("route_from") and signal.get("route_to") and signal.get("price"):
        return "flight_deal"
    if signal.get("event_name"):
        return "concert_trip" if "конц" in text else "event_trip"
    if signal.get("hotel_name") and signal.get("price"):
        return "hotel_post"
    for topic, words in RULES.items():
        if any(word in text for word in words):
            return topic
    return "destination_post" if slot == "morning" else "practical_travel" if slot == "evening" else "weekend_trip"


def infer_slot_by_hour(hour: int) -> str:
    return "morning" if hour < 12 else "day" if hour < 17 else "evening"
