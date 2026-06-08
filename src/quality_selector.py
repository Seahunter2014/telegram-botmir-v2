from .anti_template_checker import AntiTemplateChecker
from .config_loader import read_json
from .models import GeneratedPost, PostVariant


def _normalize_warnings(value) -> list[str]:
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return [str(x) for x in value if str(x).strip()]
    if isinstance(value, tuple):
        return [str(x) for x in value if str(x).strip()]
    return [str(value)]


class QualitySelector:
    def __init__(self):
        self.checker = AntiTemplateChecker()
        self.policy = read_json("editorial_policy.json", {})

    def score_variant(self, variant: PostVariant) -> tuple[int, list[str]]:
        score = int(variant.score or 0)
        notes: list[str] = []
        ok, errors = self.checker.check(variant.title, variant.body, variant.cta_text)
        if not ok:
            notes.extend(errors)
            score -= 25
        if any(ch.isdigit() for ch in variant.title):
            score += 5
        if any(e in variant.title for e in ["✈️", "🏖️", "🌆", "💰", "🗺️", "🍽️", "⛰️", "🎟️", "🧳", "🛡️"]):
            score += 3
        if len(variant.body) > 260:
            score += 8
        body_lower = variant.body.lower()
        if "?" in variant.body or "сохран" in body_lower or "перешл" in body_lower:
            score += 7
        return max(0, min(100, score)), notes

    def select_best(self, post: GeneratedPost) -> tuple[PostVariant | None, list[str]]:
        if not post.variants:
            return None, [post.reject_reason or "GPT не вернул варианты"]
        best = None
        best_score = -1
        all_notes: list[str] = []
        for variant in post.variants:
            s, notes = self.score_variant(variant)
            variant.score = s
            variant.warnings = _normalize_warnings(variant.warnings)
            for note in notes:
                if note not in variant.warnings:
                    variant.warnings.append(note)
            if notes:
                all_notes.extend([f"Вариант {variant.variant_id}: {n}" for n in notes])
            if s > best_score:
                best = variant
                best_score = s
        if best and best.score < int(self.policy.get("quality_min_publication_score", 85)):
            all_notes.append(
                f"Лучший вариант набрал только {best.score}/100, а для публикации нужно минимум {int(self.policy.get('quality_min_publication_score', 85))}/100."
            )
        return best, all_notes
