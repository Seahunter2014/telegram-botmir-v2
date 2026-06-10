from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class Button:
    text: str
    url: str = ""
    service_key: str = ""
    callback_data: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Signal:
    id: str
    source_key: str
    source_name: str
    source_url: str
    title: str
    text: str
    url: str
    published_at: str = ""
    raw: dict[str, Any] = field(default_factory=dict)
    city: str = ""
    country: str = ""
    price: str = ""
    dates: str = ""
    genre: str = ""
    slot: str = ""
    score: int = 0
    is_fallback: bool = False
    base_topic: str = ""
    angle: str = ""
    semantic_hash: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Brief:
    source_key: str
    source_name: str
    source_url: str
    topic: str
    genre: str
    slot: str
    city: str = ""
    country: str = ""
    price: str = ""
    dates: str = ""
    editorial_angle: str = ""
    target_emotion: str = ""
    main_fact: str = ""
    practical_value: str = ""
    cta_level: str = "soft"
    allowed_services: list[str] = field(default_factory=list)
    forbidden_claims: list[str] = field(default_factory=list)
    media_query_ru: str = ""
    media_query_en: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PostVariant:
    variant_id: int
    style: str
    score: int
    title: str
    body: str
    cta_text: str = ""
    buttons: list[Button] = field(default_factory=list)
    hashtags: list[str] = field(default_factory=list)
    why_it_works: str = ""
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["buttons"] = [b.to_dict() for b in self.buttons]
        return d

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "PostVariant":
        buttons = []
        for item in data.get("buttons", []) or []:
            if isinstance(item, dict):
                buttons.append(Button(**{k: item.get(k, "") for k in ["text", "url", "service_key", "callback_data"]}))
        warnings = data.get("warnings", [])
        if isinstance(warnings, str):
            warnings = [warnings] if warnings else []
        hashtags = data.get("hashtags", [])
        if isinstance(hashtags, str):
            hashtags = [x.strip() for x in hashtags.split() if x.strip().startswith("#")]
        return PostVariant(
            variant_id=int(data.get("variant_id", 1) or 1),
            style=str(data.get("style", "")),
            score=int(data.get("score", 0) or 0),
            title=str(data.get("title", "")),
            body=str(data.get("body", "")),
            cta_text=str(data.get("cta_text", "")),
            buttons=buttons,
            hashtags=hashtags if isinstance(hashtags, list) else [],
            why_it_works=str(data.get("why_it_works", "")),
            warnings=[str(x) for x in warnings if str(x).strip()] if isinstance(warnings, list) else [],
        )


@dataclass
class MediaAsset:
    path: str = ""
    url: str = ""
    kind: str = "photo"
    source: str = ""
    author: str = ""
    license_url: str = ""
    generated: bool = False
    query_used: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PreparedPost:
    session_id: str
    signal: Signal
    brief: Brief
    variants: list[PostVariant]
    best_variant_id: int
    media: MediaAsset = field(default_factory=MediaAsset)
    diagnostics: dict[str, Any] = field(default_factory=dict)

    def best_variant(self) -> PostVariant:
        for v in self.variants:
            if v.variant_id == self.best_variant_id:
                return v
        return self.variants[0]

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "signal": self.signal.to_dict(),
            "brief": self.brief.to_dict(),
            "variants": [v.to_dict() for v in self.variants],
            "best_variant_id": self.best_variant_id,
            "media": self.media.to_dict(),
            "diagnostics": self.diagnostics,
        }
