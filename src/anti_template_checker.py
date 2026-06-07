from __future__ import annotations

import re
from typing import Any

from .dedup_engine import is_duplicate_variant


def check_variant(variant: dict, bundle: Any) -> dict:
    text = f"{variant.get('title', '')}\n{variant.get('text', '')}\n{variant.get('cta', '')}"
    issues: list[str] = []
    for phrase in bundle.forbidden.get("phrases", []):
        if phrase.lower() in text.lower():
            issues.append("Запрещённая фраза обнаружена")
    if ("сигнал" + " для") in text.lower():
        issues.append("Внутренняя техническая фраза")
    paragraphs = [part.strip() for part in variant.get("text", "").split("\n") if part.strip()]
    if len(paragraphs) < 3:
        issues.append("Мало абзацев")
    if len(variant.get("text", "")) < 420:
        issues.append("Мало текста и конкретики")
    if len(variant.get("title", "")) < 18:
        issues.append("Слабый заголовок")
    starts: list[str] = []
    for paragraph in paragraphs:
        words = re.findall(r"[A-Za-zА-Яа-яЁё0-9]+", paragraph.lower())
        starts.append(words[0] if words else "")
    if len(starts) >= 3 and len(set(starts)) < len(starts):
        issues.append("Повторяются начала абзацев")
    is_duplicate, reason = is_duplicate_variant(text)
    if is_duplicate:
        issues.append(reason)
    return {"passed": not issues, "issues": issues, "quality_score": max(0, 100 - len(issues) * 18)}
