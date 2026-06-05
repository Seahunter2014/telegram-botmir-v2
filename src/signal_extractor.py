from __future__ import annotations
import re
from datetime import datetime, timezone
from typing import Any

# Небольшой словарь нужен не для "угадывания всего мира", а чтобы не делать слепые ссылки.
# Если город не распознан, бот оставляет кнопку на источник и партнёрскую общую ссылку.
CITY_DATA = {
    'москва': ('Москва','Россия','MOW'), 'москву': ('Москва','Россия','MOW'), 'москвы': ('Москва','Россия','MOW'), 'москве': ('Москва','Россия','MOW'),
    'пермь': ('Пермь','Россия','PEE'), 'перми': ('Пермь','Россия','PEE'), 'пермью': ('Пермь','Россия','PEE'),
    'сочи': ('Сочи','Россия','AER'), 'адлер': ('Сочи','Россия','AER'),
    'краснодар': ('Краснодар','Россия','KRR'), 'краснодара': ('Краснодар','Россия','KRR'),
    'санкт-петербург': ('Санкт-Петербург','Россия','LED'), 'петербург': ('Санкт-Петербург','Россия','LED'), 'питера': ('Санкт-Петербург','Россия','LED'),
    'стамбул': ('Стамбул','Турция','IST'), 'стамбула': ('Стамбул','Турция','IST'), 'анталья': ('Анталья','Турция','AYT'), 'антальи': ('Анталья','Турция','AYT'),
    'ереван': ('Ереван','Армения','EVN'), 'еревана': ('Ереван','Армения','EVN'), 'тбилиси': ('Тбилиси','Грузия','TBS'),
    'баку': ('Баку','Азербайджан','GYD'), 'белград': ('Белград','Сербия','BEG'), 'дубай': ('Дубай','ОАЭ','DXB'), 'дубая': ('Дубай','ОАЭ','DXB'),
    'рим': ('Рим','Италия','ROM'), 'рима': ('Рим','Италия','ROM'), 'париж': ('Париж','Франция','PAR'), 'парижа': ('Париж','Франция','PAR'),
    'барселона': ('Барселона','Испания','BCN'), 'барселоны': ('Барселона','Испания','BCN'), 'прага': ('Прага','Чехия','PRG'), 'праги': ('Прага','Чехия','PRG')
}
MONTHS = {'января':'01','февраля':'02','марта':'03','апреля':'04','мая':'05','июня':'06','июля':'07','августа':'08','сентября':'09','октября':'10','ноября':'11','декабря':'12'}


def clean_text(text: str) -> str:
    return re.sub(r'\s+', ' ', (text or '').replace('\xa0',' ')).strip()


def _norm_city_token(token: str) -> str:
    return re.sub(r'[^а-яё\- ]+', '', token.lower()).strip()


def city_lookup(token: str) -> tuple[str,str,str]:
    t=_norm_city_token(token)
    if t in CITY_DATA:
        return CITY_DATA[t]
    for key, val in CITY_DATA.items():
        if key in t or t in key:
            return val
    return '', '', ''


def extract_price(text: str) -> str:
    m = re.search(r'\d[\d\s]{1,8}\s?(?:₽|руб\.?|рублей|€|евро|\$)', text or '', flags=re.I)
    return clean_text(m.group(0)) if m else ''


def detect_geo(text: str) -> tuple[str,str]:
    low=(text or '').lower()
    for k,(city,country,_) in CITY_DATA.items():
        if k in low:
            return city,country
    return '', ''


def extract_route(text: str) -> dict[str,str]:
    raw=clean_text(text)
    patterns=[
        r'из\s+([А-Яа-яЁё\- ]{3,30})\s+в\s+([А-Яа-яЁё\- ]{3,30})(?:\s|$|за|от|—|-|,|\.)',
        r'([А-Яа-яЁё\- ]{3,30})\s*[—–-]\s*([А-Яа-яЁё\- ]{3,30})(?:\s|$|за|от|,|\.)'
    ]
    for pat in patterns:
        m=re.search(pat, raw, flags=re.I)
        if not m: continue
        a,b=clean_text(m.group(1)),clean_text(m.group(2))
        ac,aco,ai=city_lookup(a); bc,bco,bi=city_lookup(b)
        if ac and bc and ac!=bc:
            return {'route_from':ac,'route_to':bc,'origin_iata':ai,'destination_iata':bi,'route_country_from':aco,'route_country_to':bco}
    return {}


def extract_depart_date(text: str) -> dict[str,str]:
    raw=(text or '').lower()
    m=re.search(r'\b([0-3]?\d)\s+(января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)\b', raw)
    if m:
        return {'depart_day':m.group(1).zfill(2),'depart_month':MONTHS[m.group(2)],'depart_human':f"{int(m.group(1))} {m.group(2)}"}
    # Если источник пишет просто "15 июня" в заголовке это поймается выше. Одинокую цифру не считаем датой, чтобы не делать ложные deeplink.
    return {}


def make_signal(source: dict[str, Any], title: str, url: str, text: str, published_at: str='', media_url: str='') -> dict[str, Any]:
    title=clean_text(title)[:220]; text=clean_text(text)[:2800]; full=title+' '+text
    city,country=detect_geo(full)
    data={'source_key':source['key'],'source_name':source['name'],'source_url':source['endpoint'],'title':title or text[:120] or source['name'],'text':text,'url':url or source['endpoint'],'published_at':published_at,'collected_at':datetime.now(timezone.utc).isoformat(),'price':extract_price(full),'city':city,'country':country,'raw_role':source.get('role',''),'media_url':media_url or ''}
    data.update(extract_route(full)); data.update(extract_depart_date(full))
    if data.get('route_to'):
        data['city']=data['route_to']; data['country']=data.get('route_country_to','') or data.get('country','')
    return data
