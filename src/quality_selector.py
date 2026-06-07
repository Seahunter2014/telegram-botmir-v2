from __future__ import annotations

import json
from typing import Any

from .anti_template_checker import check_variant
from .fact_checker import fact_check_variant


def score_variant(variant: dict, plan: dict, bundle: Any) -> dict:
    anti = check_variant(variant, bundle)
    fact = fact_check_variant(variant, plan)
    score = int(variant.get("score") or 70)
    score -= len(anti["issues"]) * 12 + len(fact["warnings"]) * 5
    text = variant.get("text", "").lower()
    if len(text) > 600:
        score += 5
    if "?" in text:
        score += 3
    if any(word in text for word in ["сохран", "перей", "проверить", "выбрали", "открыть"]):
        score += 4
    return {"score": max(0, min(100, score)), "anti_template": anti, "fact_check": fact}


def _heuristic_best(variants: list[dict], plan: dict, bundle: Any) -> dict:
    scored: list[dict] = []
    for index, variant in enumerate(variants, 1):
        item = {**variant, "index": index, "quality": score_variant(variant, plan, bundle)}
        scored.append(item)
    return sorted(scored, key=lambda value: value["quality"]["score"], reverse=True)[0]


def _ai_best(variants: list[dict], plan: dict, bundle: Any) -> dict | None:
    try:
        from .ai_writer import client, model, temp
    except Exception:
        return None
    if "quality_selector_ru" not in bundle.prompts:
        return None

    payload = {
        "plan": plan,
        "variants": [
            {
                "index": index,
                "title": variant.get("title", ""),
                "text": variant.get("text", ""),
                "cta": variant.get("cta", ""),
                "style": variant.get("style", ""),
                "heuristic_score": score_variant(variant, plan, bundle)["score"],
            }
            for index, variant in enumerate(variants, 1)
        ],
    }
    prompt = "\n\n".join(
        [
            bundle.prompts["quality_selector_ru"],
            "Выбери лучший вариант и верни только JSON без markdown.",
            'Формат: {"best_index":1,"reason":"","scores":[{"index":1,"score":82},{"index":2,"score":77},{"index":3,"score":74}]}',
            json.dumps(payload, ensure_ascii=False, indent=2),
        ]
    )
    try:
        response = client().chat.completions.create(
            model=model(),
            temperature=min(temp(), 0.4),
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "Ты оцениваешь редакционные варианты и возвращаешь только валидный JSON."},
                {"role": "user", "content": prompt},
            ],
        )
        data = json.loads(response.choices[0].message.content or "{}")
        best_index = int(data.get("best_index", 0))
        if best_index < 1 or best_index > len(variants):
            return None
        selected = {**variants[best_index - 1], "index": best_index}
        selected["quality"] = score_variant(selected, plan, bundle)
        selected["quality"]["ai_reason"] = str(data.get("reason", "")).strip()
        selected["quality"]["ai_scores"] = data.get("scores", [])
        return selected
    except Exception:
        return None


def select_best_variant(variants: list[dict], plan: dict, bundle: Any) -> dict:
    return _ai_best(variants, plan, bundle) or _heuristic_best(variants, plan, bundle)
