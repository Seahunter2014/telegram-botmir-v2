import logging
import re
from collections import defaultdict, deque
from typing import Iterable
import requests
from bs4 import BeautifulSoup
from .config_loader import read_json
from .models import Signal
from .text_utils import clean_text, hash_text

log = logging.getLogger(__name__)

# Редакционный цикл для /test N: тесты должны показывать разные типы тем,
# а не первые несколько постов одного источника.
TEST_GENRE_CYCLE = [
    "destination_post",
    "flight_deal",
    "practical_travel",
    "event_trip",
    "tour_offer",
    "hotel_post",
    "weekend_trip",
    "visa_or_residence",
    "activities_post",
    "inspiration_story",
]


class SourceManager:
    def __init__(self):
        self.sources = read_json("sources.json", [])
        self.fallback_signals = read_json("fallback_signals.json", [])

    def list_sources(self) -> list[dict]:
        return self.sources

    def fetch_signals(self, limit_per_source: int = 3, include_fallback: bool = False) -> list[Signal]:
        """
        Returns signals in an editorial round-robin order by source.

        IMPORTANT: the old version returned all Vandrouki posts first, then the next source.
        That broke the TZ: tests and autoposting could get stuck on one source/genre.
        Now we fetch buckets by source and interleave them:
        source1 post1, source2 post1, source3 post1, ..., source1 post2, source2 post2...
        """
        buckets: list[list[Signal]] = []
        for source in self.sources:
            if source.get("mode") == "manual":
                continue
            try:
                if source.get("method") == "telegram_public_html":
                    bucket = self._fetch_telegram(source, limit_per_source)
                else:
                    bucket = self._fetch_site(source, limit_per_source)
                if bucket:
                    buckets.append(bucket)
            except Exception as exc:
                log.warning("source failed %s: %s", source.get("key"), exc)

        signals = self._round_robin(buckets)

        if include_fallback and not signals:
            signals.extend(self._fallback())
        return signals

    def fetch_for_test(self, offset: int = 0, genre: str = "") -> Signal | None:
        """
        Test mode must demonstrate DIFFERENT editorial scenarios.

        /test 1, /test 2, /test 3 should not simply walk through the first
        source. They should rotate sources and genres according to TEST_GENRE_CYCLE.
        """
        signals = self.fetch_signals(limit_per_source=6, include_fallback=True)
        if not signals:
            return None

        # Keep only distinct URLs/titles to avoid repeated topics.
        signals = self._dedupe_signals(signals)

        genre = (genre or "").strip().lower()
        if genre:
            filtered = [s for s in signals if self._matches_genre_hint(s, genre)]
            return filtered[max(0, offset) % len(filtered)] if filtered else None

        # For numeric /test N use a genre cycle first.
        target_genre = TEST_GENRE_CYCLE[max(0, offset) % len(TEST_GENRE_CYCLE)]
        matching = [s for s in signals if self._matches_genre_hint(s, target_genre)]
        if matching:
            # Also rotate within same genre if there are many matching items.
            return matching[(max(0, offset) // len(TEST_GENRE_CYCLE)) % len(matching)]

        # Fallback: return N-th signal from already source-diversified list.
        return signals[max(0, offset) % len(signals)]

    def _round_robin(self, buckets: list[list[Signal]]) -> list[Signal]:
        queues = [deque(bucket) for bucket in buckets if bucket]
        result: list[Signal] = []
        while any(queues):
            for q in queues:
                if q:
                    result.append(q.popleft())
        return result

    def _dedupe_signals(self, signals: list[Signal]) -> list[Signal]:
        seen: set[str] = set()
        result: list[Signal] = []
        for signal in signals:
            fp = signal.url or hash_text(signal.title + "\n" + signal.text[:300])
            if fp in seen:
                continue
            seen.add(fp)
            result.append(signal)
        return result

    def _matches_genre_hint(self, signal: Signal, genre: str) -> bool:
        haystack = " ".join([
            signal.title,
            signal.text,
            " ".join(signal.raw.get("genres", [])),
            " ".join(signal.raw.get("source", {}).get("genres", [])),
        ]).lower()
        g = genre.lower()
        if g in haystack:
            return True
        if g == "flight_deal":
            return any(w in haystack for w in ["рейс", "перел", "билет", "авиа", "₽", "руб"])
        if g == "tour_offer":
            return any(w in haystack for w in ["тур", "all inclusive", "все включ", "пакет"])
        if g == "hotel_post":
            return any(w in haystack for w in ["отель", "гостиниц", "resort", "villa", "вилла"])
        if g == "event_trip":
            return any(w in haystack for w in ["концерт", "фестиваль", "выстав", "событ", "билет на событие"])
        if g == "practical_travel":
            return any(w in haystack for w in ["багаж", "аэропорт", "пересад", "страхов", "лайфхак", "ручная кладь"])
        if g == "visa_or_residence":
            return any(w in haystack for w in ["виза", "внж", "границ", "паспорт", "консуль", "документ"])
        if g == "destination_post":
            return any(w in haystack for w in ["город", "маршрут", "куда поехать", "путеше", "мест", "пляж", "море"])
        if g == "weekend_trip":
            return any(w in haystack for w in ["выходн", "2 дня", "3 дня", "уикенд", "weekend"])
        if g == "inspiration_story":
            return any(w in haystack for w in ["красив", "атмосфер", "закат", "место", "вдохнов"])
        return False

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
            # Не доверяем Telegram preview-photo как финальному медиа: media_engine сам решает,
            # брать ли фото, искать Pexels или публиковать без картинки.
            result.append(Signal(
                id=hash_text(source["key"] + link + title),
                source_key=source["key"], source_name=source["name"], source_url=url,
                title=title, text=text, url=link, media_url="",
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
