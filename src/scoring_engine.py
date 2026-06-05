from __future__ import annotations
from typing import Any
from .source_manager import freshness_score
from .dedup_engine import rotation_penalty

EVENT_WORDS = ['выставка', 'фестиваль', 'концерт', 'событие', 'шоу', 'ярмарка', 'музей', 'парк', 'билет']
GENERIC_STOP = ['подробнее', 'читать далее', 'новости', 'главная', 'подборка', 'лучшие предложения']


def _text(signal: dict) -> str:
    return f"{signal.get('title', '')} {signal.get('text', '')}".lower()


def _concrete_points(signal: dict, topic: str) -> int:
    text = _text(signal)
    points = 0
    if signal.get('price'):
        points += 7
    if signal.get('route_from') and signal.get('route_to'):
        points += 8
    if signal.get('depart_human'):
        points += 5
    if signal.get('city'):
        points += 5
    if any(ch.isdigit() for ch in text):
        points += 3
    if len(text) > 220:
        points += 4
    if topic in {'event_trip', 'concert_trip', 'weekend_activity', 'activities_post'} and any(w in text for w in EVENT_WORDS):
        points += 5
    return min(20, points)


def weak_signal_cap(signal: dict, topic: str) -> int | None:
    text = _text(signal)
    # Не берём навигационные ссылки и пустые карточки сайта как темы для редакции.
    if len(text) < 80 and not (signal.get('price') or signal.get('route_to') or signal.get('city')):
        return 42
    if any(x == text.strip() for x in GENERIC_STOP):
        return 35
    if topic == 'flight_deal' and not (signal.get('price') or (signal.get('route_from') and signal.get('route_to'))):
        return 48
    if topic in {'event_trip', 'concert_trip', 'weekend_activity', 'activities_post'} and not (signal.get('city') or any(w in text for w in EVENT_WORDS)):
        return 50
    return None


def score_signal(signal: dict, topic: str, slot: str, bundle: Any) -> dict:
    text = _text(signal)
    concrete = _concrete_points(signal, topic)
    emotion = 15 if topic in {'hidden_places', 'inspiration_story', 'viral_travel', 'luxury_escape', 'beach_trip'} else 10
    share = 15 if topic in {'viral_travel', 'weird_travel', 'hidden_places', 'discussion_post'} else 12 if topic in {'practical_travel', 'travel_hack', 'visa_or_residence'} else 8
    use = 10 if topic in {'practical_travel', 'travel_hack', 'visa_or_residence', 'payment_abroad', 'insurance_tip'} else 8 if topic in {'flight_deal', 'tour_offer', 'event_trip'} else 6
    rule = next((r for r in bundle.link_rules['rules'] if r['topic'] == topic), None)
    aff = 6 if rule and rule.get('max_links', 0) == 0 else 10 if rule else 4
    slot_fit = 10 if topic in bundle.policy.get('slots', {}).get(slot, {}).get('preferred_topics', []) else 4
    pen, reasons = rotation_penalty(signal, topic)
    parts = {
        'freshness': freshness_score(signal),
        'concreteness': concrete,
        'emotion': emotion,
        'shareability': share,
        'usefulness': use,
        'affiliate_fit': aff,
        'slot_fit': slot_fit,
    }
    raw = max(0, min(100, sum(parts.values()) - pen))
    cap = weak_signal_cap(signal, topic)
    score = min(raw, cap) if cap is not None else raw
    if cap is not None:
        reasons = reasons + [f'слабый сигнал: потолок score {cap}']
    return {'score': score, 'parts': parts, 'penalty': pen, 'penalty_reasons': reasons, 'raw_score': raw}
