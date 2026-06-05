from __future__ import annotations
import re
from datetime import datetime, timezone
from typing import Any

CITY_HINTS = {'стамбул':('Стамбул','Турция'),'анталь':('Анталья','Турция'),'ереван':('Ереван','Армения'),'тбилис':('Тбилиси','Грузия'),'баку':('Баку','Азербайджан'),'белград':('Белград','Сербия'),'дубай':('Дубай','ОАЭ'),'рим':('Рим','Италия'),'париж':('Париж','Франция'),'барселон':('Барселона','Испания'),'прага':('Прага','Чехия'),'сочи':('Сочи','Россия'),'москв':('Москва','Россия')}

def clean_text(text: str) -> str:
    return re.sub(r'\s+', ' ', (text or '').replace('\xa0',' ')).strip()

def extract_price(text: str) -> str:
    m = re.search(r'\d[\d\s]{1,8}\s?(?:₽|руб\.?|рублей|€|евро|\$)', text or '', flags=re.I)
    return clean_text(m.group(0)) if m else ''

def detect_geo(text: str) -> tuple[str,str]:
    low=(text or '').lower()
    for k,v in CITY_HINTS.items():
        if k in low: return v
    return '', ''

def make_signal(source: dict[str, Any], title: str, url: str, text: str, published_at: str='') -> dict[str, Any]:
    title=clean_text(title)[:220]; text=clean_text(text)[:2800]; city,country=detect_geo(title+' '+text)
    return {'source_key':source['key'],'source_name':source['name'],'source_url':source['endpoint'],'title':title or text[:120] or source['name'],'text':text,'url':url or source['endpoint'],'published_at':published_at,'collected_at':datetime.now(timezone.utc).isoformat(),'price':extract_price(title+' '+text),'city':city,'country':country,'raw_role':source.get('role','')}
