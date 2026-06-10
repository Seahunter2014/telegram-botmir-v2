from __future__ import annotations

import hashlib
import html
import re
from datetime import datetime


def normalize_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip()


def clean_text(text: str) -> str:
    text = html.unescape(text or "")
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def slug(text: str, limit: int = 80) -> str:
    text = normalize_spaces(text).lower()
    text = re.sub(r"[^a-zа-я0-9]+", "-", text, flags=re.I).strip("-")
    return text[:limit] or "item"


def stable_hash(text: str) -> str:
    return hashlib.sha256(normalize_spaces(text).lower().encode("utf-8")).hexdigest()[:16]


def semantic_fingerprint(*parts: str) -> str:
    joined = " ".join(normalize_spaces(p).lower() for p in parts if p)
    joined = re.sub(r"[^a-zа-я0-9 ]+", " ", joined, flags=re.I)
    words = [w for w in joined.split() if len(w) > 3]
    return stable_hash(" ".join(words[:80]))


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def extract_price(text: str) -> str:
    m = re.search(r"(?:от\s*)?([0-9][0-9\s]{2,})(?:\s*)(₽|руб|р\.|€|\$)", text or "", re.I)
    if not m:
        return ""
    return f"{m.group(1).strip()} {m.group(2)}".replace("  ", " ")


def extract_dates(text: str) -> str:
    patterns = [r"\b\d{1,2}\s*(?:января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)\b", r"\b\d{1,2}[./-]\d{1,2}(?:[./-]\d{2,4})?\b", r"\b(?:летом|осенью|зимой|весной|на майские|на Новый год)\b"]
    hits=[]
    for p in patterns:
        hits += re.findall(p, text or "", re.I)
    return ", ".join(dict.fromkeys([str(x) for x in hits][:4]))


def split_sentences(text: str) -> list[str]:
    chunks = re.split(r"(?<=[.!?…])\s+", text.strip())
    return [c.strip() for c in chunks if c.strip()]


def safe_html(text: str) -> str:
    return html.escape(text or "", quote=False)
