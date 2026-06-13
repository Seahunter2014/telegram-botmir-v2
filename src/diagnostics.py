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

    def _step_details(self, name: str) -> Any:
        for s in reversed(self.steps):
            if s.get("name") == name:
                return s.get("details")
        return None

    def admin_text(self) -> str:
        c = self.counters
        context = self._step_details("generation.context") or {}
        writer = self._step_details("ai_writer.generate") or {}
        quality = self._step_details("quality.gate") or {}
        media = self._step_details("media.find_or_generate") or {}
        cta = self._step_details("cta.apply") or {}
        publish = self._step_details("publisher.publish") or {}
        publication = self._step_details("publication.summary") or {}

        openai_state = "OK" if c.get("openai_ok") else ("ERROR" if c.get("openai_error") else "не проверен")
        lines = [
            f"🧭 Отчёт запуска: {self.run_id}",
            f"Старт: {self.started_at}",
            f"Итог: {self.result}",
            "",
            "🔎 Источники и выбор темы",
            f"Источников проверено: {c.get('sources_checked', 0)}",
            f"Работают: {c.get('sources_ok', 0)}",
            f"Ошибки источников: {c.get('source_errors', 0)}",
            f"Сигналов найдено: {c.get('signals_found', 0)}",
            f"После travel-фильтра: {c.get('after_guard', 0)}",
            f"После дедупликации: {c.get('after_dedup', 0)}",
            f"Кандидатов для GPT: {c.get('candidates', 0)}",
        ]

        if isinstance(context, dict) and context:
            lines += [
                "",
                "🧩 Brief",
                f"Источник: {context.get('source_name') or '-'}",
                f"Тема: {context.get('topic') or '-'}",
                f"Жанр: {context.get('genre') or '-'} · слот: {context.get('slot') or '-'} · score: {context.get('signal_score') or 0}",
                f"Угол: {context.get('editorial_angle') or '-'}",
                f"Польза: {context.get('practical_value') or '-'}",
            ]

        lines += [
            "",
            "🤖 Генерация",
            f"Генератор: {'OpenAI' if c.get('openai_ok') else ('OpenAI ERROR' if c.get('openai_error') else 'не проверен')}",
            f"Модель: {writer.get('model') if isinstance(writer, dict) else '-'}",
            f"Промт: {writer.get('prompt_file') if isinstance(writer, dict) else '-'}",
            f"OpenAI: {openai_state}",
            f"Постов от GPT: {c.get('gpt_variants', 0)}",
        ]

        if isinstance(quality, dict) and quality:
            lines += [
                "",
                "✅ Quality Gate",
                f"Качество: {quality.get('score', 0)}/100",
                f"Решение: {quality.get('decision', '-')}",
            ]
            if quality.get("rewrite_attempts") is not None:
                lines.append(f"Переписываний до прохода Quality Gate: {quality.get('rewrite_attempts')}")
            reasons = quality.get("reasons") or ""
            if reasons:
                lines.append(f"Причины оценки: {reasons}")
            warnings = quality.get("warnings") or []
            if warnings:
                lines.append("Предупреждения: " + "; ".join(str(x) for x in warnings[:5]))

        if isinstance(media, dict):
            lines += ["", "🖼 Медиа", f"Статус: {'найдено/создано' if media else 'нет'}"]
            if media.get("source"):
                lines.append(f"Источник медиа: {media.get('source')}")
            if media.get("query_used"):
                lines.append(f"Запрос: {media.get('query_used')}")

        if isinstance(cta, dict) and cta:
            buttons = cta.get("buttons") or []
            lines += ["", "🔘 Кнопки", "Кнопки: " + (", ".join(buttons) if buttons else "нет")]

        lines += ["", "📣 Публикация", f"Публикация: {c.get('published', 0)}"]
        if isinstance(publication, dict) and publication:
            ids = publication.get("post_ids") or []
            urls = publication.get("post_urls") or []
            lines.append(f"Номер поста: {ids[0] if ids else '-'}")
            lines.append(f"Оценка Quality Gate: {publication.get('score', 0)}/100")
            if urls:
                lines.append(f"Ссылка на пост: {urls[0]}")
            lines.append(f"Команда оценки: {publication.get('rating_command', '/rate НОМЕР_ПОСТА 10')}")
        if isinstance(publish, dict) and publish:
            lines.append("Результат каналов: " + ", ".join(f"{k}: {'OK' if v.get('ok') else 'ERROR'}" for k, v in publish.items()))

        if self.message:
            lines += ["", self.message]
        if self.source_errors:
            lines += ["", "Ошибки источников:"]
            for key, err in list(self.source_errors.items())[:8]:
                lines.append(f"• {key}: {err[:120]}")
        return "\n".join(lines)
