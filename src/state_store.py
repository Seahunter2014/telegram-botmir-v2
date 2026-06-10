from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from .config_loader import DATA_DIR, load_json, save_json
from .models import Signal


class StateStore:
    def __init__(self, path: Path | None = None):
        self.path = path or (DATA_DIR / "state.json")

    def load(self) -> dict[str, Any]:
        return load_json(self.path, default={})

    def save(self, data: dict[str, Any]) -> None:
        save_json(self.path, data)

    def get(self, key: str, default: Any = None) -> Any:
        return self.load().get(key, default)

    def set(self, key: str, value: Any) -> None:
        data = self.load()
        data[key] = value
        self.save(data)

    def append_publication(self, item: dict[str, Any]) -> None:
        data = load_json(DATA_DIR / "publication_log.json", default=[])
        data.append(item)
        save_json(DATA_DIR / "publication_log.json", data[-500:])

    def publications(self) -> list[dict[str, Any]]:
        return load_json(DATA_DIR / "publication_log.json", default=[])

    def save_session(self, session: dict[str, Any]) -> None:
        data = self.load()
        sessions = data.setdefault("sessions", {})
        sessions[session["session_id"]] = session
        self.save(data)

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        return self.load().get("sessions", {}).get(session_id)

    def new_session_id(self) -> str:
        return f"s{int(time.time()*1000)}"

    def channels(self, fallback: str = "") -> list[str]:
        data = self.load()
        channels = data.get("channels") or []
        if isinstance(channels, str):
            channels = [channels]
        if not channels and fallback:
            channels = [fallback]
        return [c for c in channels if c]

    def next_test_index(self) -> int:
        data = self.load()
        idx = int(data.get("next_test_index", 0) or 0) + 1
        data["next_test_index"] = idx
        self.save(data)
        return idx

    def remember_preview(self, signal: Signal, title: str = "") -> None:
        data = self.load()
        history = data.setdefault("preview_history", [])
        history.append({
            "time": int(time.time()),
            "title": title or signal.title,
            "url": signal.url,
            "source_key": signal.source_key,
            "genre": signal.genre,
            "city": signal.city,
            "country": signal.country,
            "semantic_hash": signal.semantic_hash,
        })
        data["preview_history"] = history[-300:]
        self.save(data)

    def preview_history(self) -> list[dict[str, Any]]:
        return self.load().get("preview_history", []) or []
