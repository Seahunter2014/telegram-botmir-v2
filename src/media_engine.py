from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import urlencode

import requests
from PIL import Image, ImageDraw, ImageFont

from .config_loader import ROOT_DIR


def query(plan: dict, signal: dict) -> str:
    parts = [
        plan.get("city"),
        plan.get("country"),
        signal.get("route_to"),
        signal.get("hotel_name"),
        signal.get("event_name"),
        signal.get("title"),
    ]
    return " ".join([part for part in parts if part])[:120] or "travel"


def source_media(signal: dict) -> str:
    return (signal.get("media_url") or "").strip()


def pexels(plan: dict, signal: dict) -> str:
    key = os.getenv("PEXELS_API_KEY", "").strip()
    if not key:
        return ""
    try:
        response = requests.get(
            "https://api.pexels.com/v1/search?" + urlencode({"query": query(plan, signal), "per_page": 1, "orientation": "portrait"}),
            headers={"Authorization": key},
            timeout=10,
        )
        response.raise_for_status()
        photos = response.json().get("photos", [])
        if not photos:
            return ""
        return photos[0].get("src", {}).get("large2x") or photos[0].get("src", {}).get("large") or ""
    except Exception:
        return ""


def card(plan: dict, signal: dict) -> Path:
    out = ROOT_DIR / "data" / "media_cache"
    out.mkdir(parents=True, exist_ok=True)
    path = out / "fallback_card.jpg"
    img = Image.new("RGB", (1080, 1350), (245, 241, 232))
    draw = ImageDraw.Draw(img)
    try:
        big = ImageFont.truetype("DejaVuSans.ttf", 54)
        small = ImageFont.truetype("DejaVuSans.ttf", 36)
    except Exception:
        big = small = None
    title = (plan.get("main_fact") or signal.get("title") or "Мир на ладони")[:160]
    words = title.split()
    lines: list[str] = []
    current = ""
    for word in words:
        if len(current + " " + word) <= 26:
            current = (current + " " + word).strip()
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    draw.rectangle((60, 60, 1020, 1290), outline=(80, 80, 80), width=4)
    draw.text((100, 180), "Мир на ладони", fill=(30, 30, 30), font=small)
    draw.text((100, 320), "\n".join(lines[:8]), fill=(20, 20, 20), font=big, spacing=12)
    draw.text((100, 1120), plan.get("genre", "travel"), fill=(60, 60, 60), font=small)
    img.save(path, quality=92)
    return path


def choose_media(plan: dict, signal: dict, allow_fallback: bool = True) -> dict:
    direct = source_media(signal)
    if direct:
        return {"type": "url", "value": direct, "source": "source_media"}
    url = pexels(plan, signal)
    if url:
        return {"type": "url", "value": url, "source": "pexels"}
    if allow_fallback:
        return {"type": "file", "value": str(card(plan, signal)), "source": "fallback_card"}
    return {"type": "none", "value": "", "source": "none"}
