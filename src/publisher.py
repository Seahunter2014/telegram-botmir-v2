from __future__ import annotations

from html import escape, unescape
from pathlib import Path
import re
from typing import Any

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode

from .offer_formatter import build_offer_line


def keyboard(buttons: list[dict]) -> InlineKeyboardMarkup | None:
    rows = [[InlineKeyboardButton(button["text"], url=button["url"])] for button in buttons[:3] if button.get("text") and button.get("url")]
    return InlineKeyboardMarkup(rows) if rows else None


def _plain_parts(variant: dict, plan: dict | None = None, signal: dict | None = None) -> list[str]:
    parts: list[str] = []
    title = (variant.get("title") or "").strip()
    if title:
        parts.append(title)
    offer_line = build_offer_line(plan or {}, signal or {})
    if offer_line:
        plain_offer = re.sub(r"</?a[^>]*>", "", offer_line)
        parts.append(unescape(plain_offer))
    text = (variant.get("text") or "").strip()
    if text:
        parts.append(text)
    cta = (variant.get("cta") or "").strip()
    if cta:
        parts.append(cta)
    return parts


def render_post(variant: dict, plan: dict | None = None, signal: dict | None = None) -> str:
    return "\n\n".join(_plain_parts(variant, plan, signal))[:3900]


def render_post_html(variant: dict, plan: dict | None = None, signal: dict | None = None) -> str:
    parts: list[str] = []
    title = (variant.get("title") or "").strip()
    if title:
        parts.append(f"<b>{escape(title)}</b>")
    offer_line = build_offer_line(plan or {}, signal or {})
    if offer_line:
        parts.append(offer_line)
    text = (variant.get("text") or "").strip()
    if text:
        escaped = escape(text).replace("\n", "\n")
        parts.append(escaped)
    cta = (variant.get("cta") or "").strip()
    if cta:
        parts.append(escape(cta))
    return "\n\n".join(parts).strip()[:3900]


async def publish_to_channel(
    bot: Any,
    channel_id: str,
    variant: dict,
    media: dict,
    plan: dict | None = None,
    signal: dict | None = None,
) -> bool:
    used = False
    html_text = render_post_html(variant, plan, signal)
    markup = keyboard(variant.get("buttons", []))

    if media.get("type") == "url" and media.get("value") and len(html_text) <= 1000:
        await bot.send_photo(
            chat_id=channel_id,
            photo=media["value"],
            caption=html_text,
            parse_mode=ParseMode.HTML,
            reply_markup=markup,
        )
        return True

    if media.get("type") == "file" and media.get("value") and Path(media["value"]).exists() and len(html_text) <= 1000:
        with Path(media["value"]).open("rb") as fh:
            await bot.send_photo(
                chat_id=channel_id,
                photo=fh,
                caption=html_text,
                parse_mode=ParseMode.HTML,
                reply_markup=markup,
            )
        return True

    if media.get("type") == "url" and media.get("value"):
        await bot.send_photo(chat_id=channel_id, photo=media["value"])
        used = True
    elif media.get("type") == "file" and media.get("value") and Path(media["value"]).exists():
        with Path(media["value"]).open("rb") as fh:
            await bot.send_photo(chat_id=channel_id, photo=fh)
        used = True

    await bot.send_message(
        chat_id=channel_id,
        text=html_text,
        parse_mode=ParseMode.HTML,
        reply_markup=markup,
        disable_web_page_preview=False,
    )
    return used
