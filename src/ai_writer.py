from __future__ import annotations

import json
from typing import Any

from .config_loader import PROMPTS_DIR, load_text
from .models import Brief, PostVariant
from .state_store import StateStore
from .openai_client import OpenAIClient

MASTER_PROMPT_FILE = "prompts/master_writer_ru.md"


def _as_list(value: Any) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, str):
        return [value] if value.strip() else []
    return [value]


class AIWriter:
    def __init__(self, client: OpenAIClient | None = None, local_fallback: bool = False):
        self.client = client
        # В продакшене локальный генератор запрещён: без OpenAI бот не должен писать посты.
        self.local_fallback = False
        self.system_prompt = (
            "Ты — главный редактор travel Telegram-канала «Мир на ладони». "
            "Строго следуй master prompt. Верни только валидный JSON."
        )
        self.master_prompt = load_text(PROMPTS_DIR / "master_writer_ru.md")
        self.prompt_file = MASTER_PROMPT_FILE
        self.state = StateStore()

    async def generate(self, brief: Brief) -> tuple[list[PostVariant], int, list[str]]:
        warnings: list[str] = []
        if not self.client:
            return [], 0, ["OpenAI не настроен. Нужен OPENAI_API_KEY и доступная модель. Локальный генератор отключён."]
        prompt = self._build_prompt(brief)
        data = await self.client.generate_json(self.system_prompt, prompt)
        variant = self._parse_response(data)
        if variant:
            return [variant], variant.variant_id, warnings
        err = getattr(self.client, "last_error", "нет данных об ошибке")
        warnings.append(f"OpenAI не вернул валидный пост: {err}. Локальный генератор отключён.")
        return [], 0, warnings

    async def improve(self, brief: Brief, previous: PostVariant, feedback: str, attempt: int) -> tuple[list[PostVariant], int, list[str]]:
        warnings: list[str] = []
        if not self.client:
            return [], 0, ["OpenAI не настроен. Улучшение поста невозможно."]
        prompt = self._build_prompt(brief) + (
            "\n\nРЕЖИМ УЛУЧШЕНИЯ. Предыдущий вариант не прошёл Quality Gate. "
            "Не меняй тему. Перепиши пост полностью, сильнее и конкретнее. "
            "Сохрани факты из BRIEF, но исправь структуру, оформление, ритм, пользу и финал.\n"
            f"Попытка улучшения: {attempt}.\n"
            f"Оценка и замечания Quality Gate:\n{feedback}\n\n"
            "ПРЕДЫДУЩИЙ СЛАБЫЙ ВАРИАНТ:\n"
            + json.dumps(previous.to_dict(), ensure_ascii=False, indent=2)
        )
        data = await self.client.generate_json(self.system_prompt, prompt)
        variant = self._parse_response(data)
        if variant:
            variant.warnings.append(f"переписано после Quality Gate, попытка {attempt}")
            return [variant], variant.variant_id, warnings
        err = getattr(self.client, "last_error", "нет данных об ошибке")
        warnings.append(f"OpenAI не вернул валидное улучшение: {err}")
        return [], 0, warnings

    def _build_prompt(self, brief: Brief) -> str:
        ratings = self.state.ratings_memory_text()
        return (
            self.master_prompt
            + "\n\nПАМЯТЬ ОЦЕНОК АДМИНИСТРАТОРА:\n"
            + ratings
            + "\n\nBRIEF ДЛЯ ТЕКУЩЕГО ПОСТА:\n"
            + json.dumps(brief.to_dict(), ensure_ascii=False, indent=2)
        )

    def _parse_response(self, data: dict[str, Any] | None) -> PostVariant | None:
        if not isinstance(data, dict):
            return None
        if str(data.get("decision", "")).lower() == "reject":
            return None

        # Основной формат v6.4 — один лучший пост в корне JSON.
        if any(k in data for k in ["title", "body", "cta_text"]):
            raw = {
                "variant_id": 1,
                "style": str(data.get("generator_note") or "лучший редакционный пост"),
                # Оценку модели не принимаем. QualitySelector считает качество сам.
                "score": 0,
                "title": str(data.get("title", "")),
                "body": str(data.get("body", "")),
                "cta_text": str(data.get("cta_text", "")),
                "buttons": [],
                "hashtags": _as_list(data.get("hashtags")),
                "why_it_works": str(data.get("generator_note", "")),
                "warnings": _as_list(data.get("warnings")),
            }
            try:
                variant = PostVariant.from_dict(raw)
                if variant.title.strip() and variant.body.strip():
                    return variant
            except Exception:
                return None

        # Защитная совместимость: если модель вернула старый variants-массив, берём только первый.
        variants_raw = data.get("variants") or []
        for idx, raw in enumerate(_as_list(variants_raw), 1):
            if not isinstance(raw, dict):
                continue
            raw.setdefault("variant_id", idx)
            raw["score"] = 0
            raw["warnings"] = _as_list(raw.get("warnings"))
            raw["buttons"] = [x for x in _as_list(raw.get("buttons")) if isinstance(x, dict)]
            try:
                variant = PostVariant.from_dict(raw)
                if variant.title.strip() and variant.body.strip():
                    return variant
            except Exception:
                continue
        return None
