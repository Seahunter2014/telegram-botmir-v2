from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT_DIR / "configs"
DATA_DIR = ROOT_DIR / "data"
PROMPTS_DIR = ROOT_DIR / "prompts"
MEDIA_CACHE_DIR = ROOT_DIR / "media_cache"


def load_json(path: str | Path, default: Any = None) -> Any:
    p = Path(path)
    if not p.exists():
        if default is not None:
            return default
        raise FileNotFoundError(str(p))
    return json.loads(p.read_text(encoding="utf-8"))


def save_json(path: str | Path, data: Any) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(p)


def load_text(path: str | Path, default: str = "") -> str:
    p = Path(path)
    return p.read_text(encoding="utf-8") if p.exists() else default


def env(name: str, default: str = "") -> str:
    return os.getenv(name, default)


@dataclass
class Settings:
    telegram_bot_token: str
    telegram_admin_id: str
    telegram_channel_id: str
    test_channel_id: str
    openai_api_key: str
    openai_model: str
    openai_temperature: float
    pexels_api_key: str
    unsplash_access_key: str
    pixabay_api_key: str
    travelpayouts_api_token: str
    travelpayouts_marker: str
    schedule_timezone: str
    allow_fallback_autopublish: bool
    channel_public_url: str
    local_writer_fallback: bool


def load_settings() -> Settings:
    load_dotenv(ROOT_DIR / ".env")
    temp = env("OPENAI_TEMPERATURE", "0.85")
    try:
        temperature = float(temp)
    except ValueError:
        temperature = 0.85
    return Settings(
        telegram_bot_token=env("TELEGRAM_BOT_TOKEN"),
        telegram_admin_id=env("TELEGRAM_ADMIN_ID"),
        telegram_channel_id=env("TELEGRAM_CHANNEL_ID"),
        test_channel_id=env("TEST_CHANNEL_ID"),
        openai_api_key=env("OPENAI_API_KEY"),
        openai_model=env("OPENAI_MODEL", "gpt-4.1"),
        openai_temperature=temperature,
        pexels_api_key=env("PEXELS_API_KEY"),
        unsplash_access_key=env("UNSPLASH_ACCESS_KEY"),
        pixabay_api_key=env("PIXABAY_API_KEY"),
        travelpayouts_api_token=env("TRAVELPAYOUTS_API_TOKEN"),
        travelpayouts_marker=env("TRAVELPAYOUTS_MARKER", "98526"),
        schedule_timezone=env("SCHEDULE_TIMEZONE", "Europe/Moscow"),
        allow_fallback_autopublish=env("ALLOW_FALLBACK_AUTOPUBLISH", "true").lower() in {"1", "true", "yes", "on"},
        channel_public_url=env("TELEGRAM_CHANNEL_URL"),
        local_writer_fallback=env("LOCAL_WRITER_FALLBACK", "false").lower() in {"1", "true", "yes", "on"},
    )


def required_env_missing(settings: Settings) -> list[str]:
    missing = []
    if not settings.telegram_bot_token:
        missing.append("TELEGRAM_BOT_TOKEN")
    if not settings.telegram_admin_id:
        missing.append("TELEGRAM_ADMIN_ID")
    if not settings.telegram_channel_id:
        missing.append("TELEGRAM_CHANNEL_ID")
    if not settings.test_channel_id:
        missing.append("TEST_CHANNEL_ID")
    if not settings.openai_api_key:
        missing.append("OPENAI_API_KEY")
    return missing
