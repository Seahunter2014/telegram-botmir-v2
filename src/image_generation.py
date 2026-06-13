from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

from .config_loader import MEDIA_CACHE_DIR
from .text_utils import slug


class ImageGeneration:
    def generate(self, topic: str, filename_prefix: str = "travel") -> str:
        MEDIA_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        path = MEDIA_CACHE_DIR / f"{filename_prefix}_{slug(topic, 40)}.png"
        w, h = 1280, 720
        img = Image.new("RGB", (w, h), (30, 90, 140))
        draw = ImageDraw.Draw(img)
        for y in range(h):
            r = int(20 + 80 * y / h)
            g = int(90 + 80 * y / h)
            b = int(150 + 70 * y / h)
            draw.line((0, y, w, y), fill=(r, g, b))
        # sun
        draw.ellipse((880, 90, 1060, 270), fill=(255, 205, 120))
        # mountains
        draw.polygon([(0, 520), (250, 260), (520, 520)], fill=(45, 100, 95))
        draw.polygon([(300, 520), (610, 220), (920, 520)], fill=(35, 85, 105))
        draw.polygon([(720, 520), (980, 300), (1280, 520)], fill=(50, 110, 100))
        # sea foreground
        draw.rectangle((0, 520, w, h), fill=(20, 125, 155))
        for yy in range(550, 700, 35):
            draw.arc((100, yy-20, 1180, yy+40), 0, 180, fill=(220, 245, 250), width=3)
        # soft blur for premium look
        img = img.filter(ImageFilter.SMOOTH_MORE)
        img.save(path, "PNG")
        return str(path)
