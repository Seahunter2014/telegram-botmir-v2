import json
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
            read_prompt("writer_3_variants_ru.md"),
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
                "no_random_cta": True
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
            {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)}
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

    def _parse_generated(self, data: dict, brief: EditorialBrief) -> GeneratedPost:
        variants = []
        for i, item in enumerate(data.get("variants", []), start=1):
            buttons = [Button(text=b.get("text", ""), url=b.get("url", ""), service_key=b.get("service_key", "")) for b in item.get("buttons", [])]
            variants.append(PostVariant(
                variant_id=int(item.get("variant_id") or i),
                style=item.get("style", ""),
                title=item.get("title", "").strip(),
                body=item.get("body", "").strip(),
                cta_text=item.get("cta_text", "").strip(),
                buttons=buttons,
                score=int(item.get("score") or 0),
                why_it_works=item.get("why_it_works", ""),
                warnings=item.get("warnings", []) or []
            ))
        return GeneratedPost(
            decision=data.get("decision", "publishable"),
            reject_reason=data.get("reject_reason", ""),
            genre=data.get("genre", brief.genre),
            slot=data.get("slot", brief.slot),
            editorial_angle=data.get("editorial_angle", brief.editorial_angle),
            target_emotion=data.get("target_emotion", brief.target_emotion),
            media_query=data.get("media_query", ""),
            media_requirements=data.get("media_requirements", ""),
            variants=variants[:3],
            best_variant_id=int(data.get("best_variant_id") or 1),
        )
