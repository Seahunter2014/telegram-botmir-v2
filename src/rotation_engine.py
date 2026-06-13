from __future__ import annotations

from .models import Signal
from .state_store import StateStore


class RotationEngine:
    def __init__(self, state: StateStore | None = None):
        self.state = state or StateStore()

    def rank(self, signals: list[Signal], current_slot: str = "", test_index: int = 0) -> list[Signal]:
        pubs = self.state.publications()[-10:]
        last_sources = [p.get("source_key") for p in pubs[-2:]]
        last_genres = [p.get("genre") for p in pubs[-2:]]
        last_countries = [p.get("country") for p in pubs[-3:]]
        last_cities = [p.get("city") for p in pubs[-5:]]
        ranked = []
        for s in signals:
            score = s.score
            if s.source_key in last_sources:
                score -= 25
            if s.genre in last_genres:
                score -= 20
            if s.country and s.country in last_countries:
                score -= 12
            if s.city and s.city in last_cities:
                score -= 15
            if current_slot and s.slot == current_slot:
                score += 8
            if s.is_fallback:
                score -= 3
            ranked.append((score, s))
        ranked.sort(key=lambda x: x[0], reverse=True)
        ordered = [s for _, s in ranked]
        if test_index and ordered:
            # Для /test N показываем разные темы, а не первый источник пачкой.
            idx = max(0, test_index - 1) % len(ordered)
            ordered = ordered[idx:] + ordered[:idx]
        return ordered
