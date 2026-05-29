from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any

from .classifier import classify_signal
from .models import RankedSignal, Signal
from .storage import load_state, recent_titles


def _identity(text: str) -> str:
    return hashlib.sha1(text.lower().strip().encode("utf-8")).hexdigest()[:16]


def rank_signals(signals: list[Signal], configs: dict[str, Any]) -> list[RankedSignal]:
    recent = recent_titles()
    state = load_state()
    published = state.get("published", []) + state.get("tested", [])
    recent_topics = [item.get("topic") for item in published[-5:]]
    recent_sources = [item.get("source_key") for item in published[-5:]]
    ranked: list[RankedSignal] = []
    for signal in signals:
        if signal.title.strip().lower() in recent:
            continue
        topic = classify_signal(signal, configs)
        source_priority = int(signal.raw.get("source_priority", 50))
        score = source_priority + topic.priority
        reasons = [f"приоритет источника {source_priority}", f"приоритет темы {topic.priority}"]
        if topic.key not in recent_topics[-topic.cooldown_posts:]:
            score += 20
            reasons.append("тема не повторялась недавно")
        else:
            score -= 40
            reasons.append("тема недавно была — штраф")
        if signal.source_key not in recent_sources[-2:]:
            score += 10
            reasons.append("источник не залипал подряд")
        else:
            score -= 20
            reasons.append("источник уже был недавно")
        text = f"{signal.title} {signal.summary}".lower()
        if any(x in text for x in ["₽", "руб", "цена", "скид", "дешев"]):
            score += 12
            reasons.append("есть коммерческий крючок")
        if any(x in text for x in ["нов", "запуст", "открыл", "измен", "тест", "начал"]):
            score += 8
            reasons.append("есть новостной повод")
        ranked.append(RankedSignal(signal=signal, topic=topic, score=score, reasons=reasons))
    ranked.sort(key=lambda item: item.score, reverse=True)
    return ranked


def package_key(ranked: RankedSignal) -> str:
    return _identity(f"{ranked.signal.source_key}|{ranked.signal.title}|{datetime.now(timezone.utc).date()}")
