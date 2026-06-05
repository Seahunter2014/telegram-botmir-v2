from __future__ import annotations
from datetime import datetime
from typing import Any
from uuid import uuid4
from .source_manager import collect_signals
from .topic_classifier import classify_signal
from .rotation_engine import current_slot
from .dedup_engine import is_duplicate_signal
from .scoring_engine import score_signal
from .editorial_planner import plan_post
from .ai_writer import generate_variants, ensure_quality_or_raise
from .quality_selector import score_variant, select_best_variant
from .cta_engine import select_cta
from .media_engine import choose_media
from .state_store import record_skip, record_selection

def candidate_pool(bundle:Any, forced_slot:str|None=None)->list[dict]:
    slot=current_slot(bundle.policy, forced_slot); pool=[]
    for sig in collect_signals(bundle):
        dup, reason=is_duplicate_signal(sig)
        if dup: continue
        topic=classify_signal(sig,bundle,slot); sc=score_signal(sig,topic,slot,bundle)
        if sc['score'] < int(bundle.policy.get('minimum_score',60)): continue
        pool.append({'signal':sig,'topic':topic,'score':sc,'slot':slot})
    return sorted(pool,key=lambda x:x['score']['score'], reverse=True)

def create_package(bundle:Any, forced_topic:str|None=None, forced_slot:str|None=None, allow_media:bool=True)->dict:
    pool=candidate_pool(bundle,forced_slot)
    if forced_topic: pool=[p for p in pool if p['topic']==forced_topic] or pool
    if not pool:
        record_skip('no_fresh_candidate','Нет свежих тем после фильтров')
        raise RuntimeError('Не найдено свежих тем: источники недоступны, устарели или отфильтрованы дедупликацией.')
    ch=pool[0]; signal=ch['signal']; topic=ch['topic']; slot=ch['slot']; plan=plan_post(signal,topic,ch['score'],slot,bundle); cta=select_cta(plan,bundle)
    variants=generate_variants(plan,signal,bundle); ensure_quality_or_raise(variants,bundle)
    scored=[]
    for v in variants:
        v['buttons']=cta.get('buttons',[]); v['quality']=score_variant(v,plan,bundle); scored.append(v)
    best=select_best_variant(scored,plan,bundle); media=choose_media(plan,signal,allow_media)
    package={'id':uuid4().hex,'created_at':datetime.now().isoformat(),'slot':slot,'signal':signal,'topic':topic,'plan':plan,'cta':cta,'variants':scored,'best_variant':best,'media':media,'pool_size':len(pool)}
    record_selection({'package_id':package['id'],'topic':topic,'slot':slot,'source':signal.get('source_name'),'title':signal.get('title'),'score':ch['score'],'pool_size':len(pool)})
    return package
