from .anti_template_checker import AntiTemplateChecker
from .models import GeneratedPost, PostVariant

class QualitySelector:
    def __init__(self):
        self.checker = AntiTemplateChecker()

    def score_variant(self, variant: PostVariant) -> tuple[int, list[str]]:
        score = int(variant.score or 0)
        notes = []
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
        if "?" in variant.body or "сохран" in variant.body.lower() or "перешл" in variant.body.lower():
            score += 7
        return max(0, min(100, score)), notes

    def select_best(self, post: GeneratedPost) -> tuple[PostVariant | None, list[str]]:
        if not post.variants:
            return None, [post.reject_reason or "GPT не вернул варианты"]
        best = None
        best_score = -1
        all_notes = []
        for variant in post.variants:
            s, notes = self.score_variant(variant)
            variant.score = s
            variant.warnings.extend(notes)
            if notes:
                all_notes.extend([f"Вариант {variant.variant_id}: {n}" for n in notes])
            if s > best_score:
                best = variant
                best_score = s
        return best, all_notes
