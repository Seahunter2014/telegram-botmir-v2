from __future__ import annotations
import os, requests
from pathlib import Path
from urllib.parse import urlencode
from PIL import Image, ImageDraw, ImageFont
from .config_loader import ROOT_DIR

CITY_IMAGE_QUERY = {
    'Москва':'Moscow Kremlin Red Square skyline', 'Пермь':'Perm Russia city panorama', 'Сочи':'Sochi Russia sea mountains', 'Санкт-Петербург':'Saint Petersburg Russia city',
    'Стамбул':'Istanbul Bosphorus skyline', 'Анталья':'Antalya Turkey beach old town', 'Ереван':'Yerevan Armenia city Ararat', 'Тбилиси':'Tbilisi Georgia old town',
    'Баку':'Baku Azerbaijan skyline', 'Дубай':'Dubai skyline travel', 'Прага':'Prague old town travel', 'Париж':'Paris city travel', 'Рим':'Rome city travel'
}


def query(plan:dict, signal:dict)->str:
    # Для flight_deal не просим у Pexels случайный самолёт или случайную Москву: это часто даёт мусор.
    city=plan.get('city') or signal.get('route_to') or signal.get('city')
    if city in CITY_IMAGE_QUERY: return CITY_IMAGE_QUERY[city]
    country=plan.get('country') or signal.get('country')
    if city and country: return f'{city} {country} travel landmark'
    return 'beautiful travel destination landscape'


def pexels(plan:dict, signal:dict)->str:
    # Для билетов без нормального городского запроса лучше карточка, чем случайная нерелевантная фотография.
    if plan.get('topic')=='flight_deal' and not (plan.get('city') in CITY_IMAGE_QUERY):
        return ''
    key=os.getenv('PEXELS_API_KEY','').strip()
    if not key: return ''
    try:
        r=requests.get('https://api.pexels.com/v1/search?'+urlencode({'query':query(plan,signal),'per_page':1,'orientation':'portrait'}),headers={'Authorization':key},timeout=10)
        r.raise_for_status(); photos=r.json().get('photos',[])
        return photos[0].get('src',{}).get('large2x') or photos[0].get('src',{}).get('large') if photos else ''
    except Exception: return ''


def card(plan:dict, signal:dict)->Path:
    out=ROOT_DIR/'data'/'media_cache'; out.mkdir(parents=True,exist_ok=True)
    safe=(plan.get('topic') or 'post').replace('/','_')
    path=out/f'{safe}_fallback_card.jpg'
    img=Image.new('RGB',(1080,1350),(245,241,232)); d=ImageDraw.Draw(img)
    try:
        big=ImageFont.truetype('DejaVuSans.ttf',58); mid=ImageFont.truetype('DejaVuSans.ttf',42); small=ImageFont.truetype('DejaVuSans.ttf',32)
    except Exception:
        big=mid=small=None
    route=' → '.join([x for x in [signal.get('route_from'), signal.get('route_to')] if x])
    price=signal.get('price','')
    date=signal.get('depart_human','')
    if plan.get('topic')=='flight_deal' and route:
        title=route
        subtitle=' '.join([x for x in [date, ('от '+price if price else '')] if x]) or 'проверьте даты и наличие мест'
    else:
        title=(plan.get('main_fact') or signal.get('title') or 'Мир на ладони')[:120]
        subtitle=plan.get('genre','travel')
    def lines(s,limit):
        words=str(s).split(); res=[]; cur=''
        for w in words:
            if len((cur+' '+w).strip())<=limit: cur=(cur+' '+w).strip()
            else: res.append(cur); cur=w
        if cur: res.append(cur)
        return res
    d.rectangle((58,58,1022,1292),outline=(70,70,70),width=4)
    d.text((90,140),'Мир на ладони',fill=(25,25,25),font=small)
    d.text((90,320),'\n'.join(lines(title,22)[:5]),fill=(10,10,10),font=big,spacing=14)
    d.text((90,760),'\n'.join(lines(subtitle,28)[:3]),fill=(55,55,55),font=mid,spacing=10)
    d.text((90,1140),'Проверьте условия перед покупкой',fill=(80,80,80),font=small)
    img.save(path,quality=92); return path


def choose_media(plan:dict, signal:dict, allow_fallback:bool=True)->dict:
    # 1) Фото из источника, если источник его отдал.
    if signal.get('media_url'):
        return {'type':'url','value':signal['media_url'],'source':'source_media'}
    # 2) Для flight_deal карточка лучше случайного нерелевантного фото.
    if plan.get('topic')=='flight_deal' and allow_fallback:
        return {'type':'file','value':str(card(plan,signal)),'source':'offer_card'}
    # 3) Для направлений можно пробовать Pexels с нормальным английским запросом.
    url=pexels(plan,signal)
    if url: return {'type':'url','value':url,'source':'pexels'}
    if allow_fallback: return {'type':'file','value':str(card(plan,signal)),'source':'fallback_card'}
    return {'type':'none','value':'','source':'none'}
