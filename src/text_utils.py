import hashlib
import html
import re
from datetime import datetime

MONTHS_RU = {
    "января": "01", "февраля": "02", "марта": "03", "апреля": "04", "мая": "05", "июня": "06",
    "июля": "07", "августа": "08", "сентября": "09", "октября": "10", "ноября": "11", "декабря": "12",
}


def clean_text(text: str) -> str:
    text = html.unescape(text or "")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def normalize_title(text: str) -> str:
    text = clean_text(text).lower()
    text = re.sub(r"[^а-яa-z0-9ё\s]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def hash_text(text: str) -> str:
    return hashlib.sha256(normalize_title(text).encode("utf-8")).hexdigest()[:16]


def extract_price(text: str) -> str:
    patterns = [
        r"(?:от\s*)?(\d[\d\s]{2,})\s*(?:₽|руб|рублей|р\.)",
        r"(?:за\s*)(\d[\d\s]{2,})\s*(?:₽|руб|рублей|р\.)",
    ]
    for pattern in patterns:
        m = re.search(pattern, text, flags=re.IGNORECASE)
        if m:
            return m.group(1).replace(" ", "") + " ₽"
    return ""


def extract_date_text(text: str) -> str:
    m = re.search(r"\b(\d{1,2})\s+(января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)\b", text, re.I)
    if m:
        return f"{m.group(1)} {m.group(2).lower()}"
    m = re.search(r"\b(\d{1,2})[./-](\d{1,2})(?:[./-](\d{2,4}))?\b", text)
    if m:
        return m.group(0)
    return ""


def date_to_ddmm(date_text: str) -> str:
    if not date_text:
        return ""
    m = re.search(r"(\d{1,2})\s+([а-яё]+)", date_text.lower())
    if m and m.group(2) in MONTHS_RU:
        return f"{int(m.group(1)):02d}{MONTHS_RU[m.group(2)]}"
    m = re.search(r"(\d{1,2})[./-](\d{1,2})", date_text)
    if m:
        return f"{int(m.group(1)):02d}{int(m.group(2)):02d}"
    return ""


def first_sentence(text: str, limit: int = 140) -> str:
    text = clean_text(text)
    parts = re.split(r"(?<=[.!?])\s+", text)
    result = parts[0] if parts else text
    return result[:limit]


def html_escape(text: str) -> str:
    return html.escape(text or "", quote=False)
