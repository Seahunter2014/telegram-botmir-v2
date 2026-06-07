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
    Chooses media by editorial meaning.

    Critical rules:
    - flight_deal always gets an offer card, not a random/blank Telegram image;
    - source images from Telegram are not trusted by default;
    - city/destination posts should use recognizable city/landmark query;
    - fallback is a branded card, not an empty source preview.
    """

    def choose_media(self, brief: EditorialBrief, variant: PostVariant, media_query: str = "") -> str:
        if brief.genre == "flight_deal":
            return self.make_offer_card(brief, variant)

        # Do NOT trust Telegram source photos by default: public HTML often returns
        # tiny/blank preview wrappers. Use source media only when explicitly whitelisted.
        if self._source_media_allowed(brief) and brief.signal.media_url:
            return brief.signal.media_url

        query = media_query or self.query_from_brief(brief, variant)
        pexels = self.fetch_pexels(query)
        if pexels:
            return pexels

        return self.make_text_card(variant.title, brief.genre, brief.route_to or brief.city)

    def _source_media_allowed(self, brief: EditorialBrief) -> bool:
        source = brief.signal.raw.get("source", {}) if isinstance(brief.signal.raw, dict) else {}
        if not source.get("allow_source_media"):
            return False
        # Even if allowed, never use Telegram media wrappers as channel illustration.
        url = brief.signal.media_url or ""
        host = (urlparse(url).netloc or "").lower()
        if "telegram" in host or "t.me" in host:
            return False
        return True

    def query_from_brief(self, brief: EditorialBrief, variant: PostVariant) -> str:
        place = brief.route_to or brief.city or brief.country
        if place:
            return f"{place} famous landmark travel cityscape"
        return f"travel destination landmark {variant.title[:40]}"

    def fetch_pexels(self, query: str) -> str:
        key = env("PEXELS_API_KEY")
        if not key:
            return ""
        try:
            r = requests.get(
                "https://api.pexels.com/v1/search",
                params={"query": query, "orientation": "landscape", "per_page": 5},
                headers={"Authorization": key},
                timeout=10,
            )
            data = r.json()
            photos = data.get("photos") or []
            for photo in photos:
                src = photo.get("src", {})
                candidate = src.get("large") or src.get("original") or ""
                if candidate:
                    return candidate
        except Exception as exc:
            log.warning("Pexels failed: %s", exc)
        return ""

    def make_offer_card(self, brief: EditorialBrief, variant: PostVariant) -> str:
        route_from = brief.route_from or "Город вылета"
        route_to = brief.route_to or "Направление"
        title = f"{route_from} → {route_to}"
        subtitle_parts = []
        if brief.date_text:
            subtitle_parts.append(brief.date_text)
        if brief.price:
            subtitle_parts.append(brief.price)
        subtitle = " · ".join(subtitle_parts) or "проверьте даты и условия"
        return self._draw_card(title, subtitle, "✈️ Мир на ладони")

    def make_text_card(self, title: str, genre: str, place: str = "") -> str:
        subtitle = place or "идея для путешествия"
        return self._draw_card(title[:75], subtitle, "🌍 Мир на ладони")

    def _draw_card(self, title: str, subtitle: str, brand: str) -> str:
        MEDIA_DIR.mkdir(parents=True, exist_ok=True)
        path = MEDIA_DIR / f"card_{hash_text(title + subtitle)}.jpg"
        if path.exists():
            return str(path)

        img = Image.new("RGB", (1280, 720), (238, 244, 248))
        draw = ImageDraw.Draw(img)
        try:
            font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 58)
            font_sub = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36)
            font_brand = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)
        except Exception:
            font_title = font_sub = font_brand = None

        draw.rounded_rectangle((70, 70, 1210, 650), radius=42, fill=(255, 255, 255), outline=(205, 215, 230), width=3)
        draw.text((110, 120), brand, fill=(30, 70, 105), font=font_brand)
        y = 250
        for line in textwrap.wrap(title, width=25)[:3]:
            draw.text((110, y), line, fill=(18, 30, 48), font=font_title)
            y += 72
        draw.text((110, 545), subtitle, fill=(70, 90, 110), font=font_sub)
        img.save(path, quality=94)
        return str(path)
