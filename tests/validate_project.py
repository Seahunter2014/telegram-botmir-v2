import ast
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    "src/telegram_app.py", "src/source_manager.py", "src/topic_guard.py", "src/topic_classifier.py",
    "src/scoring_engine.py", "src/rotation_engine.py", "src/dedup_engine.py", "src/editorial_brief_engine.py",
    "src/ai_writer.py", "src/engagement_engine.py", "src/quality_selector.py", "src/anti_template_checker.py",
    "src/fact_checker.py", "src/cta_engine.py", "src/media_engine.py", "src/publisher.py",
    "configs/sources.json", "configs/services.json", "configs/link_rules.json", "configs/topics.json",
    "prompts/system_editor_ru.md", "prompts/hook_engagement_engine_ru.md", "requirements.txt"
]
FORBIDDEN_FILES = ["draft_writer.py", "style_editor.py", "download", "download (1)"]

errors=[]

def fail(msg): errors.append(msg)

for rel in REQUIRED:
    if not (ROOT/rel).exists(): fail(f"Нет файла: {rel}")

for p in ROOT.rglob("*"):
    if p.name == "__pycache__" or p.suffix == ".pyc": fail(f"Мусор: {p}")
    if p.name in FORBIDDEN_FILES: fail(f"Старый/мусорный файл: {p}")

req = (ROOT/"requirements.txt").read_text(encoding="utf-8")
if "TELEGRAM_BOT_TOKEN" in req or "OPENAI_API_KEY" in req:
    fail("requirements.txt содержит переменные или мусор")

for py in (ROOT/"src").glob("*.py"):
    try:
        source = py.read_text(encoding="utf-8")
        ast.parse(source)
        compile(source, str(py), "exec")
    except SyntaxError as e:
        fail(f"SyntaxError {py}: {e}")

for js in (ROOT/"configs").glob("*.json"):
    try:
        json.loads(js.read_text(encoding="utf-8"))
    except Exception as e:
        fail(f"JSON error {js}: {e}")

services = json.loads((ROOT/"configs/services.json").read_text(encoding="utf-8"))
if not any(s.get("key") == "tourjin_bot" and "TourJin" in s.get("name", "") for s in services):
    fail("В services.json нет TourJin Bot")

telegram = (ROOT/"src/telegram_app.py").read_text(encoding="utf-8")
for token in ["schedule_set", "add_channel", "remove_channel", "set_channels", "test_cmd", "text_test_handler", "rewrite_cmd", "softer_cmd", "sales_cmd", "publish_cmd"]:
    if token not in telegram:
        fail(f"В telegram_app.py нет сценария: {token}")

version = (ROOT/"src/version.py").read_text(encoding="utf-8")
if "PROJECT_NAME" not in version or "VERSION" not in version:
    fail("В version.py нет PROJECT_NAME или VERSION")

prompt_files = ["system_editor_ru.md", "hook_engagement_engine_ru.md", "editorial_planner_ru.md", "writer_3_variants_ru.md", "anti_template_ru.md", "quality_selector_ru.md", "cta_rules_ru.md", "fact_check_ru.md"]
for name in prompt_files:
    if not (ROOT/"prompts"/name).exists():
        fail(f"Нет промта: {name}")

forbidden = json.loads((ROOT/"configs/forbidden_phrases.json").read_text(encoding="utf-8"))
if not forbidden:
    fail("forbidden_phrases.json пуст")

if errors:
    print("VALIDATION FAILED")
    for e in errors: print("ERROR:", e)
    raise SystemExit(1)
print("OK: структура соответствует ТЗ")
print("OK: requirements.txt чистый")
print("OK: мусора нет")
print("OK: JSON читаются")
print("OK: src/*.py компилируются")
print("OK: TourJin есть в services.json")
print("OK: меню расписания/каналов/тестов присутствует")
