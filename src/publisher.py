from pathlib import Path
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from .models import PostVariant
from .telegram_post_writer import TelegramPostWriter

class Publisher:
    def __init__(self, bot: Bot):
        self.bot = bot
        self.writer = TelegramPostWriter()

    def keyboard(self, variant: PostVariant) -> InlineKeyboardMarkup | None:
        rows = []
        for b in variant.buttons[:3]:
            if b.url:
                rows.append([InlineKeyboardButton(b.text, url=b.url)])
        return InlineKeyboardMarkup(rows) if rows else None

    async def publish_to_channel(self, channel_id: str, variant: PostVariant, media: str = ""):
        caption = self.writer.format_caption(variant)
        reply_markup = self.keyboard(variant)
        if media:
            if media.startswith("http"):
                await self.bot.send_photo(chat_id=channel_id, photo=media, caption=caption, parse_mode="HTML", reply_markup=reply_markup)
            elif Path(media).exists():
                with open(media, "rb") as f:
                    await self.bot.send_photo(chat_id=channel_id, photo=f, caption=caption, parse_mode="HTML", reply_markup=reply_markup)
            else:
                await self.bot.send_message(chat_id=channel_id, text=caption, parse_mode="HTML", reply_markup=reply_markup, disable_web_page_preview=False)
        else:
            await self.bot.send_message(chat_id=channel_id, text=caption, parse_mode="HTML", reply_markup=reply_markup, disable_web_page_preview=False)
