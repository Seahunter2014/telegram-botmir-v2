from __future__ import annotations
import json
import os
from typing import Any
from openai import OpenAI
from .cta_engine import select_cta
from .anti_template_checker import check_variant
from .editorial_polisher import polish_variants


def client() -> OpenAI:
    key = os.getenv('OPENAI_API_KEY', '').strip()
    if not key:
        raise RuntimeError('OPENAI_API_KEY не задан. Генерация шаблонами запрещена.')
    return OpenAI(api_key=key)


def model() -> str:
    return os.getenv('OPENAI_MODEL', 'gpt-4.1-mini').strip() or 'gpt-4.1-mini'


def temp() -> float:
    try:
        return float(os.getenv('OPENAI_TEMPERATURE', '0.85'))
    except ValueError:
        return 0.85


def _facts_line(signal: dict) -> str:
    pieces = []
    if signal.get('route_from') and signal.get('route_to'):
        pieces.append(f"маршрут {signal.get('route_from')} — {signal.get('route_to')}")
    if signal.get('price'):
        pieces.append(f"цена {signal.get('price')}")
    if signal.get('depart_human'):
        pieces.append(f"дата {signal.get('depart_human')}")
    if signal.get('city'):
        pieces.append(f"город {signal.get('city')}")
    if signal.get('country'):
        pieces.append(f"страна {signal.get('country')}")
    return '; '.join(pieces) if pieces else signal.get('title', '')


def _genre_hard_rules(plan: dict, signal: dict) -> str:
    topic = plan.get('topic')
    facts = _facts_line(signal)
    if topic == 'flight_deal':
        return f'''ЖАНР: авиабилет / перелёт / цена как повод для поездки.
ФАКТЫ, КОТОРЫЕ НЕЛЬЗЯ ПОТЕРЯТЬ: {facts}
Обязательные требования:
- заголовок должен содержать маршрут и цену/дату, если они есть;
- первый абзац начинаетcя с факта, а не с общей фразы;
- текст должен объяснить, почему это полезно подписчику: цена, прямой рейс, короткий сценарий, что проверить;
- не делай вид, что место гарантировано: пиши «проверьте», «на момент сигнала», «перед покупкой»;
- не пиши советский инструктаж: «рекомендуем определиться», «можно позаботиться», «не терять время»;
- в тексте 3–5 коротких абзацев, 650–950 знаков;
- без подписи «С любовью…»;
- без англицизмов.'''
    if topic in {'destination_post', 'weekend_trip', 'city_break'}:
        return f'''ЖАНР: направление / короткая поездка.
ФАКТЫ: {facts}
Обязательные требования:
- минимум 2 конкретные детали места или сценария поездки;
- первый абзац без абстрактной философии;
- не продавать жёстко, если нет оффера;
- 3–5 коротких абзацев;
- финал вовлекает или мягко ведёт к проверке деталей.'''
    if topic in {'tour_offer', 'hot_tour', 'last_minute'}:
        return f'''ЖАНР: тур / оффер.
ФАКТЫ: {facts}
Обязательные требования:
- вынеси цену, даты, отель, условия, если они есть;
- CTA прямой, но без истерики;
- не скрывай, что детали надо проверить;
- 3–5 коротких абзацев.'''
    if topic in {'event_trip', 'concert_trip', 'weekend_activity', 'activities_post'}:
        return f'''ЖАНР: событие или активность как повод для поездки.
ФАКТЫ: {facts}
Обязательные требования:
- покажи связку «событие + поездка»;
- укажи, что заранее стоит проверить билеты, дорогу и проживание;
- 3–5 коротких абзацев.'''
    return f'''ЖАНР: {topic}.
ФАКТЫ: {facts}
Пиши конкретно, без воды, с опорой на сигнал. Если фактов мало — делай аккуратный короткий пост, а не пустую красоту.'''


def _hard_prompt(plan: dict, signal: dict, cta: dict, bundle: Any) -> str:
    return '\n\n'.join([
        bundle.prompts['system_editor_ru'],
        bundle.prompts['writer_3_variants_ru'],
        bundle.prompts['anti_template_ru'],
        _genre_hard_rules(plan, signal),
        'КРИТИЧЕСКИ ВАЖНО: источник — только инфоповод. Не копируй источник, но сохрани конкретные факты.',
        'КРИТИЧЕСКИ ВАЖНО: каждый вариант должен отличаться углом подачи, заголовком, первым абзацем и концовкой.',
        'ФОРМАТ КАЖДОГО ВАРИАНТА: title — одна строка с конкретикой; text — 3–4 коротких абзаца через \n\n, 650–950 знаков; cta — 1 короткая строка или пусто.',
        'ЗАПРЕЩЕНО: слабые общие заходы, канцелярит, школьный пересказ, рекламные пустые фразы, служебные слова, англицизмы без смысла. Нужны конкретика, живой ритм и Telegram-оформление.',
        'ДАННЫЕ СИГНАЛА:', json.dumps(signal, ensure_ascii=False, indent=2),
        'РЕДАКЦИОННЫЙ ПЛАН:', json.dumps(plan, ensure_ascii=False, indent=2),
        'CTA И КНОПКИ:', json.dumps(cta, ensure_ascii=False, indent=2),
        'Верни строго JSON без markdown: {"variants":[{"title":"","text":"","cta":"","style":"","score":80,"notes":[]}]} Ровно 3 варианта.'
    ])


def _call_json(prompt: str) -> dict:
    r = client().chat.completions.create(
        model=model(),
        temperature=temp(),
        response_format={'type': 'json_object'},
        messages=[
            {'role': 'system', 'content': 'Ты возвращаешь только валидный JSON на русском языке. Никакого markdown, никаких пояснений.'},
            {'role': 'user', 'content': prompt},
        ],
    )
    return json.loads(r.choices[0].message.content or '{}')


def _normalize_variants(data: dict, cta: dict) -> list[dict]:
    variants = data.get('variants', [])
    if not isinstance(variants, list):
        variants = []
    out = []
    for item in variants[:3]:
        if not isinstance(item, dict):
            continue
        out.append({
            'title': str(item.get('title', '')).strip(),
            'text': str(item.get('text', '')).strip(),
            'cta': str(item.get('cta', '')).strip(),
            'style': str(item.get('style', '')).strip(),
            'score': int(item.get('score', 70) or 70),
            'notes': item.get('notes', []),
            'buttons': cta.get('buttons', []),
        })
    return out


def _repair_prompt(variants: list[dict], plan: dict, signal: dict, cta: dict, bundle: Any) -> str:
    checks = [{'variant': i + 1, 'check': check_variant(v, bundle)} for i, v in enumerate(variants)]
    return '\n\n'.join([
        bundle.prompts['system_editor_ru'],
        bundle.prompts['anti_template_ru'],
        _genre_hard_rules(plan, signal),
        'Ниже варианты и замечания редактора. Перепиши ВСЕ 3 варианта заново так, чтобы они прошли проверку.',
        'Не сокращай текст до одной фразы. Дай 3–5 абзацев, конкретику из сигнала и разные углы подачи.',
        'ИСХОДНЫЙ СИГНАЛ:', json.dumps(signal, ensure_ascii=False, indent=2),
        'ПЛАН:', json.dumps(plan, ensure_ascii=False, indent=2),
        'ЗАМЕЧАНИЯ:', json.dumps(checks, ensure_ascii=False, indent=2),
        'Верни строго JSON без markdown: {"variants":[{"title":"","text":"","cta":"","style":"","score":80,"notes":[]}]} Ровно 3 варианта.'
    ])


def _has_hard_blocks(variants: list[dict], bundle: Any) -> bool:
    return any(check_variant(v, bundle).get('hard_issues') for v in variants)


def generate_variants(plan: dict, signal: dict, bundle: Any) -> list[dict]:
    cta = select_cta(plan, bundle)
    data = _call_json(_hard_prompt(plan, signal, cta, bundle))
    variants = _normalize_variants(data, cta)
    if len(variants) < 3:
        raise RuntimeError('OpenAI не вернул 3 варианта поста')

    # Если есть критические блокеры или все варианты слишком слабые, даём модели второй шанс.
    checks = [check_variant(v, bundle) for v in variants]
    all_soft_bad = all(len(c.get('soft_issues', [])) >= 2 for c in checks)
    if _has_hard_blocks(variants, bundle) or all_soft_bad:
        repaired = _normalize_variants(_call_json(_repair_prompt(variants, plan, signal, cta, bundle)), cta)
        if len(repaired) == 3:
            variants = repaired

    variants = polish_variants(variants, plan, signal, bundle, _call_json)
    for v in variants:
        v['buttons'] = cta.get('buttons', [])
    return variants[:3]


def rewrite_variant(variant: dict, plan: dict, signal: dict, bundle: Any, mode: str) -> dict:
    task = {
        'rewrite': 'Перепиши полностью: больше фактов, меньше воды, другой заголовок и другая концовка.',
        'softer': 'Сделай мягче и редакционнее, но не размывай конкретику.',
        'sales': 'Сделай продающе, но с конкретикой и без рекламного шума.',
    }.get(mode, 'Перепиши полностью.')
    cta = select_cta(plan, bundle)
    prompt = '\n\n'.join([
        bundle.prompts['system_editor_ru'],
        bundle.prompts['anti_template_ru'],
        _genre_hard_rules(plan, signal),
        task,
        json.dumps({'variant': variant, 'plan': plan, 'signal': signal, 'cta': cta}, ensure_ascii=False, indent=2),
        'Верни JSON: {"title":"","text":"","cta":"","style":"","score":80,"notes":[]}'
    ])
    r = client().chat.completions.create(
        model=model(),
        temperature=temp(),
        response_format={'type': 'json_object'},
        messages=[{'role': 'system', 'content': 'Только валидный JSON на русском.'}, {'role': 'user', 'content': prompt}],
    )
    data = json.loads(r.choices[0].message.content or '{}')
    data['buttons'] = cta.get('buttons', [])
    return data


def ensure_quality_or_raise(variants: list[dict], bundle: Any) -> None:
    # В v3.1 эта функция убивала /test из-за мягких замечаний «мало абзацев».
    # Теперь блокируем только реально запрещённое: старые фразы, техслужебку и дубли.
    hard = []
    for i, v in enumerate(variants, 1):
        check = check_variant(v, bundle)
        if check.get('hard_issues'):
            hard.append(f"Вариант {i}: {'; '.join(check['hard_issues'])}")
    if hard:
        raise RuntimeError('Критические нарушения в вариантах: ' + ' | '.join(hard))
