from __future__ import annotations

from typing import Any

from .dedup_engine import rotation_penalty
from .source_manager import freshness_score


def score_signal(signal: dict, topic: str, slot: str, bundle: Any) -> dict:
    text = f"{signal.get('title', '')} {signal.get('text', '')}"
    concreteness = 0
    if signal.get("price"):
        concreteness += 7
    if signal.get("city") or signal.get("route_to"):
        concreteness += 5
    if signal.get("route_from") and signal.get("route_to"):
        concreteness += 6
    if signal.get("event_date") or signal.get("nights"):
        concreteness += 5
    if any(char.isdigit() for char in text):
        concreteness += 4
    if len(text) > 180:
        concreteness += 4

    emotion = 15 if topic in {"hidden_places", "inspiration_story", "viral_travel", "luxury_escape", "beach_trip"} else 10
    shareability = 15 if topic in {"viral_travel", "weird_travel", "hidden_places", "discussion_post"} else 12 if topic in {"practical_travel", "travel_hack", "visa_or_residence"} else 8
    usefulness = 10 if topic in {"practical_travel", "travel_hack", "visa_or_residence", "payment_abroad", "insurance_tip"} else 8 if topic in {"flight_deal", "tour_offer", "event_trip", "concert_trip"} else 6

    rule = next((item for item in bundle.link_rules["rules"] if item["topic"] == topic), None)
    affiliate_fit = 6 if rule and rule.get("max_links", 0) == 0 else 10 if rule else 4
    slot_fit = 10 if topic in bundle.policy.get("slots", {}).get(slot, {}).get("preferred_topics", []) else 4

    penalty, reasons = rotation_penalty(signal, topic)
    parts = {
        "freshness": freshness_score(signal),
        "concreteness": min(24, concreteness),
        "emotion": emotion,
        "shareability": shareability,
        "usefulness": usefulness,
        "affiliate_fit": affiliate_fit,
        "slot_fit": slot_fit,
    }
    total = max(0, min(100, sum(parts.values()) - penalty))
    return {"score": total, "parts": parts, "penalty": penalty, "penalty_reasons": reasons}
