from __future__ import annotations

import json
import os
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_ROOT = ["requirements.txt", "README.md", ".env.example", "railway.json", "Procfile", "main.py"]
REQUIRED_DIRS = ["src", "configs", "prompts", "data", "tests", "docs", "media_cache"]
REQUIRED_SRC = [
    "telegram_app.py", "menu.py", "config_loader.py", "source_registry.py", "source_manager.py", "source_health.py",
    "signal_extractor.py", "fallback_topic_engine.py", "topic_guard.py", "topic_classifier.py", "scoring_engine.py",
    "rotation_engine.py", "dedup_engine.py", "editorial_brief_engine.py", "openai_client.py", "ai_writer.py",
    "engagement_engine.py", "anti_template_checker.py", "fact_checker.py", "quality_selector.py", "cta_engine.py",
    "url_builder.py", "media_engine.py", "media_sources.py", "image_generation.py", "telegram_post_writer.py",
    "publisher.py", "scheduler.py", "diagnostics.py", "state_store.py", "analytics_store.py", "version.py", "models.py"
]
REQUIRED_CONFIGS = ["sources.json", "services.json", "topics.json", "fallback_topics.json", "link_rules.json", "editorial_policy.json", "forbidden_phrases.json", "media_sources.json", "cities_iata.json", "city_aliases.json"]
REQUIRED_ENVS = ["TELEGRAM_BOT_TOKEN", "TELEGRAM_ADMIN_ID", "TELEGRAM_CHANNEL_ID", "TEST_CHANNEL_ID", "OPENAI_API_KEY", "OPENAI_MODEL", "OPENAI_TEMPERATURE", "SCHEDULE_TIMEZONE", "ALLOW_FALLBACK_AUTOPUBLISH"]


def fail(msg: str):
    raise SystemExit("FAIL: " + msg)


def main():
    for d in REQUIRED_DIRS:
        if not (ROOT / d).is_dir(): fail(f"нет папки {d}")
    for f in REQUIRED_ROOT:
        if not (ROOT / f).is_file(): fail(f"нет файла {f}")
    for f in REQUIRED_SRC:
        if not (ROOT / "src" / f).is_file(): fail(f"нет src/{f}")
    for f in REQUIRED_CONFIGS:
        path = ROOT / "configs" / f
        if not path.is_file(): fail(f"нет configs/{f}")
        try: json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc: fail(f"configs/{f} не JSON: {exc}")
    for p in list((ROOT / "src").glob("*.py")) + list((ROOT / "tests").glob("*.py")):
        ast.parse(p.read_text(encoding="utf-8"), filename=str(p))
    req = (ROOT / "requirements.txt").read_text(encoding="utf-8")
    if "TELEGRAM_BOT_TOKEN" in req or "OPENAI_API_KEY" in req: fail("секреты в requirements")
    if any("download" in str(p) for p in ROOT.rglob("*")): fail("есть download")
    if any(p.name == "__pycache__" for p in ROOT.rglob("*")): fail("есть __pycache__")
    if any(p.suffix == ".pyc" for p in ROOT.rglob("*")): fail("есть pyc")
    env_text = (ROOT / ".env.example").read_text(encoding="utf-8")
    for e in REQUIRED_ENVS:
        if e not in env_text: fail(f"нет env {e}")
    services = json.loads((ROOT / "configs/services.json").read_text(encoding="utf-8"))
    if not any(s.get("key") == "tourjin_bot" and s.get("url") == "https://t.me/TourJin_bot" for s in services): fail("нет TourJin")
    sources = json.loads((ROOT / "configs/sources.json").read_text(encoding="utf-8"))
    for url in ["https://t.me/s/hackmytrip", "https://vk.com/tourister", "https://dzen.ru/tonkostiru?tab=articles", "https://t.me/s/travelnews24", "https://t.me/s/travel_tema", "https://ru.wikivoyage.org/wiki/Wikivoyage:Все_маршруты"]:
        if not any(s.get("url") == url for s in sources): fail(f"нет источника {url}")
    print("OK: validate_project passed")

if __name__ == "__main__":
    main()
