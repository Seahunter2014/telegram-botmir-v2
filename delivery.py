from __future__ import annotations

import os
import re
from datetime import datetime, timezone
from html import unescape
from typing import Any

import requests
from bs4 import BeautifulSoup

from .models import Signal

HEADERS = {"User-Agent": "Mozilla/5.0 mirnala-editorial-bot/1.0"}


def _clean(text: str) -> str:
    text = unescape(text or "")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _collect_telegram_html(source: dict[str, Any], limit: int = 5) -> list[Signal]:
    url = source.get("url", "")
    if not url:
        return []
    resp = requests.get(url, headers=HEADERS, timeout=12)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")
    posts = soup.select(".tgme_widget_message")[-limit:]
    signals: list[Signal] = []
    for post in posts:
        text_node = post.select_one(".tgme_widget_message_text")
        if not text_node:
            continue
        text = _clean(text_node.get_text(" "))
        if len(text) < 40:
            continue
        title = text[:140].strip(" .,—")
        link_node = post.select_one("a.tgme_widget_message_date")
        link = link_node.get("href", "") if link_node else url
        signals.append(Signal(title=title, summary=text[:700], url=link, source_key=source["key"], source_name=source["name"]))
    return signals


def _collect_site_listing(source: dict[str, Any], limit: int = 6) -> list[Signal]:
    url = source.get("url", "")
    if not url:
        return []
    resp = requests.get(url, headers=HEADERS, timeout=12)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")
    candidates: list[tuple[str, str]] = []
    for tag in soup.find_all(["h1", "h2", "h3", "a"]):
        text = _clean(tag.get_text(" "))
        if len(text) < 25 or len(text) > 180:
            continue
        href = tag.get("href", "") if tag.name == "a" else ""
        if href.startswith("/"):
            base = re.match(r"https?://[^/]+", url)
            href = (base.group(0) if base else "") + href
        candidates.append((text, href or url))
    seen: set[str] = set()
    signals: list[Signal] = []
    for title, link in candidates:
        norm = title.lower()
        if norm in seen:
            continue
        seen.add(norm)
        signals.append(Signal(title=title, summary=title, url=link, source_key=source["key"], source_name=source["name"]))
        if len(signals) >= limit:
            break
    return signals


def _fallback_signals(configs: dict[str, Any]) -> list[Signal]:
    result: list[Signal] = []
    for item in configs["sources"].get("fallback_signals", []):
        result.append(Signal(
            title=item["title"],
            summary=item["summary"],
            topic_hint=item.get("topic_hint", "destination_post"),
            source_key=item.get("source_key", "editorial_seed"),
            source_name="Редакционная заготовка",
            raw={"source_priority": 40, "roles": [item.get("topic_hint", "destination_post")]},
        ))
    return result


def collect_signals(configs: dict[str, Any], per_source_limit: int = 5) -> list[Signal]:
    if os.getenv("LIVE_COLLECTION_ENABLED", "true").lower() in {"0", "false", "no"}:
        return _fallback_signals(configs)
    signals: list[Signal] = []
    for source in configs["sources"].get("sources", []):
        if not source.get("enabled", True):
            continue
        try:
            if source.get("type") == "telegram_html":
                batch = _collect_telegram_html(source, per_source_limit)
            else:
                batch = _collect_site_listing(source, per_source_limit)
            for signal in batch:
                signal.raw["source_priority"] = int(source.get("priority", 50))
                signal.raw["roles"] = source.get("roles", [])
            signals.extend(batch)
        except Exception as exc:
            signals.append(Signal(
                title=f"Источник временно недоступен: {source.get('name', source.get('key'))}",
                summary=f"Сбор не удался: {exc}",
                source_key=source.get("key", "unknown"),
                source_name=source.get("name", "unknown"),
                raw={"source_priority": 1, "roles": []},
                published_at=datetime.now(timezone.utc),
            ))
    if not [s for s in signals if not s.title.startswith("Источник временно недоступен")]:
        signals.extend(_fallback_signals(configs))
    return signals
