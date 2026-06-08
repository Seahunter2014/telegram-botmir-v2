import json
from typing import Any

from .config_loader import read_prompt, read_json
from .json_repair import extract_json
from .models import EditorialBrief, GeneratedPost, PostVariant, Button
from .openai_client import OpenAIClient


class AIWriter:
    def __init__(self):
        self.client = OpenAIClient()
        self.system_prompt = "\n\n".join([
            read_prompt("system_editor_ru.md"),
            read_prompt("hook_engagement_engine_ru.md"),
            read_prompt("editorial_planner_ru.md"),
            read_prompt("writer_3_variants_ru.md"),
            read_prompt("anti_template_ru.md"),
            read_prompt("quality_selector_ru.md"),
            read_prompt("cta_rules_ru.md"),
            read_prompt("fact_check_ru.md"),
        ])
        self.forbidden = read_json("forbidden_phrases.json", [])

    def generate(self, brief: EditorialBrief, mode: str = "normal") -> GeneratedPost:
        user_payload = {
            "task": "Создай 3 готовых варианта Telegram-поста по MASTER-ТЗ. Не пересказывай источник. Верни только JSON.",
            "mode": mode,
            "strict_limits": {
                "max_total_caption_chars": 900,
                "max_body_chars": 760,
                "title_required": True,
                "telegram_format": True,
                "no_source_copy": True,
                "no_random_cta": True,
            },
            "brief": self._brief_dict(brief),
            "source_signal": {
                "source_name": brief.signal.source_name,
                "source_url": brief.signal.source_url,
                "title": brief.signal.title,
                "text": brief.signal.text,
                "url": brief.signal.url,
            },
            "allowed_services": brief.allowed_services,
            "forbidden_phrases": self.forbidden,
        }
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
        ]
        raw = self.client.complete_json(messages)
        data = extract_json(raw)
        return self._parse_generated(data, brief)

    def _brief_dict(self, brief: EditorialBrief) -> dict:
        return {
            "genre": brief.genre,
            "slot": brief.slot,
            "score": brief.score,
            "route_from": brief.route_from,
            "route_to": brief.route_to,
            "price": brief.price,
            "date_text": brief.date_text,
            "editorial_angle": brief.editorial_angle,
            "target_emotion": brief.target_emotion,
            "warnings": brief.warnings,
        }

    @staticmethod
    def _as_text(value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return value.strip()
        return str(value).strip()

    @staticmethod
    def _as_int(value: Any, default: int = 0) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    @classmethod
    def _as_list(cls, value: Any) -> list:
        """Normalize GPT output fields that must be lists.

        OpenAI can occasionally return warnings/buttons as a string or dict even when
        the schema asks for a list. Runtime code must never crash because of that.
        """
        if value is None or value == "":
            return []
        if isinstance(value, list):
            return value
        if isinstance(value, tuple):
            return list(value)
        if isinstance(value, dict):
            return [value]
        return [cls._as_text(value)]

    def _parse_buttons(self, raw_buttons: Any) -> list[Button]:
        buttons: list[Button] = []
        for item in self._as_list(raw_buttons):
            if isinstance(item, dict):
                text = self._as_text(item.get("text"))
                url = self._as_text(item.get("url"))
                service_key = self._as_text(item.get("service_key"))
                if text or url:
                    buttons.append(Button(text=text, url=url, service_key=service_key))
            elif isinstance(item, str) and item.strip():
                # Do not create a button without URL. Keep malformed GPT text out of Telegram buttons.
                continue
        return buttons

    def _parse_warnings(self, raw_warnings: Any) -> list[str]:
        return [self._as_text(x) for x in self._as_list(raw_warnings) if self._as_text(x)]

    def _parse_generated(self, data: dict, brief: EditorialBrief) -> GeneratedPost:
        if not isinstance(data, dict):
            data = {}

        raw_variants = self._as_list(data.get("variants", []))
        variants: list[PostVariant] = []

        for i, item in enumerate(raw_variants, start=1):
            if not isinstance(item, dict):
                continue
            variants.append(PostVariant(
                variant_id=self._as_int(item.get("variant_id"), i) or i,
                style=self._as_text(item.get("style")),
                title=self._as_text(item.get("title")),
                body=self._as_text(item.get("body")),
                cta_text=self._as_text(item.get("cta_text")),
                buttons=self._parse_buttons(item.get("buttons", [])),
                score=self._as_int(item.get("score"), 0),
                why_it_works=self._as_text(item.get("why_it_works")),
                warnings=self._parse_warnings(item.get("warnings", [])),
            ))

        return GeneratedPost(
            decision=self._as_text(data.get("decision", "publishable")) or "publishable",
            reject_reason=self._as_text(data.get("reject_reason", "")),
            genre=self._as_text(data.get("genre", brief.genre)) or brief.genre,
            slot=self._as_text(data.get("slot", brief.slot)) or brief.slot,
            editorial_angle=self._as_text(data.get("editorial_angle", brief.editorial_angle)) or brief.editorial_angle,
            target_emotion=self._as_text(data.get("target_emotion", brief.target_emotion)) or brief.target_emotion,
            media_query=self._as_text(data.get("media_query", "")),
            media_requirements=self._as_text(data.get("media_requirements", "")),
            variants=variants[:3],
            best_variant_id=self._as_int(data.get("best_variant_id"), 1) or 1,
        )
