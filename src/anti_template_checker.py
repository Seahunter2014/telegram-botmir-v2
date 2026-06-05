from __future__ import annotations
import re
from typing import Any
from .dedup_engine import is_duplicate_variant

# Важно: этот модуль не должен превращать /test в тупик.
# Он различает критические блокеры и редакционные замечания.
# Критические блокеры запрещают публикацию. Мягкие замечания снижают score и отправляют вариант на доработку/понижение.

HARD_TECH_PATTERNS = [
    'сигнал' + ' для',
    'editorial_seed',
    'snapshot_seed',
    'quality_seed',
    'source_rotation',
    'reason:',
    'genre:',
]

SOFT_GENERIC_PHRASES = [
    'давно хотели',
    'отличный момент',
    'рекомендуем',
    'заранее — тогда',
    'комфортной и оправдает ожидания',
    'не терять время на поиски',
    'такие предложения быстро меняются',
    'подходящий вариант',
]


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r'[.!?…]+', text) if s.strip()]


def check_variant(variant: dict, bundle: Any) -> dict:
    title = str(variant.get('title', '')).strip()
    body = str(variant.get('text', '')).strip()
    cta = str(variant.get('cta', '')).strip()
    full = f"{title}\n{body}\n{cta}".strip()
    low = full.lower()

    hard: list[str] = []
    soft: list[str] = []

    # Запрещённые фразы из ТЗ — критический блокер.
    for p in bundle.forbidden.get('phrases', []):
        if str(p).strip() and str(p).lower() in low:
            hard.append(f'Запрещённая фраза: {p}')

    for p in HARD_TECH_PATTERNS:
        if p in low:
            hard.append(f'Внутренняя техническая фраза: {p}')

    for p in SOFT_GENERIC_PHRASES:
        if p in low:
            soft.append(f'Общая рекламная фраза: {p}')

    paras = [p.strip() for p in body.split('\n') if p.strip()]
    sents = _sentences(body)

    # Для preview не блокируем текст только из-за длины: это была причина провала v3.1.
    # Но жёстко штрафуем, чтобы автоселектор предпочитал более сильный вариант.
    if len(paras) < 2:
        soft.append('Мало абзацев')
    if len(body) < 260:
        soft.append('Мало текста')
    if len(title) < 18:
        soft.append('Слабый заголовок')
    if len(sents) < 4:
        soft.append('Мало смысловых предложений')

    starts = []
    for p in paras:
        m = re.findall(r'[A-Za-zА-Яа-яЁё0-9]+', p.lower())
        starts.append(m[0] if m else '')
    if len(starts) >= 3 and len(set(starts)) < len(starts):
        soft.append('Повторяются начала абзацев')

    dup, reason = is_duplicate_variant(full)
    if dup:
        hard.append(reason)

    passed = not hard
    score = max(0, 100 - len(hard) * 40 - len(soft) * 8)
    return {
        'passed': passed,
        'hard_issues': hard,
        'soft_issues': soft,
        'issues': hard + soft,
        'quality_score': score,
    }
