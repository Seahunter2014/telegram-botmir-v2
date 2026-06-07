from __future__ import annotations

import json
import os
from typing import Any

from openai import OpenAI

from .anti_template_checker import check_variant
from .cta_engine import select_cta


def client() -> OpenAI:
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key:
        raise RuntimeError("OPENAI_API_KEY не задан. Шаблонный fallback запрещён.")
    return OpenAI(api_key=key)


def model() -> str:
    return os.getenv("OPENAI_MODEL", "gpt-4.1-mini").strip() or "gpt-4.1-mini"


def temp() -> float:
    raw = os.getenv("AI_EDITOR_TEMPERATURE", "").strip() or os.getenv("OPENAI_TEMPERATURE", "0.85").strip()
    try:
        return float(raw)
    except ValueError:
        return 0.85


def _editor_enabled() -> bool:
    raw = os.getenv("AI_EDITOR_ENABLED", "true").strip().lower()
    return raw not in {"0", "false", "off", "no"}


def generate_variants(plan: dict, signal: dict, bundle: Any) -> list[dict]:
    if not _editor_enabled():
        raise RuntimeError("AI_EDITOR_ENABLED выключен. Генерация остановлена.")

    cta = select_cta(plan, bundle)
    direct_offer_note = (
        "В финальном посте система сама добавит строку с прямой ссылкой на конкретный оффер, если источник содержит прямой оффер. "
        "Твоя задача — не терять фактуру и не писать общий текст без повода."
    )
    prompt = "\n\n".join(
        [
            bundle.prompts["system_editor_ru"],
            bundle.prompts["editorial_planner_ru"],
            bundle.prompts["writer_3_variants_ru"],
            bundle.prompts["anti_template_ru"],
            direct_offer_note,
            "ДАННЫЕ СИГНАЛА:",
            json.dumps(signal, ensure_ascii=False, indent=2),
            "РЕДАКЦИОННЫЙ ПЛАН:",
            json.dumps(plan, ensure_ascii=False, indent=2),
            "CTA:",
            json.dumps(cta, ensure_ascii=False, indent=2),
            (
                'Верни строго JSON без markdown: '
                '{"variants":[{"title":"","text":"","cta":"","style":"","score":80,"notes":[]}]} '
                "Ровно 3 варианта. Каждый вариант должен быть законченным, живым и отличаться по подаче."
            ),
        ]
    )
    response = client().chat.completions.create(
        model=model(),
        temperature=temp(),
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": "Ты возвращаешь только валидный JSON на русском языке."},
            {"role": "user", "content": prompt},
        ],
    )
    data = json.loads(response.choices[0].message.content or "{}")
    variants = data.get("variants", [])
    if not isinstance(variants, list) or len(variants) < 3:
        raise RuntimeError("OpenAI не вернул 3 варианта поста")

    out: list[dict] = []
    for item in variants[:3]:
        out.append(
            {
                "title": str(item.get("title", "")).strip(),
                "text": str(item.get("text", "")).strip(),
                "cta": str(item.get("cta", "")).strip(),
                "style": str(item.get("style", "")).strip(),
                "score": int(item.get("score", 70) or 70),
                "notes": item.get("notes", []),
                "buttons": cta.get("buttons", []),
            }
        )
    return out


def rewrite_variant(variant: dict, plan: dict, signal: dict, bundle: Any, mode: str) -> dict:
    task = {
        "rewrite": "Перепиши полностью, сохрани смысл и усили текст.",
        "softer": "Сделай мягче, редакционнее и благороднее по тону.",
        "sales": "Сделай сильнее по вовлечению и CTR, но без рекламного шума.",
    }.get(mode, "Перепиши полностью.")
    cta = select_cta(plan, bundle)
    prompt = "\n\n".join(
        [
            bundle.prompts["system_editor_ru"],
            bundle.prompts["anti_template_ru"],
            task,
            json.dumps({"variant": variant, "plan": plan, "signal": signal, "cta": cta}, ensure_ascii=False, indent=2),
            'Верни JSON: {"title":"","text":"","cta":"","style":"","score":80,"notes":[]}',
        ]
    )
    response = client().chat.completions.create(
        model=model(),
        temperature=temp(),
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": "Только валидный JSON на русском."},
            {"role": "user", "content": prompt},
        ],
    )
    data = json.loads(response.choices[0].message.content or "{}")
    data["buttons"] = cta.get("buttons", [])
    return data


def ensure_quality_or_raise(variants: list[dict], bundle: Any) -> None:
    bad: list[str] = []
    for index, variant in enumerate(variants, 1):
        check = check_variant(variant, bundle)
        if not check["passed"]:
            bad.append(f"Вариант {index}: {'; '.join(check['issues'])}")
    if len(bad) == len(variants):
        raise RuntimeError("Все варианты забракованы: " + " | ".join(bad))
