from __future__ import annotations

from .config_loader import CONFIG_DIR, DATA_DIR, load_json, save_json
from .models import Signal
from .text_utils import now_iso, semantic_fingerprint, stable_hash


class FallbackTopicEngine:
    def __init__(self):
        self.topics = load_json(CONFIG_DIR / "fallback_topics.json", default=[])
        self.history_path = DATA_DIR / "fallback_history.json"

    def generate(self, slot: str = "", index_offset: int = 0) -> Signal:
        history = load_json(self.history_path, default=[])
        used_pairs = {(h.get("base_topic"), h.get("angle")) for h in history[-200:]}
        if not self.topics:
            base = {"base_topic": "10 идей для путешествий, которые стоит сохранить", "category": "evergreen", "possible_angles": ["общий топ"], "preferred_genres": ["top_list"]}
        else:
            base = None
            start = index_offset % len(self.topics)
            ordered = self.topics[start:] + self.topics[:start]
            for topic in ordered:
                for angle in topic.get("possible_angles", []):
                    if (topic.get("base_topic"), angle) not in used_pairs:
                        base = {**topic, "selected_angle": angle}
                        break
                if base:
                    break
            if not base:
                topic = self.topics[start]
                angle = topic.get("possible_angles", ["новый угол"])[index_offset % len(topic.get("possible_angles", ["новый угол"]))]
                base = {**topic, "selected_angle": f"{angle}: новая версия"}
        angle = base.get("selected_angle") or (base.get("possible_angles") or ["общий угол"])[0]
        title = f"{base.get('base_topic')} — {angle}"
        text = f"Fallback-тема для travel-канала: {base.get('base_topic')}. Угол раскрытия: {angle}."
        genre = (base.get("preferred_genres") or ["top_list"])[0]
        signal = Signal(
            id=stable_hash(title + now_iso()),
            source_key="fallback_topics",
            source_name="Evergreen fallback",
            source_url="configs/fallback_topics.json",
            title=title,
            text=text,
            url="",
            published_at=now_iso(),
            genre=genre,
            slot=slot,
            is_fallback=True,
            base_topic=base.get("base_topic", ""),
            angle=angle,
            semantic_hash=semantic_fingerprint(base.get("base_topic", ""), angle),
            raw={"category": base.get("category", "evergreen"), "possible_angles": base.get("possible_angles", [])},
        )
        return signal

    def remember(self, signal: Signal, title: str) -> None:
        if not signal.is_fallback:
            return
        history = load_json(self.history_path, default=[])
        history.append({"base_topic": signal.base_topic, "angle": signal.angle, "title": title, "semantic_hash": signal.semantic_hash, "published_at": now_iso()})
        save_json(self.history_path, history[-500:])
