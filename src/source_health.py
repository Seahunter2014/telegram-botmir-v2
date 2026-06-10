from __future__ import annotations

from .config_loader import DATA_DIR, load_json, save_json
from .text_utils import now_iso


class SourceHealthStore:
    def __init__(self):
        self.path = DATA_DIR / "source_health.json"

    def load(self) -> dict:
        return load_json(self.path, default={})

    def update(self, key: str, ok: bool, count: int = 0, error: str = "") -> None:
        data = self.load()
        data[key] = {"ok": ok, "count": count, "error": error, "updated_at": now_iso()}
        save_json(self.path, data)

    def bulk_update(self, items: dict[str, dict]) -> None:
        data = self.load()
        now = now_iso()
        for key, item in items.items():
            data[key] = {**item, "updated_at": now}
        save_json(self.path, data)

    def summary_text(self) -> str:
        data = self.load()
        if not data:
            return "Данных по источникам пока нет. Запустите /run_once или /test."
        lines = ["🛰 Источники:"]
        for key, item in data.items():
            mark = "✅" if item.get("ok") else "⚠️"
            err = item.get("error", "")
            cnt = item.get("count", 0)
            lines.append(f"{mark} {key}: {cnt} сигналов" + (f" — {err[:80]}" if err else ""))
        return "\n".join(lines)
