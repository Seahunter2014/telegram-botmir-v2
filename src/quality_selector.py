from __future__ import annotations
from typing import Any
from .anti_template_checker import check_variant
from .fact_checker import fact_check_variant

def score_variant(variant:dict, plan:dict, bundle:Any)->dict:
    anti=check_variant(variant,bundle); fact=fact_check_variant(variant,plan); score=int(variant.get('score') or 70)
    score-=len(anti['issues'])*12+len(fact['warnings'])*5
    text=variant.get('text','').lower()
    if len(text)>600: score+=5
    if '?' in text: score+=3
    if any(w in text for w in ['сохран','перешл','проверить','выбрали']): score+=4
    return {'score':max(0,min(100,score)),'anti_template':anti,'fact_check':fact}

def select_best_variant(variants:list[dict], plan:dict, bundle:Any)->dict:
    scored=[]
    for i,v in enumerate(variants,1):
        v={**v,'index':i,'quality':score_variant(v,plan,bundle)}; scored.append(v)
    return sorted(scored,key=lambda x:x['quality']['score'], reverse=True)[0]
