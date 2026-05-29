from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "configs"
PROMPTS_DIR = ROOT / "prompts"
DATA_DIR = ROOT / "data"
MEDIA_CACHE_DIR = ROOT / "media_cache"


def read_json(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8-sig")
    return json.loads(text)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_all_configs() -> dict[str, Any]:
    required = [
        "channel.json",
        "topics.json",
        "sources.json",
        "services.json",
        "editorial_policy.json",
    ]
    data: dict[str, Any] = {}
    for file_name in required:
        path = CONFIG_DIR / file_name
        if not path.exists():
            raise FileNotFoundError(f"Не найден обязательный конфиг: {path}")
        data[file_name.replace(".json", "")] = read_json(path)
    data["prompts"] = {
        "system": read_text(PROMPTS_DIR / "system_editor_ru.md"),
        "anti_template": read_text(PROMPTS_DIR / "anti_template_ru.md"),
        "genre_matrix": read_text(PROMPTS_DIR / "genre_matrix_ru.md"),
    }
    DATA_DIR.mkdir(exist_ok=True)
    MEDIA_CACHE_DIR.mkdir(exist_ok=True)
    return data
