from __future__ import annotations
from typing import Any
from .config_loader import link_rule_for_topic

def _by_category(bundle:Any, category:str, topic:str)->list[dict]:
    out=[]
    for s in bundle.services['services']:
        if s.get('status')!='active' or s.get('category')!=category: continue
        if topic in s.get('usage_rules',[]) or not s.get('usage_rules'): out.append(s)
    return sorted(out, key=lambda x:x.get('priority',0), reverse=True)

def select_cta(plan:dict, bundle:Any)->dict:
    topic=plan['topic']; rule=link_rule_for_topic(bundle, topic)
    cats=rule.get('links',[]) if rule else plan.get('allowed_categories',[]); max_links=rule.get('max_links',plan.get('max_links',2)) if rule else plan.get('max_links',2); fmt=rule.get('preferred_format','text') if rule else 'text'
    if max_links<=0 or fmt=='no_partner_link': return {'text_cta':'','buttons':[],'format':'no_partner_link','reason':'Жанр без партнёрских ссылок'}
    buttons=[]
    for cat in cats:
        cand=_by_category(bundle,cat,topic)
        if not cand: cand=[s for s in bundle.services['services'] if s.get('status')=='active' and s.get('category')==cat]
        if not cand: continue
        s=cand[0]; buttons.append({'text':s.get('button_text') or s['name'],'url':s['ref_url'],'service_key':s['key'],'category':s['category']})
        if len(buttons)>=max_links: break
    return {'text_cta':_text(topic,fmt,buttons),'buttons':buttons,'format':fmt,'reason':'Ссылки выбраны по link_rules.json'}

def _text(topic:str, fmt:str, buttons:list[dict])->str:
    if not buttons: return ''
    if fmt=='soft_cta': return 'Полезные сервисы лучше проверить заранее — особенно если поездка связана с документами, оплатой или страховкой.'
    if topic in {'flight_deal','last_minute'}: return 'Если направление подходит по датам, лучше проверить варианты сразу: такие предложения быстро меняются.'
    if topic in {'tour_offer','hot_tour'}: return 'Для готового отдыха удобнее сразу сравнить даты, состав тура и условия.'
    if topic in {'event_trip','concert_trip','weekend_activity'}: return 'Событие проще превращается в поездку, когда сразу понятны билеты, проживание и дорога.'
    return 'Ниже — сервисы, через которые можно быстро проверить детали поездки.'
