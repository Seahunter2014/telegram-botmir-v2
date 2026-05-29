from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import DATA_DIR

STATE_PATH = DATA_DIR / "state.json"

DEFAULT_STATE: dict[str, Any] = {
    "published": [],
    "tested": [],
    "rejected": [],
    "topic_cursor": 0,
    "source_cursor": 0,
    "pending_packages": {},
    "analytics": []
}


def load_state() -> dict[str, Any]:
    if not STATE_PATH.exists():
        save_state(DEFAULT_STATE.copy())
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except Exception:
        backup = STATE_PATH.with_suffix(".broken.json")
        STATE_PATH.replace(backup)
        save_state(DEFAULT_STATE.copy())
        return DEFAULT_STATE.copy()


def save_state(state: dict[str, Any]) -> None:
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def remember_event(kind: str, payload: dict[str, Any]) -> None:
    state = load_state()
    payload = dict(payload)
    payload["timestamp"] = datetime.now(timezone.utc).isoformat()
    state.setdefault(kind, []).append(payload)
    state[kind] = state[kind][-300:]
    save_state(state)


def recent_titles(limit: int = 80) -> set[str]:
    state = load_state()
    items = state.get("published", []) + state.get("tested", [])
    return {str(item.get("title", "")).strip().lower() for item in items[-limit:] if item.get("title")}


def save_pending(user_id: int, package_dict: dict[str, Any]) -> str:
    state = load_state()
    token = f"pkg_{user_id}_{int(datetime.now().timestamp())}"
    state.setdefault("pending_packages", {})[token] = package_dict
    save_state(state)
    return token


def get_pending(token: str) -> dict[str, Any] | None:
    return load_state().get("pending_packages", {}).get(token)
