from __future__ import annotations

def fact_check_variant(variant:dict, plan:dict)->dict:
    text=f"{variant.get('title','')} {variant.get('text','')} {variant.get('cta','')}".lower(); warnings=[]
    if plan.get('price') and plan['price'].lower() not in text: warnings.append('В источнике была цена, но в тексте она не использована.')
    for word in ['гарантированно','точно будет','без риска','100%','лучший в мире']:
        if word in text: warnings.append('Слишком категорично: '+word)
    if plan.get('topic') in {'visa_or_residence','relocation'} and not any(x in text for x in ['проверить','условия','документы','заранее']): warnings.append('Нужна осторожная формулировка по условиям и документам.')
    return {'passed':not warnings,'warnings':warnings}
