from __future__ import annotations
from typing import Any
from .source_manager import freshness_score
from .dedup_engine import rotation_penalty

def score_signal(signal:dict, topic:str, slot:str, bundle:Any)->dict:
    text=f"{signal.get('title','')} {signal.get('text','')}"; concrete=(7 if signal.get('price') else 0)+(5 if signal.get('city') else 0)+(4 if any(ch.isdigit() for ch in text) else 0)+(4 if len(text)>180 else 0)
    emotion=15 if topic in {'hidden_places','inspiration_story','viral_travel','luxury_escape','beach_trip'} else 10
    share=15 if topic in {'viral_travel','weird_travel','hidden_places','discussion_post'} else 12 if topic in {'practical_travel','travel_hack','visa_or_residence'} else 8
    use=10 if topic in {'practical_travel','travel_hack','visa_or_residence','payment_abroad','insurance_tip'} else 8 if topic in {'flight_deal','tour_offer','event_trip'} else 6
    rule=next((r for r in bundle.link_rules['rules'] if r['topic']==topic),None); aff=6 if rule and rule.get('max_links',0)==0 else 10 if rule else 4
    slot_fit=10 if topic in bundle.policy.get('slots',{}).get(slot,{}).get('preferred_topics',[]) else 4
    pen,reasons=rotation_penalty(signal, topic)
    parts={'freshness':freshness_score(signal),'concreteness':min(20,concrete),'emotion':emotion,'shareability':share,'usefulness':use,'affiliate_fit':aff,'slot_fit':slot_fit}
    return {'score':max(0,min(100,sum(parts.values())-pen)),'parts':parts,'penalty':pen,'penalty_reasons':reasons}
