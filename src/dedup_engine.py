from __future__ import annotations

from .models import Signal
from .state_store import StateStore
from .text_utils import semantic_fingerprint


class DedupEngine:
    def __init__(self, state: StateStore | None = None):
        self.state = state or StateStore()

    def is_duplicate(self, signal: Signal) -> tuple[bool, str]:
        pubs = self.state.publications()[-300:]
        urls = {p.get("url") for p in pubs if p.get("url")}
        hashes = {p.get("semantic_hash") for p in pubs if p.get("semantic_hash")}
        titles = {str(p.get("title", "")).lower() for p in pubs}
        fp = signal.semantic_hash or semantic_fingerprint(signal.title, signal.city, signal.country, signal.genre, signal.angle)
        if signal.url and signal.url in urls:
            return True, "URL уже публиковался"
        if fp and fp in hashes:
            return True, "смысловой hash уже был"
        if signal.title.lower() in titles:
            return True, "заголовок уже был"
        return False, ""

    def filter(self, signals: list[Signal]) -> list[Signal]:
        out = []
        for s in signals:
            dup, _ = self.is_duplicate(s)
            if not dup:
                out.append(s)
        return out
