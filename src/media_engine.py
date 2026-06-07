import logging
import textwrap
from pathlib import Path
import requests
from PIL import Image, ImageDraw, ImageFont
from .config_loader import MEDIA_DIR, env
from .models import EditorialBrief, PostVariant
from .text_utils import hash_text

log = logging.getLogger(__name__)

class MediaEngine:
    def choose_media(self, brief: EditorialBrief, variant: PostVariant, media_query: str = "") -> str:
        # 1. Авиабилет/оффер — карточка. Так не будет случайной картинки.
        if brief.genre == "flight_deal":
            return self.make_offer_card(brief, variant)
        # 2. Если источник дал фото — используем его.
        if brief.signal.media_url:
            return brief.signal.media_url
        # 3. Pexels по редакционному запросу.
        query = media_query or self.query_from_brief(brief, variant)
        pexels = self.fetch_pexels(query)
        if pexels:
            return pexels
        # 4. Fallback-card.
        return self.make_text_card(variant.title, brief.genre)

    def query_from_brief(self, brief: EditorialBrief, variant: PostVariant) -> str:
        if brief.route_to:
            return f"{brief.route_to} city landmark travel"
        return f"{variant.title} travel landmark"

    def fetch_pexels(self, query: str) -> str:
        key = env("PEXELS_API_KEY")
        if not key:
            return ""
        try:
            r = requests.get(
                "https://api.pexels.com/v1/search",
                params={"query": query, "orientation": "landscape", "per_page": 1},
                headers={"Authorization": key}, timeout=10
            )
            data = r.json()
            photos = data.get("photos") or []
            if photos:
                return photos[0]["src"].get("large") or photos[0]["src"].get("original")
        except Exception as exc:
            log.warning("Pexels failed: %s", exc)
        return ""

    def make_offer_card(self, brief: EditorialBrief, variant: PostVariant) -> str:
        title = f"{brief.route_from or 'Город'} → {brief.route_to or 'Направление'}"
        subtitle = " · ".join(x for x in [brief.date_text, brief.price] if x) or "проверьте даты и условия"
        return self._draw_card(title, subtitle, "✈️ Мир на ладони")

    def make_text_card(self, title: str, genre: str) -> str:
        return self._draw_card(title[:70], "идея для путешествия", "🌍 Мир на ладони")

    def _draw_card(self, title: str, subtitle: str, brand: str) -> str:
        MEDIA_DIR.mkdir(exist_ok=True)
        path = MEDIA_DIR / f"card_{hash_text(title + subtitle)}.jpg"
        if path.exists():
            return str(path)
        img = Image.new("RGB", (1280, 720), (245, 247, 250))
        draw = ImageDraw.Draw(img)
        try:
            font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 58)
            font_sub = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36)
            font_brand = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)
        except Exception:
            font_title = font_sub = font_brand = None
        draw.rounded_rectangle((70, 70, 1210, 650), radius=40, fill=(255, 255, 255), outline=(220, 225, 235), width=3)
        draw.text((110, 120), brand, fill=(35, 60, 90), font=font_brand)
        y = 250
        for line in textwrap.wrap(title, width=26)[:3]:
            draw.text((110, y), line, fill=(20, 30, 45), font=font_title)
            y += 70
        draw.text((110, 545), subtitle, fill=(70, 90, 110), font=font_sub)
        img.save(path, quality=92)
        return str(path)
