from __future__ import annotations
from typing import Any
from .anti_template_checker import check_variant
from .fact_checker import fact_check_variant

BAD_GENERIC = ['давно хотели', 'отличный момент', 'рекомендуем', 'заранее — тогда', 'комфортной и оправдает ожидания', 'не терять время на поиски', 'такие предложения быстро меняются']


def score_variant(variant:dict, plan:dict, bundle:Any)->dict:
    anti=check_variant(variant,bundle); fact=fact_check_variant(variant,plan); score=int(variant.get('score') or 70)
    score-=len(anti['issues'])*15+len(fact['warnings'])*5
    full=(variant.get('title','')+' '+variant.get('text','')+' '+variant.get('cta','')).lower()
    if len(variant.get('text',''))>500: score+=4
    if '?' in full: score+=2
    if any(w in full for w in ['сохран','перешл','проверить','выбрали']): score+=3
    # Для flight_deal конкретика важнее красивого слога.
    if plan.get('topic')=='flight_deal':
        sig=plan.get('signal') or {}
        if sig.get('price') and sig['price'].lower() in full: score+=10
        if sig.get('route_to') and sig['route_to'].lower() in full: score+=8
        if sig.get('route_from') and sig['route_from'].lower() in full: score+=8
        if not sig.get('price') or sig.get('price','').lower() not in full: score-=12
        if not sig.get('route_to') or sig.get('route_to','').lower() not in full: score-=12
    for phrase in BAD_GENERIC:
        if phrase in full: score-=18
    return {'score':max(0,min(100,score)),'anti_template':anti,'fact_check':fact}


def select_best_variant(variants:list[dict], plan:dict, bundle:Any)->dict:
    scored=[]
    for i,v in enumerate(variants,1):
        v={**v,'index':i,'quality':score_variant(v,plan,bundle)}; scored.append(v)
    return sorted(scored,key=lambda x:x['quality']['score'], reverse=True)[0]
