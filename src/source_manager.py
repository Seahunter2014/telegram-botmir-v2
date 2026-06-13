from __future__ import annotations

import asyncio
import re
from typing import Any
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from .models import Signal
from .source_registry import SourceRegistry
from .source_health import SourceHealthStore
from .text_utils import clean_text, normalize_spaces, now_iso, semantic_fingerprint, stable_hash


class SourceManager:
    def __init__(self, registry: SourceRegistry | None = None, health: SourceHealthStore | None = None):
        self.registry = registry or SourceRegistry()
        self.health = health or SourceHealthStore()
        self.headers = {"User-Agent": "Mozilla/5.0 MirNaLadoniBot/6.2 (+https://t.me/NadoTurKrd)"}

    async def collect(self, limit_per_source: int = 4, total_timeout: int = 28) -> tuple[list[Signal], dict[str, str]]:
        import os
        if os.getenv("MIRNALA_SKIP_SOURCE_FETCH", "").lower() in {"1", "true", "yes"}:
            return [], {"sources": "source fetch skipped by MIRNALA_SKIP_SOURCE_FETCH"}
        sources = self.registry.active_sources()
        tasks = [self._fetch_source_async(src, limit_per_source) for src in sources]
        try:
            results = await asyncio.wait_for(asyncio.gather(*tasks, return_exceptions=True), timeout=total_timeout)
        except asyncio.TimeoutError:
            results = []
            errors = {s.get("key", "unknown"): "общий таймаут сбора источников" for s in sources}
            for k, e in errors.items():
                self.health.update(k, False, 0, e)
            return [], errors

        per_source: list[list[Signal]] = []
        errors: dict[str, str] = {}
        health_payload: dict[str, dict[str, Any]] = {}
        for src, result in zip(sources, results):
            key = src.get("key", "unknown")
            if isinstance(result, Exception):
                errors[key] = str(result)
                health_payload[key] = {"ok": False, "count": 0, "error": str(result)}
                per_source.append([])
            else:
                signals, err = result
                if err:
                    errors[key] = err
                health_payload[key] = {"ok": bool(signals), "count": len(signals), "error": err}
                per_source.append(signals)
        self.health.bulk_update(health_payload)
        return self._round_robin(per_source), errors

    async def _fetch_source_async(self, src: dict, limit: int) -> tuple[list[Signal], str]:
        return await asyncio.to_thread(self._fetch_source, src, limit)

    def _fetch_source(self, src: dict, limit: int) -> tuple[list[Signal], str]:
        url = self._normalize_url(src.get("url", ""), src.get("type", ""))
        timeout = int(src.get("timeout", 8) or 8)
        try:
            r = requests.get(url, timeout=timeout, headers=self.headers)
            r.raise_for_status()
            html = r.text
        except Exception as exc:
            return [], f"{type(exc).__name__}: {exc}"
        try:
            if src.get("type") == "telegram":
                signals = self._parse_telegram(src, url, html, limit)
            else:
                signals = self._parse_site(src, url, html, limit)
            return signals, "" if signals else "нет пригодных сигналов"
        except Exception as exc:
            return [], f"parse {type(exc).__name__}: {exc}"

    def _normalize_url(self, url: str, source_type: str) -> str:
        if source_type == "telegram" and "t.me/" in url and "/s/" not in url:
            return url.replace("https://t.me/", "https://t.me/s/").replace("http://t.me/", "https://t.me/s/")
        return url

    def _parse_telegram(self, src: dict, url: str, html: str, limit: int) -> list[Signal]:
        soup = BeautifulSoup(html, "lxml")
        messages = soup.select(".tgme_widget_message")
        out: list[Signal] = []
        for msg in messages[-30:]:
            text_el = msg.select_one(".tgme_widget_message_text")
            if not text_el:
                continue
            text = clean_text(text_el.get_text("\n", strip=True))
            if len(text) < 35:
                continue
            link_el = msg.select_one("a.tgme_widget_message_date")
            link = link_el.get("href", url) if link_el else url
            title = self._make_title(text)
            out.append(self._signal(src, title, text, link))
            if len(out) >= limit:
                break
        return out

    def _parse_site(self, src: dict, url: str, html: str, limit: int) -> list[Signal]:
        soup = BeautifulSoup(html, "lxml")
        out: list[Signal] = []
        seen: set[str] = set()
        for a in soup.find_all("a", href=True):
            text = normalize_spaces(a.get_text(" ", strip=True))
            if len(text) < 28 or len(text) > 180:
                continue
            href = urljoin(url, a.get("href", ""))
            if href in seen or href.startswith("javascript:"):
                continue
            seen.add(href)
            title = text
            out.append(self._signal(src, title, text, href))
            if len(out) >= limit:
                break
        if not out:
            title = soup.title.get_text(" ", strip=True) if soup.title else src.get("name", "Travel source")
            out.append(self._signal(src, title, title, url))
        return out

    def _signal(self, src: dict, title: str, text: str, url: str) -> Signal:
        fp = semantic_fingerprint(src.get("key", ""), title, text)
        genre = ""
        genres = src.get("genres") or []
        if genres:
            genre = genres[0]
        return Signal(
            id=stable_hash(src.get("key", "") + url + title),
            source_key=src.get("key", ""),
            source_name=src.get("name", src.get("key", "")),
            source_url=src.get("url", ""),
            title=title,
            text=text,
            url=url,
            published_at=now_iso(),
            raw={"source_type": src.get("type"), "role": src.get("role"), "priority": src.get("priority")},
            genre=genre,
            semantic_hash=fp,
        )

    def _make_title(self, text: str) -> str:
        text = re.sub(r"\s+", " ", text).strip()
        first = re.split(r"[\n.!?]", text)[0].strip()
        return first[:120] if first else text[:120]

    def _round_robin(self, buckets: list[list[Signal]]) -> list[Signal]:
        out: list[Signal] = []
        max_len = max((len(b) for b in buckets), default=0)
        for i in range(max_len):
            for bucket in buckets:
                if i < len(bucket):
                    out.append(bucket[i])
        return out
