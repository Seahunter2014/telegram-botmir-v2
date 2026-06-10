from __future__ import annotations

from .config_loader import DATA_DIR, load_json, save_json
from .text_utils import now_iso


class AnalyticsStore:
    def __init__(self):
        self.path = DATA_DIR / "analytics.json"

    def record(self, event: str, payload: dict | None = None) -> None:
        data = load_json(self.path, default={"events": []})
        data.setdefault("events", []).append({"time": now_iso(), "event": event, "payload": payload or {}})
        save_json(self.path, data)
