from __future__ import annotations
from typing import Any
from .rotation_engine import slot_name_ru

def cta_level(topic:str)->str:
    if topic in {'flight_deal','tour_offer','last_minute','hot_tour'}: return 'прямой'
    if topic in {'visa_or_residence','relocation','payment_abroad','practical_travel'}: return 'мягкий'
    if topic in {'inspiration_story','viral_travel','discussion_post'}: return 'без продажи'
    return 'редакционный'

def plan_post(signal:dict, topic:str, score:dict, slot:str, bundle:Any)->dict:
    cfg=next((t for t in bundle.topics['topics'] if t['key']==topic),{})
    return {'topic':topic,'genre':cfg.get('name',topic),'slot':slot,'slot_ru':slot_name_ru(slot),'source':signal.get('source_name',''),'source_url':signal.get('url',''),'city':signal.get('city',''),'country':signal.get('country',''),'price':signal.get('price',''),'main_fact':signal.get('title',''),'source_text':signal.get('text',''),'target_emotion':'сохранить, переслать или открыть ссылку по смыслу','hook_angle':_hook(topic),'practical_value':_value(topic),'cta_level':cta_level(topic),'allowed_categories':cfg.get('cta_categories',[]),'max_links':cfg.get('max_links',2),'forbidden_claims':['Не обещать наличие мест.','Не утверждать цену как гарантированную.','Не делать юридические выводы.'],'score':score}

def _hook(topic:str)->str:
    return {'flight_deal':'билет как повод быстро собрать поездку','tour_offer':'готовый сценарий отдыха','destination_post':'почему направление актуально сейчас','hotel_post':'отель как самостоятельный повод','event_trip':'событие как причина увидеть город','visa_or_residence':'что важно понять заранее','practical_travel':'маленькое решение, которое упрощает поездку'}.get(topic,'редакционный travel-повод')

def _value(topic:str)->str:
    return 'дать понятный следующий шаг' if topic in {'flight_deal','tour_offer','hotel_post'} else 'помочь избежать ошибки' if topic in {'practical_travel','travel_hack','visa_or_residence'} else 'показать, как превратить идею в поездку'
