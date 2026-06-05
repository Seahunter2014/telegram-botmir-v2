from __future__ import annotations
from typing import Any
from urllib.parse import urlencode
import os
from .config_loader import link_rule_for_topic


def _by_category(bundle:Any, category:str, topic:str)->list[dict]:
    out=[]
    for s in bundle.services['services']:
        if s.get('status')!='active' or s.get('category')!=category: continue
        if topic in s.get('usage_rules',[]) or not s.get('usage_rules'): out.append(s)
    return sorted(out, key=lambda x:x.get('priority',0), reverse=True)


def _aviasales_search_url(plan:dict)->str:
    sig=plan.get('signal') or {}
    origin=sig.get('origin_iata'); dest=sig.get('destination_iata')
    marker=os.getenv('TRAVELPAYOUTS_MARKER') or os.getenv('AVIASALES_MARKER') or '98526'
    if not (origin and dest): return ''
    dd=sig.get('depart_day'); mm=sig.get('depart_month')
    route=f'{origin}{dd}{mm}{dest}' if dd and mm else f'{origin}{dest}'
    return 'https://www.aviasales.ru/search/'+route+'?'+urlencode({'marker':marker})


def select_cta(plan:dict, bundle:Any)->dict:
    topic=plan['topic']; rule=link_rule_for_topic(bundle, topic)
    cats=rule.get('links',[]) if rule else plan.get('allowed_categories',[])
    max_links=rule.get('max_links',plan.get('max_links',2)) if rule else plan.get('max_links',2)
    fmt=rule.get('preferred_format','text') if rule else 'text'
    if max_links<=0 or fmt=='no_partner_link':
        return {'text_cta':'','buttons':[],'format':'no_partner_link','reason':'Жанр без партнёрских ссылок'}
    buttons=[]
    sig=plan.get('signal') or {}
    # Для офферов сначала даём прямую ссылку на исходное предложение, иначе пользователь видит красивый текст без фактической опоры.
    if topic in {'flight_deal','tour_offer','last_minute','hot_tour'} and sig.get('url'):
        buttons.append({'text':'Открыть предложение','url':sig['url'],'service_key':'source_offer','category':'source'})
    for cat in cats:
        cand=_by_category(bundle,cat,topic)
        if not cand:
            cand=[s for s in bundle.services['services'] if s.get('status')=='active' and s.get('category')==cat]
        if not cand: continue
        s=cand[0]
        url=s['ref_url']
        text=s.get('button_text') or s['name']
        if cat=='flights' and topic=='flight_deal':
            deep=_aviasales_search_url(plan)
            if deep:
                url=deep
                frm=sig.get('route_from','')
                to=sig.get('route_to','')
                text=f'Проверить {frm} → {to}' if frm and to else 'Проверить билеты'
        if all(b.get('url')!=url for b in buttons):
            buttons.append({'text':text,'url':url,'service_key':s['key'],'category':s['category']})
        if len(buttons)>=max_links: break
    return {'text_cta':_text(topic,fmt,buttons,plan),'buttons':buttons[:max_links],'format':fmt,'reason':'Ссылки выбраны по link_rules.json; для оффера добавлена ссылка на источник'}


def _text(topic:str, fmt:str, buttons:list[dict], plan:dict)->str:
    if not buttons: return ''
    sig=plan.get('signal') or {}
    price=sig.get('price','')
    route=' → '.join([x for x in [sig.get('route_from'),sig.get('route_to')] if x])
    if fmt=='soft_cta': return 'Полезные сервисы лучше проверить заранее — особенно если поездка связана с документами, оплатой или страховкой.'
    if topic=='flight_deal':
        parts=[]
        if route: parts.append(route)
        if price: parts.append(f'от {price}')
        return 'Проверяйте конкретные даты и наличие мест перед покупкой' + (': ' + ', '.join(parts) if parts else '.')
    if topic in {'last_minute'}: return 'Если направление подходит по датам, лучше проверить варианты сразу: такие предложения быстро меняются.'
    if topic in {'tour_offer','hot_tour'}: return 'Для готового отдыха удобнее сразу сравнить даты, состав тура и условия.'
    if topic in {'event_trip','concert_trip','weekend_activity'}: return 'Событие проще превращается в поездку, когда сразу понятны билеты, проживание и дорога.'
    return 'Ниже — сервисы, через которые можно быстро проверить детали поездки.'
