from __future__ import annotations

import logging
import textwrap
from pathlib import Path
from urllib.parse import urlparse

import requests
from PIL import Image, ImageDraw, ImageFont

from .config_loader import MEDIA_DIR, env
from .models import EditorialBrief, PostVariant
from .text_utils import hash_text

log = logging.getLogger(__name__)


class MediaEngine:
    """
    Editorial media selector.

    Rules fixed in v5.4:
    - do not use Telegram source previews for channel pictures;
    - do not attach white "document-like" offer cards to flight deals;
    - for flight deals, first try a real recognizable destination photo;
    - if no good real photo is available, publish without media instead of a bad card;
    - cards are allowed only for non-flight fallback/manual informational posts.
    """

    def choose_media(self, brief: EditorialBrief, variant: PostVariant, media_query: str = "") -> str:
        # Flight deals need either a real destination photo or no image.
        # A weak white offer card looks like a document preview and damages the channel.
        if brief.genre == "flight_deal":
            query = self.flight_photo_query(brief, variant, media_query)
            pexels = self.fetch_pexels(query)
            if pexels:
                return pexels
            log.info("No real photo found for flight_deal; publishing without media instead of fallback card. query=%s", query)
            return ""

        # Telegram source pictures are not trusted: public previews often contain
        # blank wrappers, documents, screenshots, or unrelated channel cards.
        if self._source_media_allowed(brief) and self._looks_like_real_image_url(brief.signal.media_url):
            return brief.signal.media_url

        query = media_query or self.query_from_brief(brief, variant)
        pexels = self.fetch_pexels(query)
        if pexels:
            return pexels

        # Non-flight fallback: use a clear branded card. Never for flight_deal.
        return self.make_text_card(variant.title, brief.genre, brief.route_to or brief.city)

    def flight_photo_query(self, brief: EditorialBrief, variant: PostVariant, media_query: str = "") -> str:
        destination = brief.route_to or brief.city or brief.country
        if media_query and destination and destination.lower() in media_query.lower():
            return media_query
        if destination:
            return f"{destination} famous landmark city skyline travel"
        return "airplane window city skyline travel"

    def _source_media_allowed(self, brief: EditorialBrief) -> bool:
        source = brief.signal.raw.get("source", {}) if isinstance(brief.signal.raw, dict) else {}
        if not source.get("allow_source_media"):
            return False
        url = brief.signal.media_url or ""
        host = (urlparse(url).netloc or "").lower()
        if "telegram" in host or "t.me" in host:
            return False
        return True

    def _looks_like_real_image_url(self, url: str) -> bool:
        if not url:
            return False
        lower = url.lower()
        bad_hosts = ["t.me", "telegram", "web.telegram.org"]
        host = (urlparse(url).netloc or "").lower()
        if any(x in host for x in bad_hosts):
            return False
        # Accept common CDN/image URLs; reject obvious HTML/source wrappers.
        if any(lower.endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".webp"]):
            return True
        if any(x in lower for x in ["images", "photos", "cdn", "pexels", "unsplash"]):
            return True
        return False

    def query_from_brief(self, brief: EditorialBrief, variant: PostVariant) -> str:
        place = brief.route_to or brief.city or brief.country
        if place:
            genre_hint = {
                "destination_post": "famous landmark travel cityscape",
                "weekend_trip": "historic center travel street",
                "city_break": "city skyline landmark travel",
                "beach_trip": "beautiful beach sea resort",
                "hotel_post": "hotel travel interior exterior",
                "premium_hotel": "luxury hotel travel resort",
                "event_trip": "city landmark evening travel",
                "concert_trip": "city landmark evening travel",
            }.get(brief.genre, "famous landmark travel cityscape")
            return f"{place} {genre_hint}"
        return f"travel destination landmark {variant.title[:40]}"

    def fetch_pexels(self, query: str) -> str:
        key = env("PEXELS_API_KEY")
        if not key:
            return ""
        try:
            r = requests.get(
                "https://api.pexels.com/v1/search",
                params={"query": query, "orientation": "landscape", "per_page": 8},
                headers={"Authorization": key},
                timeout=10,
            )
            if r.status_code != 200:
                log.warning("Pexels non-200: %s %s", r.status_code, r.text[:120])
                return ""
            data = r.json()
            photos = data.get("photos") or []
            for photo in photos:
                src = photo.get("src", {})
                candidate = src.get("large2x") or src.get("large") or src.get("original") or ""
                if candidate and self._looks_like_real_image_url(candidate):
                    return candidate
        except Exception as exc:
            log.warning("Pexels failed: %s", exc)
        return ""

    def make_text_card(self, title: str, genre: str, place: str = "") -> str:
        subtitle = place or "идея для путешествия"
        return self._draw_card(title[:75], subtitle, "🌍 Мир на ладони")

    def _draw_card(self, title: str, subtitle: str, brand: str) -> str:
        MEDIA_DIR.mkdir(parents=True, exist_ok=True)
        path = MEDIA_DIR / f"card_{hash_text(title + subtitle)}.jpg"
        if path.exists():
            return str(path)

        # Dark travel-style fallback card for non-flight posts only.
        img = Image.new("RGB", (1280, 720), (24, 46, 62))
        draw = ImageDraw.Draw(img)
        try:
            font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 64)
            font_sub = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36)
            font_brand = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
        except Exception:
            font_title = font_sub = font_brand = None

        draw.rounded_rectangle((60, 60, 1220, 660), radius=42, fill=(31, 77, 96), outline=(116, 190, 188), width=4)
        draw.text((105, 105), brand, fill=(224, 246, 243), font=font_brand)
        y = 235
        for line in textwrap.wrap(title, width=26)[:3]:
            draw.text((105, y), line, fill=(255, 255, 255), font=font_title)
            y += 78
        draw.text((105, 560), subtitle, fill=(207, 234, 230), font=font_sub)
        img.save(path, quality=94)
        return str(path)
