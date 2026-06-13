from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from .models import Button, MediaAsset
from .telegram_post_writer import FormattedPost


class Publisher:
    def __init__(self, bot=None):
        self.bot = bot

    async def publish(self, channels: list[str], post: FormattedPost, buttons: list[Button] | None = None, media: MediaAsset | None = None, dry_run: bool = False) -> dict[str, Any]:
        results = {}
        for channel in channels:
            results[channel] = await self._publish_one(channel, post, buttons or [], media, dry_run)
        return results

    async def _publish_one(self, channel: str, post: FormattedPost, buttons: list[Button], media: MediaAsset | None, dry_run: bool) -> dict[str, Any]:
        if dry_run or not self.bot:
            return {"ok": True, "dry_run": True, "channel": channel, "parts": 2 if post.second_text else 1}
        markup_first = None if post.buttons_on_second else self._markup(buttons)
        markup_second = self._markup(buttons) if post.buttons_on_second else None
        try:
            if media and (media.path or media.url):
                first_message = await self._send_photo(channel, media, post.first_text, markup_first)
            else:
                first_message = await self._send_message(channel, post.first_text, markup_first)
            second_message = None
            if post.second_text:
                second_message = await self._send_message(channel, post.second_text, markup_second)
            post_id = getattr(first_message, "message_id", None)
            result = {"ok": True, "channel": channel}
            if post_id:
                result["post_id"] = post_id
                if isinstance(channel, str) and channel.startswith("@"):
                    result["post_url"] = f"https://t.me/{channel.lstrip('@')}/{post_id}"
            if second_message:
                result["parts"] = 2
                result["second_post_id"] = getattr(second_message, "message_id", None)
            return result
        except Exception as exc:
            try:
                first_message = await self._send_message(channel, post.first_text, None)
                if post.second_text:
                    await self._send_message(channel, post.second_text, None)
                result = {"ok": True, "channel": channel, "fallback": "text_without_buttons", "warning": str(exc)}
                post_id = getattr(first_message, "message_id", None)
                if post_id:
                    result["post_id"] = post_id
                    if isinstance(channel, str) and channel.startswith("@"):
                        result["post_url"] = f"https://t.me/{channel.lstrip('@')}/{post_id}"
                return result
            except Exception as exc2:
                return {"ok": False, "channel": channel, "error": f"{type(exc2).__name__}: {exc2}", "original_error": str(exc)}

    async def _send_message(self, channel: str, text: str, markup):
        return await self._retry(lambda: self.bot.send_message(chat_id=channel, text=text, parse_mode="HTML", reply_markup=markup, disable_web_page_preview=True))

    async def _send_photo(self, channel: str, media: MediaAsset, caption: str, markup):
        if media.path and Path(media.path).exists():
            with open(media.path, "rb") as f:
                return await self._retry(lambda: self.bot.send_photo(chat_id=channel, photo=f, caption=caption, parse_mode="HTML", reply_markup=markup))
        return await self._retry(lambda: self.bot.send_photo(chat_id=channel, photo=media.url, caption=caption, parse_mode="HTML", reply_markup=markup))

    async def _retry(self, func, attempts: int = 3):
        last = None
        for i in range(attempts):
            try:
                return await func()
            except Exception as exc:
                last = exc
                retry_after = getattr(exc, "retry_after", None)
                if retry_after:
                    await asyncio.sleep(float(retry_after) + 0.5)
                elif i < attempts - 1:
                    await asyncio.sleep(1.0 * (i + 1))
                else:
                    raise
        if last:
            raise last

    def _markup(self, buttons: list[Button]):
        try:
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        except Exception:
            return None
        rows = []
        for b in buttons:
            if b.url:
                rows.append([InlineKeyboardButton(text=b.text, url=b.url)])
            elif b.callback_data:
                rows.append([InlineKeyboardButton(text=b.text, callback_data=b.callback_data)])
        return InlineKeyboardMarkup(rows) if rows else None
