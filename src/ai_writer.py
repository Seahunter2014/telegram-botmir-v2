from __future__ import annotations
import json, os
from typing import Any
from openai import OpenAI
from .cta_engine import select_cta
from .anti_template_checker import check_variant


def client() -> OpenAI:
    key=os.getenv('OPENAI_API_KEY','').strip()
    if not key: raise RuntimeError('OPENAI_API_KEY не задан. Шаблонный fallback запрещён.')
    return OpenAI(api_key=key)


def model()->str: return os.getenv('OPENAI_MODEL','gpt-4.1-mini').strip() or 'gpt-4.1-mini'
def temp()->float:
    try: return float(os.getenv('OPENAI_TEMPERATURE','0.85'))
    except ValueError: return 0.85


def _genre_hard_rules(plan:dict)->str:
    topic=plan.get('topic')
    if topic=='flight_deal':
        return '''ЖАНР: авиабилет/рейс.
Обязательные требования:
- заголовок должен содержать маршрут, цену и/или дату, если они есть в сигнале;
- первый абзац должен начинаться с конкретного факта, а не с рассуждения;
- обязательно упомяни, что цену/места надо проверить перед покупкой;
- не пиши общие фразы вроде «давно хотели попасть», «отличный момент», «рекомендуем определиться»;
- не обещай наличие билетов;
- не превращай пост в инструкцию для новичков;
- текст 500–900 знаков, живой, конкретный.'''
    if topic in {'destination_post','weekend_trip','city_break'}:
        return '''ЖАНР: направление/короткая поездка.
Обязательные требования:
- минимум 2 конкретные детали места или сценария поездки;
- не начинать с абстрактной философии путешествий;
- не продавать жёстко, если нет оффера;
- финал должен вовлекать или мягко вести к проверке деталей.'''
    if topic in {'tour_offer','hot_tour','last_minute'}:
        return '''ЖАНР: тур/оффер.
Обязательные требования:
- вынести цену/даты/условия, если они есть;
- не скрывать, что детали надо проверить;
- CTA прямой, но без истерики.'''
    return 'Пиши конкретно, без воды, с опорой на факт из сигнала. Если фактов мало — честно сделай короткий пост, а не растягивай пустоту.'


def _hard_prompt(plan:dict, signal:dict, cta:dict, bundle:Any)->str:
    return '\n\n'.join([
        bundle.prompts['system_editor_ru'],
        bundle.prompts['writer_3_variants_ru'],
        bundle.prompts['anti_template_ru'],
        _genre_hard_rules(plan),
        'КРИТИЧЕСКИ ВАЖНО: не делай текст похожим на старый шаблон. В каждом варианте должны быть разные заголовки, первые абзацы и концовки.',
        'НЕ ДОПУСКАТЬ: общих абзацев, которые можно вставить в любой travel-пост. Каждый абзац должен быть связан с сигналом.',
        'ДАННЫЕ СИГНАЛА:', json.dumps(signal,ensure_ascii=False,indent=2),
        'РЕДАКЦИОННЫЙ ПЛАН:', json.dumps(plan,ensure_ascii=False,indent=2),
        'CTA И КНОПКИ:', json.dumps(cta,ensure_ascii=False,indent=2),
        'Верни строго JSON без markdown: {"variants":[{"title":"","text":"","cta":"","style":"","score":80,"notes":[]}]} Ровно 3 варианта.'
    ])


def generate_variants(plan:dict, signal:dict, bundle:Any)->list[dict]:
    cta=select_cta(plan,bundle)
    prompt=_hard_prompt(plan,signal,cta,bundle)
    r=client().chat.completions.create(model=model(), temperature=temp(), response_format={'type':'json_object'}, messages=[{'role':'system','content':'Ты возвращаешь только валидный JSON на русском языке. Никакого markdown, никаких пояснений.'},{'role':'user','content':prompt}])
    data=json.loads(r.choices[0].message.content or '{}'); variants=data.get('variants',[])
    if not isinstance(variants,list) or len(variants)<3: raise RuntimeError('OpenAI не вернул 3 варианта поста')
    out=[]
    for item in variants[:3]:
        out.append({'title':str(item.get('title','')).strip(),'text':str(item.get('text','')).strip(),'cta':str(item.get('cta','')).strip(),'style':str(item.get('style','')).strip(),'score':int(item.get('score',70) or 70),'notes':item.get('notes',[]),'buttons':cta.get('buttons',[])})
    return out


def rewrite_variant(variant:dict, plan:dict, signal:dict, bundle:Any, mode:str)->dict:
    task={'rewrite':'Перепиши полностью: больше фактов, меньше воды, другой заголовок и другая концовка.','softer':'Сделай мягче и редакционнее, но не размывай конкретику.','sales':'Сделай продающе, но с конкретикой и без рекламного шума.'}.get(mode,'Перепиши полностью.')
    cta=select_cta(plan,bundle)
    prompt='\n\n'.join([bundle.prompts['system_editor_ru'], bundle.prompts['anti_template_ru'], _genre_hard_rules(plan), task, json.dumps({'variant':variant,'plan':plan,'signal':signal,'cta':cta},ensure_ascii=False,indent=2), 'Верни JSON: {"title":"","text":"","cta":"","style":"","score":80,"notes":[]}'])
    r=client().chat.completions.create(model=model(), temperature=temp(), response_format={'type':'json_object'}, messages=[{'role':'system','content':'Только валидный JSON на русском.'},{'role':'user','content':prompt}])
    data=json.loads(r.choices[0].message.content or '{}'); data['buttons']=cta.get('buttons',[]); return data


def ensure_quality_or_raise(variants:list[dict], bundle:Any)->None:
    bad=[]
    for i,v in enumerate(variants,1):
        check=check_variant(v,bundle)
        if not check['passed']: bad.append(f"Вариант {i}: {'; '.join(check['issues'])}")
    if len(bad)==len(variants): raise RuntimeError('Все варианты забракованы: '+' | '.join(bad))
