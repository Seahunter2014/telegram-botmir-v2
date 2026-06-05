from __future__ import annotations
import re
from typing import Any
from .dedup_engine import is_duplicate_variant

def check_variant(variant:dict, bundle:Any)->dict:
    text=f"{variant.get('title','')}\n{variant.get('text','')}\n{variant.get('cta','')}"; issues=[]
    for p in bundle.forbidden.get('phrases',[]):
        if p.lower() in text.lower(): issues.append('Запрещённая фраза обнаружена')
    if ('сигнал' + ' для') in text.lower(): issues.append('Внутренняя техническая фраза')
    paras=[p.strip() for p in variant.get('text','').split('\n') if p.strip()]
    if len(paras)<3: issues.append('Мало абзацев')
    if len(variant.get('text',''))<450: issues.append('Мало текста и конкретики')
    if len(variant.get('title',''))<18: issues.append('Слабый заголовок')
    starts=[]
    for p in paras:
        m=re.findall(r'[A-Za-zА-Яа-яЁё0-9]+',p.lower()); starts.append(m[0] if m else '')
    if len(starts)>=3 and len(set(starts))<len(starts): issues.append('Повторяются начала абзацев')
    dup, reason=is_duplicate_variant(text)
    if dup: issues.append(reason)
    return {'passed':not issues,'issues':issues,'quality_score':max(0,100-len(issues)*18)}
