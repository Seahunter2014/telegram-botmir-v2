from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class Signal:
    title: str
    summary: str
    url: str = ""
    source_key: str = ""
    source_name: str = ""
    topic_hint: str = ""
    published_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class Topic:
    key: str
    name: str
    content_type: str
    priority: int
    cooldown_posts: int
    cta_profile: str


@dataclass
class RankedSignal:
    signal: Signal
    topic: Topic
    score: int
    reasons: list[str]


@dataclass
class PostVariant:
    index: int
    title: str
    text: str
    cta_hint: str = ""
    risk_notes: list[str] = field(default_factory=list)
    quality_score: int = 0


@dataclass
class PostPackage:
    ranked: RankedSignal
    variants: list[PostVariant]
    buttons: list[dict[str, str]]
    media_path: str | None = None
    warnings: list[str] = field(default_factory=list)
