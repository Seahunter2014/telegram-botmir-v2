from __future__ import annotations
import json, re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def fail(m:str): print('ОШИБКА:',m); raise SystemExit(1)
def ok(m:str): print('OK:',m)

def check_structure():
    required=['src/telegram_app.py','src/source_manager.py','src/ai_writer.py','src/anti_template_checker.py','configs/topics.json','configs/sources.json','configs/services.json','configs/link_rules.json','configs/editorial_policy.json','configs/forbidden_phrases.json','prompts/system_editor_ru.md','requirements.txt','.env.example']
    for r in required:
        if not (ROOT/r).exists(): fail('нет файла '+r)
    for old in ['draft_writer.py','style_editor.py']:
        if (ROOT/old).exists() or (ROOT/'src'/old).exists(): fail('найден старый файл '+old)
    ok('структура соответствует ТЗ')

def check_requirements():
    text=(ROOT/'requirements.txt').read_text(encoding='utf-8')
    if 'TELEGRAM_BOT_TOKEN' in text or 'OPENAI_API_KEY' in text: fail('в requirements.txt попали переменные')
    lines=[x.strip() for x in text.splitlines() if x.strip()]
    if len(lines)<5: fail('requirements.txt короткий')
    for line in lines:
        if ' ' in line: fail('в requirements.txt строка с пробелом: '+line)
        if not re.match(r'^[A-Za-z0-9_.-]+([<>=!~]=?.+)?$', line): fail('некорректная зависимость: '+line)
    ok('requirements.txt чистый')

def check_garbage():
    for p in ROOT.rglob('*'):
        if p.name in {'__pycache__','download','download (1)','download (2)'}: fail('мусор: '+str(p))
        if p.suffix=='.pyc': fail('pyc: '+str(p))
        if p.suffix in {'.zip','.rar','.7z'}: fail('архив внутри проекта: '+str(p))
    ok('мусора нет')

def check_json():
    for p in list((ROOT/'configs').glob('*.json'))+list((ROOT/'data').glob('*.json')): json.loads(p.read_text(encoding='utf-8'))
    ok('JSON читаются')

def check_compile():
    for p in (ROOT/'src').glob('*.py'):
        compile(p.read_text(encoding='utf-8'), str(p), 'exec')
    ok('src/*.py компилируются')

def check_forbidden_runtime():
    phrases=json.loads((ROOT/'configs/forbidden_phrases.json').read_text(encoding='utf-8'))['phrases']
    for p in (ROOT/'src').glob('*.py'):
        text=p.read_text(encoding='utf-8')
        for phrase in phrases:
            
            if re.search(r'(?<![А-Яа-яЁёA-Za-z])'+re.escape(phrase)+r'(?![А-Яа-яЁёA-Za-z])', text, flags=re.IGNORECASE):
                fail(f'запрещённая фраза в runtime-коде {p.name}: {phrase}')
    ok('старых шаблонных фраз в runtime-коде нет')

def main():
    check_structure(); check_requirements(); check_garbage(); check_json(); check_compile(); check_forbidden_runtime(); ok('проект прошёл проверку')
if __name__=='__main__': main()
