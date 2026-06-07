from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from urllib.parse import urljoin, urlparse
import re

import requests
from bs4 import BeautifulSoup

from .signal_extractor import clean_text, make_signal
from .state_store import load_state, save_state, record_skip

HEADERS = {"User-Agent": "Mozilla/5.0 MirNaLadoniNewsroomBot/1.0"}


def fetch(url: str) -> str:
    response = requests.get(url, headers=HEADERS, timeout=15)
    response.raise_for_status()
    response.encoding = response.encoding or "utf-8"
    return response.text


def _extract_telegram_media_url(message: Any) -> str:
    photo_wrap = message.select_one(".tgme_widget_message_photo_wrap")
    if photo_wrap and photo_wrap.has_attr("style"):
        style = photo_wrap["style"]
        match = re.search(r"url\('([^']+)'\)", style)
        if match:
            return match.group(1)
    video = message.select_one("video")
    if video and video.get("src"):
        return video["src"]
    img = message.select_one("img")
    if img and img.get("src"):
        return img["src"]
    return ""


def parse_telegram(source: dict[str, Any], html: str) -> list[dict[str, Any]]:
    soup = BeautifulSoup(html, "lxml")
    out: list[dict[str, Any]] = []
    for message in soup.select(".tgme_widget_message")[-18:]:
        node = message.select_one(".tgme_widget_message_text")
        if not node:
            continue
        text = clean_text(node.get_text(" ", strip=True))
        if len(text) < 40:
            continue
        date_link = message.select_one("a.tgme_widget_message_date")
        url = date_link.get("href") if date_link else source["endpoint"]
        time_node = message.select_one("time")
        published_at = time_node.get("datetime") if time_node else ""
        signal = make_signal(source, text.split(". ")[0][:140], url, text, published_at)
        media_url = _extract_telegram_media_url(message)
        if media_url:
            signal["media_url"] = media_url
        out.append(signal)
    return out


def _same_domain(base_url: str, href: str) -> bool:
    base_host = urlparse(base_url).netloc
    target_host = urlparse(urljoin(base_url, href)).netloc
    return not target_host or target_host == base_host


def _looks_like_article_href(href: str) -> bool:
    low = href.lower()
    return not (
        low.startswith("#")
        or low.startswith("javascript:")
        or "/tag/" in low
        or "/tags/" in low
        or "/author/" in low
        or "/search" in low
        or "/category/" in low
        or "/cdn-cgi/" in low
    )


def parse_site_listing(source: dict[str, Any], html: str) -> list[dict[str, Any]]:
    soup = BeautifulSoup(html, "lxml")
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for link in soup.find_all("a", href=True):
        href = link.get("href") or ""
        title = clean_text(link.get_text(" ", strip=True))
        if len(title) < 24 or not _looks_like_article_href(href) or not _same_domain(source["endpoint"], href):
            continue
        full_url = urljoin(source["endpoint"], href)
        if full_url in seen:
            continue
        seen.add(full_url)
        out.append(make_signal(source, title[:160], full_url, title, ""))
        if len(out) >= 18:
            break
    if not out:
        title = clean_text(soup.title.get_text(" ", strip=True) if soup.title else source["name"])
        out.append(make_signal(source, title, source["endpoint"], title, ""))
    return out


def _article_title(soup: BeautifulSoup, fallback: str) -> str:
    for selector in ("meta[property='og:title']", "h1", "title"):
        node = soup.select_one(selector)
        if not node:
            continue
        if selector.startswith("meta"):
            content = clean_text(node.get("content", ""))
        else:
            content = clean_text(node.get_text(" ", strip=True))
        if len(content) >= 8:
            return content
    return fallback


def _article_media(soup: BeautifulSoup) -> str:
    og = soup.select_one("meta[property='og:image']")
    if og and og.get("content"):
        return clean_text(og["content"])
    img = soup.select_one("article img, main img, img")
    if img and img.get("src"):
        return clean_text(img["src"])
    return ""


def parse_single_article(source: dict[str, Any], html: str) -> list[dict[str, Any]]:
    soup = BeautifulSoup(html, "lxml")
    title = _article_title(soup, source["name"])
    paragraphs: list[str] = []
    for node in soup.select("article p, main p, .content p, .post p"):
        text = clean_text(node.get_text(" ", strip=True))
        if len(text) >= 50:
            paragraphs.append(text)
        if sum(len(x) for x in paragraphs) >= 1800:
            break
    article_text = clean_text(" ".join(paragraphs)) or title
    signal = make_signal(source, title, source["endpoint"], article_text, "")
    media_url = _article_media(soup)
    if media_url:
        signal["media_url"] = urljoin(source["endpoint"], media_url)
    return [signal]


def collect_from_source(source: dict[str, Any]) -> list[dict[str, Any]]:
    html = fetch(source["endpoint"])
    method = source.get("collection_method")
    if method == "telegram_public_html":
        return parse_telegram(source, html)
    if method == "single_article":
        return parse_single_article(source, html)
    return parse_site_listing(source, html)


def enabled_sources(bundle: Any) -> list[dict[str, Any]]:
    return [source for source in bundle.sources["sources"] if source.get("enabled") and source.get("mode") == "auto"]


def collect_signals(bundle: Any, max_sources: int = 7) -> list[dict[str, Any]]:
    sources = enabled_sources(bundle)
    if not sources:
        record_skip("source_collection_failed", "В sources.json нет активных auto-источников.")
        return []
    state = load_state()
    cursor = int(state.get("source_cursor", 0)) % max(1, len(sources))
    ordered = sources[cursor:] + sources[:cursor]
    all_items: list[dict[str, Any]] = []
    errors: list[str] = []
    for source in ordered[:max_sources]:
        try:
            all_items.extend(collect_from_source(source))
        except Exception as exc:
            errors.append(f"{source['key']}: {exc}")
    state["source_cursor"] = (cursor + max_sources) % max(1, len(sources))
    save_state(state)
    if not all_items:
        record_skip("source_collection_failed", "; ".join(errors[:5]), {"errors": errors})
    return all_items


def freshness_score(signal: dict[str, Any]) -> int:
    value = signal.get("published_at") or signal.get("collected_at")
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
        hours = (datetime.now(timezone.utc) - dt).total_seconds() / 3600
        return 20 if hours <= 24 else 15 if hours <= 72 else 10 if hours <= 168 else 3
    except Exception:
        return 10
