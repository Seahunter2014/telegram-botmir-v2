from __future__ import annotations
from typing import Any
from .anti_template_checker import check_variant
from .fact_checker import fact_check_variant

BAD_GENERIC = [
    'давно хотели', 'отличный момент', 'рекомендуем', 'заранее — тогда',
    'комфортной и оправдает ожидания', 'не терять время на поиски',
    'такие предложения быстро меняются', 'подходящий вариант',
]


def score_variant(variant: dict, plan: dict, bundle: Any) -> dict:
    anti = check_variant(variant, bundle)
    fact = fact_check_variant(variant, plan)
    score = int(variant.get('score') or 70)
    score -= len(anti.get('hard_issues', [])) * 45
    score -= len(anti.get('soft_issues', [])) * 7
    score -= len(fact.get('warnings', [])) * 4
    full = (variant.get('title', '') + ' ' + variant.get('text', '') + ' ' + variant.get('cta', '')).lower()
    text = variant.get('text', '')
    paras = [p for p in text.split('\n') if p.strip()]

    if len(text) >= 450:
        score += 8
    if len(paras) >= 3:
        score += 8
    if '?' in full:
        score += 2
    if any(w in full for w in ['сохран', 'перешл', 'проверить', 'выбрали']):
        score += 3

    if plan.get('topic') == 'flight_deal':
        sig = plan.get('signal') or {}
        for key, bonus, penalty in [('price', 12, 15), ('route_to', 8, 12), ('route_from', 8, 12)]:
            val = str(sig.get(key, '')).lower().strip()
            if val and val in full:
                score += bonus
            elif val:
                score -= penalty
        if 'прям' in full and 'прям' in str(sig.get('text', '')).lower():
            score += 5

    for phrase in BAD_GENERIC:
        if phrase in full:
            score -= 18
    return {'score': max(0, min(100, score)), 'anti_template': anti, 'fact_check': fact}


def select_best_variant(variants: list[dict], plan: dict, bundle: Any) -> dict:
    scored = []
    for i, v in enumerate(variants, 1):
        q = v.get('quality') or score_variant(v, plan, bundle)
        v = {**v, 'index': i, 'quality': q}
        scored.append(v)
    # Критические нарушения в конец списка.
    return sorted(scored, key=lambda x: (not x['quality']['anti_template'].get('hard_issues'), x['quality']['score']), reverse=True)[0]
