from __future__ import annotations

import re
from datetime import datetime

from .anti_template_checker import AntiTemplateChecker
from .models import Brief, PostVariant


class QualitySelector:
    def __init__(self, min_score: int = 85):
        self.min_score = min_score
        self.checker = AntiTemplateChecker()

    def score_variant(self, variant: PostVariant, brief: Brief) -> PostVariant:
        # Оценке, которую вернула модель, не доверяем. Считаем заново.
        score = 0
        reasons: list[str] = []
        title = variant.title.strip()
        body = variant.body.strip()
        cta = variant.cta_text.strip()
        full = f"{title}\n{body}\n{cta}\n{' '.join(variant.hashtags or [])}"
        lower = full.lower()

        if 18 <= len(title) <= 95:
            score += 10; reasons.append("заголовок конкретный")
        elif title:
            score += 5; reasons.append("заголовок есть, но требует точности")

        body_len = len(body)
        if 700 <= body_len <= 2600:
            score += 18; reasons.append("объём поста подходит Telegram")
        elif 450 <= body_len < 700 or 2600 < body_len <= 3600:
            score += 10; reasons.append("объём допустимый")
        else:
            variant.warnings.append("неудачный объём текста")

        paragraphs = [p for p in body.split("\n\n") if p.strip()]
        if len(paragraphs) >= 5:
            score += 12; reasons.append("есть структура и короткие блоки")
        elif len(paragraphs) >= 3:
            score += 7; reasons.append("структура есть, но можно усилить")
        else:
            variant.warnings.append("текст выглядит сплошным потоком: мало абзацев")

        visual_markers = ["────", "✅", "💡", "📌", "🧭", "🗓", "🌍", "✈️", "🏨", "🌊", "🎟", "🔥"]
        visual_count = sum(1 for x in visual_markers if x in full)
        bold_count = len(re.findall(r"\*\*[^*]{3,80}\*\*|<b>[^<]{3,80}</b>", full))
        if visual_count >= 3:
            score += 7; reasons.append("есть визуальное оформление и эмодзи по смыслу")
        else:
            variant.warnings.append("мало визуальной структуры: нужны эмодзи-маркеры и разделители")
        if bold_count >= 2:
            score += 6; reasons.append("есть выделенные подзаголовки")
        else:
            variant.warnings.append("нет выделенных подзаголовков")
        if "──────✦──────" in full:
            score += 3

        concrete_markers = ["₽", "руб", "%", "дн", "день", "даты", "багаж", "отель", "рейс", "пляж", "район", "сезон", "брон", "проверь", "сравн", "эконом"]
        concrete_count = sum(1 for x in concrete_markers if x in lower)
        score += min(14, concrete_count * 2)
        if concrete_count >= 4:
            reasons.append("достаточно практической конкретики")

        if any(x in lower for x in ["проверь", "сравн", "выберите", "заранее", "сдвиг", "уведомлен", "соседн", "условия"]):
            score += 12; reasons.append("есть практический следующий шаг")

        if cta:
            score += 8; reasons.append("финал есть")
            if any(x in cta.lower() for x in ["проверь", "сравн", "заранее", "сдвиг", "уведомлен", "комментар", "сохран"]):
                score += 7; reasons.append("финал связан с действием читателя")
        else:
            variant.warnings.append("нет финального блока")

        if variant.hashtags and 3 <= len(variant.hashtags) <= 7:
            score += 6; reasons.append("хештеги в норме")
        elif variant.hashtags:
            score += 3

        # Жанровая проверка финала.
        if "подборк" in cta.lower() and brief.genre not in {"top_list", "route"}:
            score -= 25
            variant.warnings.append("слово «подборка» использовано не по жанру")
        if "маршрут" in cta.lower() and brief.genre not in {"route", "top_list", "destination_post"}:
            score -= 15
            variant.warnings.append("маршрутный финал не соответствует жанру")

        # Устаревшие офферы.
        current_year = datetime.now().year
        years = [int(y) for y in re.findall(r"\b(20\d{2})\b", full)]
        old_years = [y for y in years if y < current_year]
        if old_years and brief.genre in {"flight_deal", "tour_offer", "hotel_post", "event_trip"}:
            score -= 35
            variant.warnings.append(f"в оффере есть устаревший год: {min(old_years)}")

        # Антишаблон.
        bad_phrases = [
            "мечта зовёт", "незабываем", "райский уголок", "уникальная возможность",
            "сердце биться чаще", "без лишней суеты", "travel-ценность",
            "пора отправиться", "идеальный момент для отдыха", "доступны каждому",
        ]
        found_bad = [x for x in bad_phrases if x in lower]
        if found_bad:
            score -= 8 * len(found_bad)
            variant.warnings.append("шаблонные travel-фразы: " + ", ".join(found_bad[:4]))

        ok, warnings = self.checker.check(variant)
        if not ok:
            score -= 7 * len(warnings)
            variant.warnings.extend(w for w in warnings if w not in variant.warnings)
        if re.search(r"\b(CTA|лид|визуал|подзаголовок|engagement|оффер)\b", full, re.I):
            score -= 25
            variant.warnings.append("служебные слова попали в пост")

        variant.score = max(0, min(100, score))
        if reasons:
            variant.why_it_works = "; ".join(reasons[:8])
        return variant

    def feedback_for_rewrite(self, variant: PostVariant) -> str:
        parts = [f"Текущая оценка: {variant.score}/100."]
        if variant.why_it_works:
            parts.append("Что уже работает: " + variant.why_it_works)
        if variant.warnings:
            parts.append("Что исправить: " + "; ".join(str(x) for x in variant.warnings[:10]))
        parts.append(
            "Нужно переписать пост так, чтобы он был красивым Telegram-постом: жирный заголовок, "
            "короткий лид, разделитель, 2–4 выделенных смысловых блока с эмодзи, конкретные советы, "
            "не сплошной текст, финал строго по теме."
        )
        return "\n".join(parts)

    def choose(self, variants: list[PostVariant], brief: Brief) -> tuple[PostVariant | None, list[PostVariant]]:
        scored = [self.score_variant(self.checker.sanitize(v), brief) for v in variants]
        scored.sort(key=lambda v: v.score, reverse=True)
        if not scored:
            return None, []
        best = scored[0]
        if best.score < self.min_score:
            best.warnings.append(f"качество ниже {self.min_score}, пост отклонён")
            return None, scored
        return best, scored
