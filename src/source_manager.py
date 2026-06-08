import logging
import re
from datetime import datetime, timezone
from typing import Iterable
import requests
from bs4 import BeautifulSoup
from .config_loader import read_json
from .models import Signal
from .text_utils import clean_text, hash_text

log = logging.getLogger(__name__)

class SourceManager:
    def __init__(self):
        self.sources = read_json("sources.json", [])
        self.fallback_signals = read_json("fallback_signals.json", [])

    def list_sources(self) -> list[dict]:
        return self.sources

    def fetch_signals(self, limit_per_source: int = 3, include_fallback: bool = False) -> list[Signal]:
        signals: list[Signal] = []
        for source in self.sources:
            if source.get("mode") == "manual":
                continue
            try:
                if source.get("method") == "telegram_public_html":
                    signals.extend(self._fetch_telegram(source, limit_per_source))
                else:
                    signals.extend(self._fetch_site(source, limit_per_source))
            except Exception as exc:
                log.warning("source failed %s: %s", source.get("key"), exc)
        if include_fallback and not signals:
            signals.extend(self._fallback())
        return signals

    def fetch_for_test(self, offset: int = 0, genre: str = "") -> Signal | None:
        signals = self.fetch_signals(limit_per_source=5, include_fallback=True)
        if genre:
            genre = genre.strip().lower()
            signals = [s for s in signals if genre in (" ".join(s.raw.get("genres", [])) + " " + s.text + " " + s.title).lower()]
        if not signals:
            return None
        idx = max(0, offset) % len(signals)
        return signals[idx]

    def _fetch_telegram(self, source: dict, limit: int) -> list[Signal]:
        url = source["url"]
        html = requests.get(url, timeout=12, headers={"User-Agent": "Mozilla/5.0"}).text
        soup = BeautifulSoup(html, "lxml")
        messages = soup.select(".tgme_widget_message")[: max(limit, 1)]
        result = []
        for msg in messages:
            text_el = msg.select_one(".tgme_widget_message_text")
            if not text_el:
                continue
            text = clean_text(text_el.get_text(" "))
            if len(text) < 40:
                continue
            link_el = msg.select_one("a.tgme_widget_message_date")
            link = link_el.get("href", "") if link_el else url
            title = text[:110]
            media_url = ""
            photo = msg.select_one("a.tgme_widget_message_photo_wrap")
            if photo and photo.get("style"):
                m = re.search(r"url\('([^']+)'\)", photo.get("style"))
                media_url = m.group(1) if m else ""
            result.append(Signal(
                id=hash_text(source["key"] + link + title),
                source_key=source["key"], source_name=source["name"], source_url=url,
                title=title, text=text, url=link, media_url=media_url,
                published_at="", raw={"source": source, "genres": source.get("genres", [])}
            ))
        return result

    def _fetch_site(self, source: dict, limit: int) -> list[Signal]:
        url = source["url"]
        html = requests.get(url, timeout=12, headers={"User-Agent": "Mozilla/5.0"}).text
        soup = BeautifulSoup(html, "lxml")
        result = []
        for a in soup.find_all("a", href=True):
            text = clean_text(a.get_text(" "))
            if len(text) < 25:
                continue
            href = a["href"]
            if href.startswith("/"):
                base = re.match(r"https?://[^/]+", url)
                href = (base.group(0) if base else "") + href
            if not href.startswith("http"):
                continue
            result.append(Signal(
                id=hash_text(source["key"] + href + text),
                source_key=source["key"], source_name=source["name"], source_url=url,
                title=text[:120], text=text, url=href,
                raw={"source": source, "genres": source.get("genres", [])}
            ))
            if len(result) >= limit:
                break
        return result

    def _fallback(self) -> list[Signal]:
        result = []
        for item in self.fallback_signals:
            result.append(Signal(
                id=hash_text(item["source_key"] + item["title"]),
                source_key=item["source_key"], source_name=item.get("source_name", item["source_key"]),
                source_url=item.get("source_url", ""), title=item["title"], text=item["text"],
                url=item.get("url", ""), raw=item
            ))
        return result
