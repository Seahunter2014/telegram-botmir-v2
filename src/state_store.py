from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from .config_loader import DATA_DIR, load_json, save_json
from .models import Signal
from .text_utils import semantic_fingerprint, topic_key


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


    def ratings_path(self):
        return DATA_DIR / "post_ratings.json"

    def record_post_rating(self, post_id: str, score: int, title: str = "", source: str = "manual") -> dict[str, Any]:
        score = max(1, min(10, int(score)))
        data = load_json(self.ratings_path(), default=[])
        item = {
            "time": int(time.time()),
            "post_id": str(post_id),
            "score": score,
            "title": title,
            "source": source,
        }
        data.append(item)
        save_json(self.ratings_path(), data[-1000:])
        return item

    def post_ratings(self) -> list[dict[str, Any]]:
        return load_json(self.ratings_path(), default=[])

    def ratings_memory_text(self, limit: int = 8) -> str:
        ratings = self.post_ratings()[-200:]
        if not ratings:
            return "Оценок администратора пока нет."
        good = [r for r in ratings if int(r.get("score", 0) or 0) >= 8][-limit:]
        bad = [r for r in ratings if int(r.get("score", 0) or 0) <= 6][-limit:]
        lines = []
        if good:
            lines.append("Высоко оценённые посты — усиливать похожую подачу:")
            for r in reversed(good):
                lines.append(f"+ {r.get('score')}/10 · пост {r.get('post_id')} · {r.get('title') or 'без названия'}")
        if bad:
            lines.append("Низко оценённые посты — избегать похожей подачи и усиливать структуру/конкретику:")
            for r in reversed(bad):
                lines.append(f"- {r.get('score')}/10 · пост {r.get('post_id')} · {r.get('title') or 'без названия'}")
        return "\n".join(lines) if lines else "Оценки есть, но ярких успешных/провальных паттернов пока нет."


    def topic_memory_path(self):
        return DATA_DIR / "topic_memory.json"

    def topic_memory(self) -> list[dict[str, Any]]:
        return load_json(self.topic_memory_path(), default=[])

    def remember_topic_attempt(self, signal: Signal, reason: str = "attempt", title: str = "") -> None:
        data = self.topic_memory()
        key = topic_key(signal.title, signal.city, signal.country, signal.genre, signal.angle)
        data.append({
            "time": int(time.time()),
            "title": title or signal.title,
            "url": signal.url,
            "source_key": signal.source_key,
            "genre": signal.genre,
            "city": signal.city,
            "country": signal.country,
            "semantic_hash": signal.semantic_hash or semantic_fingerprint(signal.title, signal.city, signal.country, signal.genre, signal.angle),
            "topic_key": key,
            "reason": reason,
        })
        save_json(self.topic_memory_path(), data[-800:])

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
            "topic_key": topic_key(signal.title, signal.city, signal.country, signal.genre, signal.angle),
        })
        data["preview_history"] = history[-300:]
        self.save(data)

    def preview_history(self) -> list[dict[str, Any]]:
        return self.load().get("preview_history", []) or []
