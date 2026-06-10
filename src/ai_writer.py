from __future__ import annotations

import json
from typing import Any

from .config_loader import PROMPTS_DIR, load_text
from .models import Brief, Button, PostVariant
from .openai_client import OpenAIClient


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
        # Локальный генератор намеренно отключён: без OpenAI бот не должен публиковать шаблонные посты.
        self.local_fallback = False
        self.system_prompt = "Ты — главный редактор travel Telegram-канала «Мир на ладони». Строго следуй master prompt и возвращай только валидный JSON."
        self.master_prompt = load_text(PROMPTS_DIR / "master_writer_ru.md")

    async def generate(self, brief: Brief) -> tuple[list[PostVariant], int, list[str]]:
        warnings: list[str] = []
        if not self.client:
            return [], 0, ["OpenAI не настроен. Нужен OPENAI_API_KEY и доступная модель. Локальный генератор отключён."]
        prompt = self._build_prompt(brief)
        data = await self.client.generate_json(self.system_prompt, prompt)
        variants = self._parse_response(data)
        if variants:
            best = int((data or {}).get("best_variant_id") or variants[0].variant_id)
            return variants, best, warnings
        err = getattr(self.client, "last_error", "нет данных об ошибке")
        warnings.append(f"OpenAI не вернул валидный пост: {err}. Локальный генератор отключён.")
        return [], 0, warnings

    def _build_prompt(self, brief: Brief) -> str:
        return self.master_prompt + "\n\nBRIEF ДЛЯ ТЕКУЩЕГО ПОСТА:\n" + json.dumps(brief.to_dict(), ensure_ascii=False, indent=2)

    def _parse_response(self, data: dict[str, Any] | None) -> list[PostVariant]:
        if not isinstance(data, dict):
            return []
        if data.get("decision") == "reject":
            return []
        variants_raw = data.get("variants") or []
        variants: list[PostVariant] = []
        for idx, raw in enumerate(_as_list(variants_raw), 1):
            if not isinstance(raw, dict):
                continue
            raw.setdefault("variant_id", idx)
            raw["warnings"] = _as_list(raw.get("warnings"))
            raw["buttons"] = [x for x in _as_list(raw.get("buttons")) if isinstance(x, dict)]
            try:
                variants.append(PostVariant.from_dict(raw))
            except Exception:
                continue
        return variants[:1]

    def _local_generate(self, brief: Brief) -> list[PostVariant]:
        title_base = self._title(brief)
        hashtags = ["#мирналадони", "#турджин", "#Туры", "#путешествиязаграницу", "#travel"]
        variants = [
            PostVariant(1, "вдохновляющий", 88, title_base, self._body_inspiration(brief), self._cta(brief, "soft"), hashtags=hashtags, why_it_works="эмоция + конкретика + сохранение"),
            PostVariant(2, "практичный", 90, title_base.replace("✨", "🧭"), self._body_practical(brief), self._cta(brief, "save"), hashtags=hashtags, why_it_works="структура + польза + понятный следующий шаг"),
            PostVariant(3, "вовлекающий", 87, title_base.replace("✨", "💬"), self._body_engage(brief), self._cta(brief, "engage"), hashtags=hashtags, why_it_works="вопрос + повод переслать"),
        ]
        if brief.genre in {"flight_deal", "tour_offer", "hotel_post"}:
            variants[2].style = "продающий"
            variants[2].body = self._body_offer(brief)
            variants[2].cta_text = self._cta(brief, "direct")
            variants[2].score = 91
        return variants

    def _title(self, brief: Brief) -> str:
        place = brief.city or brief.country or brief.topic.split("—")[0].strip()
        if brief.genre == "flight_deal":
            return f"✈️ {place}: повод проверить билеты без лишней суеты"
        if brief.genre == "tour_offer":
            return f"🌴 {place}: готовая идея для отпуска"
        if brief.genre == "practical_travel":
            return f"🧳 {brief.topic[:70]}"
        if brief.genre == "top_list":
            return f"🗺 {brief.topic[:80]}"
        return f"✨ {place}: travel-идея, которую стоит сохранить"

    def _lead(self, brief: Brief) -> str:
        place = brief.city or brief.country or "это направление"
        if brief.price:
            return f"В источнике появился повод присмотреться к поездке: {place}, цена {brief.price}. Разбираем не как объявление, а как идею, которую стоит проверить под свои даты."
        return f"{place.capitalize()} может стать не просто точкой на карте, а готовой идеей для следующей поездки. Главное — понять, зачем ехать, когда удобнее и что проверить заранее."

    def _body_inspiration(self, brief: Brief) -> str:
        return f"{self._lead(brief)}\n\n──────✦──────\n\n📌 **Почему это цепляет**\n{brief.editorial_angle}. Здесь важны не громкие обещания, а понятная travel-ценность: красивый визуал, маршрутная идея и повод сохранить пост.\n\n💡 **Что проверить**\n✅ сезон и погоду;\n✅ удобные рейсы или стыковки;\n✅ район проживания;\n✅ правила въезда и оплату на месте."

    def _body_practical(self, brief: Brief) -> str:
        return f"{self._lead(brief)}\n\n──────✦──────\n\n💡 **Короткий план**\n1. Сначала проверьте даты и сезон.\n2. Затем сравните перелёт, проживание и транспорт.\n3. После этого смотрите экскурсии, страховку и запас по бюджету.\n\n⚠️ **Важно**\nЦены, правила въезда и условия тарифов лучше перепроверять перед покупкой: в travel всё меняется быстрее, чем кажется."

    def _body_engage(self, brief: Brief) -> str:
        return f"{self._lead(brief)}\n\n──────✦──────\n\n📌 **Кому подойдёт**\n— тем, кто любит готовые идеи без долгого поиска;\n— тем, кто собирает маршруты в закладки;\n— тем, кто выбирает поездку по настроению, сезону и бюджету.\n\n💬 А вы бы выбрали такой формат поездки или поискали что-то спокойнее?"

    def _body_offer(self, brief: Brief) -> str:
        parts = [self._lead(brief), "──────✦──────", "📌 **Что важно перед покупкой**"]
        if brief.price:
            parts.append(f"💰 Цена: {brief.price}")
        if brief.dates:
            parts.append(f"🗓️ Даты/период: {brief.dates}")
        parts += ["🧳 Проверьте багаж, аэропорт, пересадки и условия возврата.", "⚠️ Такие предложения лучше смотреть сразу: цена и наличие мест могут измениться."]
        return "\n\n".join(parts)

    def _cta(self, brief: Brief, mode: str) -> str:
        if mode == "direct" or brief.genre in {"flight_deal", "tour_offer", "hotel_post"}:
            return "Проверьте актуальные условия и сравните варианты под свои даты."
        if mode == "save":
            return "Сохраните пост — пригодится, когда будете собирать следующую поездку."
        return "Отправьте тому, с кем давно обсуждаете новую поездку."
