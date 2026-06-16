from __future__ import annotations

from .models import Signal
from .state_store import StateStore
from .config_loader import DATA_DIR, load_json
from .text_utils import semantic_fingerprint, title_similarity, topic_key


class DedupEngine:
    def __init__(self, state: StateStore | None = None):
        self.state = state or StateStore()

    def _history(self) -> list[dict]:
        pubs = self.state.publications()[-500:]
        previews = self.state.preview_history()[-500:]
        topic_memory = self.state.topic_memory()[-800:]
        rejected = load_json(DATA_DIR / "rejected_topics.json", default=[])[-500:]
        return pubs + previews + topic_memory + rejected

    def is_duplicate(self, signal: Signal) -> tuple[bool, str]:
        checked = self._history()
        urls = {p.get("url") for p in checked if p.get("url")}
        hashes = {p.get("semantic_hash") for p in checked if p.get("semantic_hash")}
        topic_keys = {p.get("topic_key") for p in checked if p.get("topic_key")}
        titles = [str(p.get("title", "")) for p in checked if p.get("title")]
        fp = signal.semantic_hash or semantic_fingerprint(signal.title, signal.city, signal.country, signal.genre, signal.angle)
        key = topic_key(signal.title, signal.city, signal.country, signal.genre, signal.angle)
        if signal.url and signal.url in urls:
            return True, "URL уже использовался"
        if fp and fp in hashes:
            return True, "смысловой hash уже был"
        if key and key in topic_keys:
            return True, "смысловой ключ темы уже был"
        normalized = signal.title.lower().strip()
        if any(normalized == t.lower().strip() for t in titles):
            return True, "заголовок уже был"
        for old in titles[-300:]:
            if title_similarity(signal.title, old) >= 0.72:
                return True, "слишком похожая тема уже была"
        return False, ""

    def filter(self, signals: list[Signal]) -> list[Signal]:
        out = []
        seen_keys: set[str] = set()
        for s in signals:
            key = topic_key(s.title, s.city, s.country, s.genre, s.angle)
            if key in seen_keys:
                continue
            dup, _ = self.is_duplicate(s)
            if not dup:
                out.append(s)
                seen_keys.add(key)
        return out
