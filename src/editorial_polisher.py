from __future__ import annotations
import json
from typing import Any
from .anti_template_checker import check_variant

WEAK_PHRASES = [
    'уникальное событие', 'погрузиться в мир', 'удивит и взрослых', 'убедитесь',
    'не пропустите', 'самые яркие', 'может стать тем самым опытом',
    'сразу понятны билеты', 'проживание и дорога', 'подходящий вариант',
    'открытые двери', 'заряженное пространство', 'такие предложения быстро меняются',
    'поможет чувствовать ритм', 'стоит заняться бронированием',
]


def _facts(signal: dict) -> str:
    parts = []
    route = ' → '.join([x for x in [signal.get('route_from'), signal.get('route_to')] if x])
    if route:
        parts.append(f'маршрут: {route}')
    if signal.get('price'):
        parts.append(f"цена: {signal['price']}")
    if signal.get('depart_human'):
        parts.append(f"дата: {signal['depart_human']}")
    if signal.get('city'):
        parts.append(f"город: {signal['city']}")
    if signal.get('country'):
        parts.append(f"страна: {signal['country']}")
    if signal.get('title'):
        parts.append(f"инфоповод: {signal['title']}")
    return '; '.join(parts)


def _needs_polish(variant: dict, plan: dict, bundle: Any) -> bool:
    q = check_variant(variant, bundle)
    full = ' '.join([str(variant.get('title', '')), str(variant.get('text', '')), str(variant.get('cta', ''))]).lower()
    if q.get('hard_issues') or len(q.get('soft_issues', [])) >= 2:
        return True
    if any(p in full for p in WEAK_PHRASES):
        return True
    if len(str(variant.get('text', ''))) < 360:
        return True
    return False


def _fallback_variant(plan: dict, signal: dict, source: dict, index: int) -> dict:
    topic = plan.get('topic')
    city = signal.get('city') or signal.get('route_to') or ''
    route = ' → '.join([x for x in [signal.get('route_from'), signal.get('route_to')] if x])
    price = signal.get('price')
    date = signal.get('depart_human')

    if topic == 'flight_deal' and route:
        title = ' — '.join([route, ' '.join([x for x in [date, ('от ' + price if price else '')] if x])]).strip(' —')
        text = '\n\n'.join([
            f'В подборке появился конкретный перелёт: {route}' + (f' на {date}' if date else '') + (f' — {price}' if price else '') + '.',
            'Смысл такого билета простой: не строить сложный маршрут с пересадками, а быстро проверить дату, багаж и итоговую стоимость.',
            'Перед покупкой лучше открыть предложение и сверить детали: время вылета, ручную кладь, правила тарифа и актуальную цену.',
            'Если направление и дата совпадают с вашими планами, тянуть не стоит: дешёвые места обычно исчезают первыми.'
        ])
        return {'title': title, 'text': text, 'cta': '', 'style': 'редакционный оффер', 'score': 82, 'notes': ['fallback_editorial']}

    if topic in {'event_trip', 'concert_trip', 'weekend_activity', 'activities_post'}:
        event = signal.get('title') or 'событие'
        title = f'{city + ": " if city else ""}{event[:80]}'
        text = '\n\n'.join([
            f'{event} — хороший повод смотреть на поездку не как на обычный выезд, а как на маленький маршрут вокруг события.',
            (f'Если выбирать {city}, сначала стоит проверить даты события, затем билеты в город и проживание рядом с удобной точкой маршрута.' if city else 'Сначала стоит проверить дату события, затем дорогу и проживание рядом с удобной точкой маршрута.'),
            'Такой формат особенно хорош для короткой поездки: днём город, вечером событие, без ощущения, что всё собрано на бегу.',
            'Сохраните идею, если любите поездки, у которых есть конкретный повод.'
        ])
        return {'title': title, 'text': text, 'cta': '', 'style': 'событие как маршрут', 'score': 80, 'notes': ['fallback_editorial']}

    title = signal.get('title') or plan.get('main_fact') or 'Идея для поездки'
    text = '\n\n'.join([
        f'{title} — повод присмотреться к направлению внимательнее.',
        'В хороших travel-идеях важна не только красивая картинка, а понятный сценарий: когда ехать, что проверить заранее и зачем сохранять эту точку в планах.',
        'Перед бронированием лучше сверить даты, дорогу и проживание, а уже потом собирать маршрут под свой ритм.',
        'Сохраните, если хочется держать под рукой не случайные новости, а идеи, из которых реально рождаются поездки.'
    ])
    return {'title': title[:95], 'text': text, 'cta': '', 'style': 'редакционный', 'score': 76, 'notes': ['fallback_editorial']}


def polish_variants(variants: list[dict], plan: dict, signal: dict, bundle: Any, call_json) -> list[dict]:
    """Финальный редакционный слой.

    Его задача не дать в публикацию школьный пересказ, даже если первая генерация была слабой.
    На входе 3 варианта, на выходе 3 оформленных Telegram-поста.
    """
    need = any(_needs_polish(v, plan, bundle) for v in variants)
    if not need:
        return variants

    prompt = '\n\n'.join([
        'Ты главный редактор Telegram travel-канала. Нужно переписать варианты так, чтобы их не было стыдно публиковать в канале.',
        'Пиши на русском. Источник — только инфоповод. Не делай пересказ. Не делай рекламную канцелярщину.',
        'Формат каждого варианта: сильный заголовок, 3–4 коротких абзаца, 1–2 уместных эмодзи в тексте максимум, живая концовка. Общая длина варианта 650–950 знаков.',
        'В заголовке должна быть конкретика: город, маршрут, цена, событие или причина поездки. Если факта нет — не выдумывай.',
        'Запрещены общие фразы: уникальное событие, погрузиться в мир, не пропустите, рекомендуем, отличный момент, подходящий вариант, комфорт оправдает ожидания.',
        'Для авиабилета обязательно: маршрут, цена/дата, что проверить перед покупкой. Для события: событие + город + зачем ехать + что проверить.',
        'Не добавляй служебные слова, не используй Markdown, не используй HTML. Верни JSON.',
        'ФАКТЫ СИГНАЛА: ' + _facts(signal),
        'ПЛАН: ' + json.dumps({k: plan.get(k) for k in ['topic', 'genre', 'slot_ru', 'hook_angle', 'practical_value', 'cta_level']}, ensure_ascii=False),
        'СТАРЫЕ ВАРИАНТЫ: ' + json.dumps(variants, ensure_ascii=False),
        'Верни строго JSON: {"variants":[{"title":"","text":"","cta":"","style":"","score":85,"notes":[]}]} Ровно 3 варианта.'
    ])
    try:
        data = call_json(prompt)
        fixed = data.get('variants', []) if isinstance(data, dict) else []
        out = []
        for item in fixed[:3]:
            if not isinstance(item, dict):
                continue
            out.append({
                'title': str(item.get('title', '')).strip(),
                'text': str(item.get('text', '')).strip(),
                'cta': str(item.get('cta', '')).strip(),
                'style': str(item.get('style', 'редакционный')).strip(),
                'score': int(item.get('score', 82) or 82),
                'notes': item.get('notes', []),
            })
        if len(out) == 3:
            return out
    except Exception:
        pass
    return [_fallback_variant(plan, signal, {}, i) for i in range(3)]
