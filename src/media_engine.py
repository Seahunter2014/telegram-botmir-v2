from __future__ import annotations
import os, requests
from pathlib import Path
from urllib.parse import urlencode
from PIL import Image, ImageDraw, ImageFont
from .config_loader import ROOT_DIR

def query(plan:dict, signal:dict)->str:
    return ' '.join([x for x in [plan.get('city'),plan.get('country'),plan.get('genre'),signal.get('title')] if x])[:120] or 'travel'

def pexels(plan:dict, signal:dict)->str:
    key=os.getenv('PEXELS_API_KEY','').strip()
    if not key: return ''
    try:
        r=requests.get('https://api.pexels.com/v1/search?'+urlencode({'query':query(plan,signal),'per_page':1,'orientation':'portrait'}),headers={'Authorization':key},timeout=10); r.raise_for_status(); photos=r.json().get('photos',[])
        return photos[0].get('src',{}).get('large2x') or photos[0].get('src',{}).get('large') if photos else ''
    except Exception: return ''

def card(plan:dict, signal:dict)->Path:
    out=ROOT_DIR/'data'/'media_cache'; out.mkdir(parents=True,exist_ok=True); path=out/'fallback_card.jpg'
    img=Image.new('RGB',(1080,1350),(245,241,232)); d=ImageDraw.Draw(img)
    try: big=ImageFont.truetype('DejaVuSans.ttf',54); small=ImageFont.truetype('DejaVuSans.ttf',36)
    except Exception: big=small=None
    title=(plan.get('main_fact') or signal.get('title') or 'Мир на ладони')[:160]
    words=title.split(); lines=[]; cur=''
    for w in words:
        if len(cur+' '+w)<=26: cur=(cur+' '+w).strip()
        else: lines.append(cur); cur=w
    if cur: lines.append(cur)
    d.rectangle((60,60,1020,1290),outline=(80,80,80),width=4); d.text((100,180),'Мир на ладони',fill=(30,30,30),font=small); d.text((100,320),'\n'.join(lines[:8]),fill=(20,20,20),font=big,spacing=12); d.text((100,1120),plan.get('genre','travel'),fill=(60,60,60),font=small)
    img.save(path,quality=92); return path

def choose_media(plan:dict, signal:dict, allow_fallback:bool=True)->dict:
    url=pexels(plan,signal)
    if url: return {'type':'url','value':url,'source':'pexels'}
    if allow_fallback: return {'type':'file','value':str(card(plan,signal)),'source':'fallback_card'}
    return {'type':'none','value':'','source':'none'}
