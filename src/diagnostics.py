from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

from .text_utils import now_iso


@dataclass
class RunReport:
    run_id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    started_at: str = field(default_factory=now_iso)
    finished_at: str = ""
    steps: list[dict[str, Any]] = field(default_factory=list)
    counters: dict[str, int] = field(default_factory=dict)
    source_errors: dict[str, str] = field(default_factory=dict)
    result: str = "started"
    message: str = ""

    def step(self, name: str, status: str = "ok", details: Any = None) -> None:
        self.steps.append({"time": now_iso(), "name": name, "status": status, "details": details})

    def count(self, key: str, value: int) -> None:
        self.counters[key] = value

    def finish(self, result: str, message: str = "") -> None:
        self.finished_at = now_iso()
        self.result = result
        self.message = message

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "steps": self.steps,
            "counters": self.counters,
            "source_errors": self.source_errors,
            "result": self.result,
            "message": self.message,
        }

    def admin_text(self) -> str:
        c = self.counters
        lines = [
            f"🧭 Отчёт запуска: {self.run_id}",
            f"Старт: {self.started_at}",
            f"Итог: {self.result}",
            "",
            f"Источников проверено: {c.get('sources_checked', 0)}",
            f"Работают: {c.get('sources_ok', 0)}",
            f"Ошибки источников: {c.get('source_errors', 0)}",
            f"Сигналов найдено: {c.get('signals_found', 0)}",
            f"После travel-фильтра: {c.get('after_guard', 0)}",
            f"После дедупликации: {c.get('after_dedup', 0)}",
            f"Кандидатов для GPT: {c.get('candidates', 0)}",
            f"GPT: {c.get('gpt_variants', 0)} вариантов",
            f"Медиа: {c.get('media', 0)}",
            f"Публикация: {c.get('published', 0)}",
        ]
        if self.message:
            lines += ["", self.message]
        if self.source_errors:
            lines += ["", "Ошибки источников:"]
            for key, err in list(self.source_errors.items())[:8]:
                lines.append(f"• {key}: {err[:120]}")
        return "\n".join(lines)
