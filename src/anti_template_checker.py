from __future__ import annotations

from .config_loader import CONFIG_DIR, load_json
from .models import PostVariant


class AntiTemplateChecker:
    def __init__(self):
        self.forbidden = load_json(CONFIG_DIR / "forbidden_phrases.json", default=[])

    def check(self, variant: PostVariant) -> tuple[bool, list[str]]:
        text = f"{variant.title}\n{variant.body}\n{variant.cta_text}"
        warnings = []
        for phrase in self.forbidden:
            if phrase and phrase.lower() in text.lower():
                warnings.append(f"запрещённая фраза: {phrase}")
        if len(variant.body) < 350:
            warnings.append("текст слишком короткий")
        if "\n\n" not in variant.body and len(variant.body) > 700:
            warnings.append("стена текста без абзацев")
        return not warnings, warnings

    def sanitize(self, variant: PostVariant) -> PostVariant:
        for phrase in self.forbidden:
            variant.title = variant.title.replace(phrase, "")
            variant.body = variant.body.replace(phrase, "")
            variant.cta_text = variant.cta_text.replace(phrase, "")
        return variant
