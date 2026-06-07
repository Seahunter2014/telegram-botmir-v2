from dataclasses import dataclass, field
from typing import Any

@dataclass
class Signal:
    id: str
    source_key: str
    source_name: str
    source_url: str
    title: str
    text: str
    url: str = ""
    published_at: str = ""
    media_url: str = ""
    raw: dict[str, Any] = field(default_factory=dict)

@dataclass
class EditorialBrief:
    signal: Signal
    genre: str
    slot: str
    score: int
    city: str = ""
    country: str = ""
    route_from: str = ""
    route_to: str = ""
    price: str = ""
    date_text: str = ""
    editorial_angle: str = ""
    target_emotion: str = ""
    allowed_services: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

@dataclass
class Button:
    text: str
    url: str
    service_key: str = ""

@dataclass
class PostVariant:
    variant_id: int
    style: str
    title: str
    body: str
    cta_text: str = ""
    buttons: list[Button] = field(default_factory=list)
    score: int = 0
    why_it_works: str = ""
    warnings: list[str] = field(default_factory=list)

@dataclass
class GeneratedPost:
    decision: str
    reject_reason: str
    genre: str
    slot: str
    editorial_angle: str
    target_emotion: str
    media_query: str
    media_requirements: str
    variants: list[PostVariant]
    best_variant_id: int = 1
