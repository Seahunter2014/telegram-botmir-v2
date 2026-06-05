from __future__ import annotations
import os, requests
from pathlib import Path
from urllib.parse import urlencode
from PIL import Image, ImageDraw, ImageFont
from .config_loader import ROOT_DIR

CITY_IMAGE_QUERY = {
    'Москва': 'Moscow Red Square Kremlin city skyline',
    'Пермь': 'Perm Russia city panorama Kama river',
    'Сочи': 'Sochi Russia sea mountains city',
    'Санкт-Петербург': 'Saint Petersburg Russia Hermitage Neva',
    'Стамбул': 'Istanbul Bosphorus skyline Hagia Sophia',
    'Анталья': 'Antalya Turkey old town sea',
    'Ереван': 'Yerevan Armenia Ararat city',
    'Тбилиси': 'Tbilisi Georgia old town view',
    'Баку': 'Baku Azerbaijan skyline old city',
    'Дубай': 'Dubai skyline travel',
    'Прага': 'Prague old town Charles Bridge',
    'Париж': 'Paris Eiffel Tower city',
    'Рим': 'Rome Colosseum Vatican city view',
    'Барселона': 'Barcelona Sagrada Familia city',
}


def query(plan: dict, signal: dict) -> str:
    city = plan.get('city') or signal.get('route_to') or signal.get('city')
    if city in CITY_IMAGE_QUERY:
        return CITY_IMAGE_QUERY[city]
    country = plan.get('country') or signal.get('country')
    if city and country:
        return f'{city} {country} travel landmark city view'
    if plan.get('topic') in {'event_trip', 'concert_trip', 'weekend_activity'}:
        return 'travel event city landmark'
    return 'beautiful travel destination landmark'


def pexels(plan: dict, signal: dict) -> str:
    key = os.getenv('PEXELS_API_KEY', '').strip()
    if not key:
        return ''
    try:
        r = requests.get(
            'https://api.pexels.com/v1/search?' + urlencode({'query': query(plan, signal), 'per_page': 1, 'orientation': 'landscape'}),
            headers={'Authorization': key},
            timeout=10,
        )
        r.raise_for_status()
        photos = r.json().get('photos', [])
        if not photos:
            return ''
        src = photos[0].get('src', {})
        return src.get('large2x') or src.get('large') or src.get('medium') or ''
    except Exception:
        return ''


def card(plan: dict, signal: dict) -> Path:
    out = ROOT_DIR / 'data' / 'media_cache'
    out.mkdir(parents=True, exist_ok=True)
    safe = (plan.get('topic') or 'post').replace('/', '_')
    path = out / f'{safe}_fallback_card.jpg'
    img = Image.new('RGB', (1200, 900), (245, 241, 232))
    d = ImageDraw.Draw(img)
    try:
        big = ImageFont.truetype('DejaVuSans.ttf', 58)
        mid = ImageFont.truetype('DejaVuSans.ttf', 38)
        small = ImageFont.truetype('DejaVuSans.ttf', 30)
    except Exception:
        big = mid = small = None
    route = ' → '.join([x for x in [signal.get('route_from'), signal.get('route_to')] if x])
    price = signal.get('price', '')
    date = signal.get('depart_human', '')
    if plan.get('topic') == 'flight_deal' and route:
        title = route
        subtitle = ' · '.join([x for x in [date, ('от ' + price if price else '')] if x]) or 'проверьте даты и наличие мест'
    else:
        title = (plan.get('main_fact') or signal.get('title') or 'Мир на ладони')[:120]
        subtitle = plan.get('genre', 'travel')

    def lines(s: str, limit: int) -> list[str]:
        words = str(s).split()
        res, cur = [], ''
        for w in words:
            if len((cur + ' ' + w).strip()) <= limit:
                cur = (cur + ' ' + w).strip()
            else:
                if cur:
                    res.append(cur)
                cur = w
        if cur:
            res.append(cur)
        return res

    d.rectangle((54, 54, 1146, 846), outline=(55, 55, 55), width=4)
    d.text((90, 95), 'Мир на ладони', fill=(25, 25, 25), font=small)
    d.text((90, 250), '\n'.join(lines(title, 24)[:4]), fill=(10, 10, 10), font=big, spacing=12)
    d.text((90, 620), '\n'.join(lines(subtitle, 36)[:2]), fill=(55, 55, 55), font=mid, spacing=10)
    d.text((90, 780), 'Проверяйте условия перед покупкой', fill=(80, 80, 80), font=small)
    img.save(path, quality=92)
    return path


def choose_media(plan: dict, signal: dict, allow_fallback: bool = True) -> dict:
    if signal.get('media_url'):
        return {'type': 'url', 'value': signal['media_url'], 'source': 'source_media'}
    url = pexels(plan, signal)
    if url:
        return {'type': 'url', 'value': url, 'source': 'pexels'}
    if allow_fallback:
        return {'type': 'file', 'value': str(card(plan, signal)), 'source': 'fallback_card'}
    return {'type': 'none', 'value': '', 'source': 'none'}
