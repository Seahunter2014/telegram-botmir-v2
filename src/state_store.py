import json
import time
from pathlib import Path
from typing import Any
from .config_loader import DATA_DIR, env

DEFAULT_STATE = {
    "autopost_enabled": False,
    "schedule_times": ["09:00", "14:00", "19:00"],
    "channels": [],
    "test_channel": "",
    "source_cursor": 0,
    "test_cursor": 0,
    "last_session_id": "",
    "published_urls": [],
    "published_titles": [],
    "published_text_hashes": [],
    "published_topics": [],
    "published_genres": [],
    "published_countries": [],
    "published_cities": [],
    "published_sources": [],
    "last_slot": "",
    "last_cta_type": "",
    "rejected_topics": [],
    "draft_sessions": {},
    "last_skip_reason": "",
    "analytics": [],
    "source_memory": {}
}

class StateStore:
    def __init__(self, path: Path | None = None):
        self.path = path or (DATA_DIR / "state.json")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.save(DEFAULT_STATE.copy())
        self.bootstrap_env_channels()

    def load(self) -> dict[str, Any]:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            data = DEFAULT_STATE.copy()
        merged = DEFAULT_STATE.copy()
        merged.update(data)
        return merged

    def save(self, data: dict[str, Any]) -> None:
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def get(self, key: str, default=None):
        return self.load().get(key, default)

    def set(self, key: str, value) -> None:
        data = self.load()
        data[key] = value
        self.save(data)

    def append_unique(self, key: str, value, limit: int = 500) -> None:
        data = self.load()
        arr = data.setdefault(key, [])
        if value and value not in arr:
            arr.append(value)
        data[key] = arr[-limit:]
        self.save(data)

    def bootstrap_env_channels(self) -> None:
        data = self.load()
        main = env("TELEGRAM_CHANNEL_ID")
        test = env("TEST_CHANNEL_ID") or main
        if main and main not in data.get("channels", []):
            data.setdefault("channels", []).append(main)
        if test:
            data["test_channel"] = data.get("test_channel") or test
        self.save(data)

    def new_session_id(self) -> str:
        return str(int(time.time() * 1000))[-10:]

    def store_draft_session(self, session_id: str, payload: dict[str, Any]) -> None:
        data = self.load()
        sessions = data.setdefault("draft_sessions", {})
        sessions[session_id] = payload
        data["last_session_id"] = session_id
        # keep last 20 sessions
        if len(sessions) > 20:
            for key in list(sessions.keys())[:-20]:
                sessions.pop(key, None)
        self.save(data)

    def get_draft_session(self, session_id: str) -> dict[str, Any] | None:
        return self.load().get("draft_sessions", {}).get(session_id)

    def latest_session_id(self) -> str:
        return self.get("last_session_id", "")

    def append_json_list(self, filename: str, payload: dict[str, Any], limit: int = 500) -> None:
        path = DATA_DIR / filename
        try:
            current = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
            if not isinstance(current, list):
                current = []
        except Exception:
            current = []
        current.append(payload)
        path.write_text(json.dumps(current[-limit:], ensure_ascii=False, indent=2), encoding="utf-8")

    def remember_source_pick(self, source_key: str, url: str = "", title: str = "") -> None:
        data = self.load()
        memory = data.setdefault("source_memory", {})
        memory[source_key] = {"url": url, "title": title, "ts": int(time.time())}
        data["source_memory"] = memory
        self.save(data)
