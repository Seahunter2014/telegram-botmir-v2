from __future__ import annotations

from .config_loader import CONFIG_DIR, load_json


class SourceRegistry:
    def __init__(self):
        self.sources = load_json(CONFIG_DIR / "sources.json", default=[])

    def active_sources(self) -> list[dict]:
        return [s for s in self.sources if s.get("mode") in {"auto", "evergreen"}]

    def manual_sources(self) -> list[dict]:
        return [s for s in self.sources if s.get("mode") == "manual"]

    def by_key(self, key: str) -> dict | None:
        for s in self.sources:
            if s.get("key") == key:
                return s
        return None
