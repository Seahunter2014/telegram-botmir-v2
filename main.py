from __future__ import annotations

import os
from typing import Any


def _service_url(service: dict[str, Any]) -> str:
    if service.get("url_template"):
        marker = os.getenv(service.get("env_marker", "TRAVELPAYOUTS_MARKER"), "").strip()
        return service["url_template"].format(marker=marker or "98526")
    return service.get("url", "")


def buttons_for_topic(topic_key: str, configs: dict[str, Any], max_buttons: int = 3) -> list[dict[str, str]]:
    services_cfg = configs["services"]
    topics = {item["key"]: item for item in configs["topics"]["topics"]}
    profile = topics.get(topic_key, {}).get("cta_profile", "none_or_soft")
    service_keys = services_cfg.get("cta_profiles", {}).get(profile, [])
    services_by_key = {s["key"]: s for s in services_cfg.get("services", [])}
    result: list[dict[str, str]] = []
    for key in service_keys:
        service = services_by_key.get(key)
        if not service:
            continue
        url = _service_url(service)
        if not url:
            continue
        result.append({"text": service.get("button", service["name"]), "url": url, "service": service["name"], "category": service["category"]})
        if len(result) >= max_buttons:
            break
    return result


def cta_description(topic_key: str, configs: dict[str, Any]) -> str:
    buttons = buttons_for_topic(topic_key, configs)
    if not buttons:
        return "без прямой продажи; цель — реакции, сохранения и пересылки"
    names = ", ".join(b["service"] for b in buttons)
    return f"кнопки: {names}; текстовый CTA мягкий, без давления"
