from __future__ import annotations

import re

from .anti_template_checker import AntiTemplateChecker
from .models import Brief, PostVariant


class QualitySelector:
    def __init__(self, min_score: int = 85):
        self.min_score = min_score
        self.checker = AntiTemplateChecker()

    def score_variant(self, variant: PostVariant, brief: Brief) -> PostVariant:
        score = int(variant.score or 0)
        title = variant.title.strip()
        body = variant.body.strip()
        if len(title) > 10:
            score += 3
        if any(ch.isdigit() for ch in title):
            score += 3
        if any(x in title for x in ["?", ":", "—"]):
            score += 2
        if len(body) >= 600:
            score += 5
        if "\n\n" in body:
            score += 4
        if any(x in body for x in ["──────✦──────", "✅", "📌", "💡"]):
            score += 3
        if variant.cta_text:
            score += 4
        if variant.hashtags:
            score += 2
        ok, warnings = self.checker.check(variant)
        if not ok:
            score -= 7 * len(warnings)
            variant.warnings.extend(w for w in warnings if w not in variant.warnings)
        if re.search(r"\b(CTA|лид|визуал|подзаголовок)\b", f"{title} {body}", re.I):
            score -= 20
        variant.score = max(0, min(100, score))
        return variant

    def choose(self, variants: list[PostVariant], brief: Brief) -> tuple[PostVariant | None, list[PostVariant]]:
        scored = [self.score_variant(self.checker.sanitize(v), brief) for v in variants]
        scored.sort(key=lambda v: v.score, reverse=True)
        if not scored:
            return None, []
        best = scored[0]
        if best.score < self.min_score:
            best.warnings.append(f"качество ниже {self.min_score}, но вариант выбран как лучший доступный")
        return best, scored
