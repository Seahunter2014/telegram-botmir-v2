from __future__ import annotations
from typing import Any
from urllib.parse import urlencode
import os
from .config_loader import link_rule_for_topic


def _by_category(bundle: Any, category: str, topic: str) -> list[dict]:
    out = []
    for s in bundle.services['services']:
        if s.get('status') != 'active' or s.get('category') != category:
            continue
        if topic in s.get('usage_rules', []) or not s.get('usage_rules'):
            out.append(s)
    return sorted(out, key=lambda x: x.get('priority', 0), reverse=True)


def _aviasales_search_url(plan: dict) -> str:
    sig = plan.get('signal') or {}
    origin = sig.get('origin_iata')
    dest = sig.get('destination_iata')
    marker = os.getenv('TRAVELPAYOUTS_MARKER') or os.getenv('AVIASALES_MARKER') or '98526'
    if not (origin and dest):
        return ''
    dd = sig.get('depart_day')
    mm = sig.get('depart_month')
    route = f'{origin}{dd}{mm}{dest}' if dd and mm else f'{origin}{dest}'
    return 'https://www.aviasales.ru/search/' + route + '?' + urlencode({'marker': marker})


def _button_text(category: str, service: dict, topic: str, sig: dict) -> str:
    frm = sig.get('route_from', '')
    to = sig.get('route_to', '')
    city = sig.get('city') or to
    if category == 'flights':
        if frm and to:
            return f'✈️ Проверить {frm} → {to}'
        if city:
            return f'✈️ Билеты в {city}'
        return '✈️ Найти билеты'
    if category == 'hotels':
        return f'🏨 Отели {city}' if city else '🏨 Подобрать отель'
    if category == 'tours':
        return '🔥 Посмотреть туры'
    if category == 'events':
        return '🎟 Билеты на событие'
    if category == 'excursions':
        return '🗺 Экскурсии и активности'
    if category == 'insurance':
        return '🛡 Страховка'
    if category == 'foreign_cards':
        return '💳 Карта для поездки'
    if category == 'transfer':
        return '🚕 Трансфер'
    if category == 'car_rental':
        return '🚗 Аренда авто'
    return service.get('button_text') or service['name']


def _source_button_text(topic: str) -> str:
    if topic == 'flight_deal':
        return '🔎 Открыть источник'
    if topic in {'event_trip', 'concert_trip', 'weekend_activity', 'activities_post'}:
        return '🎟 Открыть событие'
    if topic in {'tour_offer', 'hot_tour', 'last_minute'}:
        return '🔥 Открыть предложение'
    return '🔎 Открыть источник'


def select_cta(plan: dict, bundle: Any) -> dict:
    topic = plan['topic']
    rule = link_rule_for_topic(bundle, topic)
    cats = rule.get('links', []) if rule else plan.get('allowed_categories', [])
    max_links = rule.get('max_links', plan.get('max_links', 2)) if rule else plan.get('max_links', 2)
    fmt = rule.get('preferred_format', 'text') if rule else 'text'
    if max_links <= 0 or fmt == 'no_partner_link':
        return {'text_cta': '', 'buttons': [], 'format': 'no_partner_link', 'reason': 'Жанр без партнёрских ссылок'}

    buttons: list[dict] = []
    sig = plan.get('signal') or {}

    # У событий и офферов первая кнопка должна вести к фактическому источнику, иначе пост выглядит как общая реклама.
    if topic in {'flight_deal', 'tour_offer', 'last_minute', 'hot_tour', 'event_trip', 'concert_trip', 'weekend_activity', 'activities_post'} and sig.get('url'):
        buttons.append({'text': _source_button_text(topic), 'url': sig['url'], 'service_key': 'source_offer', 'category': 'source'})

    for cat in cats:
        cand = _by_category(bundle, cat, topic)
        if not cand:
            cand = [s for s in bundle.services['services'] if s.get('status') == 'active' and s.get('category') == cat]
        if not cand:
            continue
        s = cand[0]
        url = s['ref_url']
        if cat == 'flights':
            deep = _aviasales_search_url(plan)
            if deep:
                url = deep
        text = _button_text(cat, s, topic, sig)
        if all(b.get('url') != url for b in buttons):
            buttons.append({'text': text, 'url': url, 'service_key': s['key'], 'category': s['category']})
        if len(buttons) >= max_links:
            break

    return {
        'text_cta': _text(topic, fmt, buttons, plan),
        'buttons': buttons[:max_links],
        'format': fmt,
        'reason': 'Ссылки выбраны по жанру, источнику и реферальной матрице',
    }


def _text(topic: str, fmt: str, buttons: list[dict], plan: dict) -> str:
    if not buttons:
        return ''
    sig = plan.get('signal') or {}
    price = sig.get('price', '')
    route = ' → '.join([x for x in [sig.get('route_from'), sig.get('route_to')] if x])
    date = sig.get('depart_human', '')
    if fmt == 'soft_cta':
        return 'Сохраните пост: такие детали лучше проверить до покупки билетов и бронирований.'
    if topic == 'flight_deal':
        tail = ' · '.join([x for x in [route, date, ('от ' + price if price else '')] if x])
        return 'Проверяйте дату, багаж и итоговую стоимость перед оплатой' + (f': {tail}.' if tail else '.')
    if topic in {'event_trip', 'concert_trip', 'weekend_activity', 'activities_post'}:
        return 'Если идея откликается, сначала проверьте событие, потом — билеты и проживание на нужные даты.'
    if topic in {'tour_offer', 'hot_tour', 'last_minute'}:
        return 'Перед бронированием проверьте состав тура, даты, багаж и итоговую стоимость.'
    return 'Сохраните идею и проверьте детали по кнопкам ниже.'
