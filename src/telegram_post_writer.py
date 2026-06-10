from __future__ import annotations

import re
from dataclasses import dataclass

from .models import Brief, PostVariant
from .text_utils import safe_html, split_sentences


@dataclass
class FormattedPost:
    first_text: str
    second_text: str = ""
    buttons_on_second: bool = False


class TelegramPostWriter:
    PHOTO_CAPTION_LIMIT = 950
    MESSAGE_LIMIT = 3900
    SPLIT_PHRASE = "Продолжение следует 👇"

    def format(self, variant: PostVariant, brief: Brief, with_media: bool = False) -> FormattedPost:
        title = self._format_title(variant.title)
        body = self._format_body(variant.body)
        cta = self._format_cta(variant.cta_text)
        tags = self._format_hashtags(variant.hashtags)
        full = "\n\n".join(x for x in [title, body, cta, tags] if x).strip()
        full = self._remove_service_words(full)
        if with_media and len(full) > self.PHOTO_CAPTION_LIMIT:
            return self._split_for_photo(full)
        if not with_media and len(full) > self.MESSAGE_LIMIT:
            return self._split_for_message(full)
        return FormattedPost(first_text=full)

    def preview(self, variant: PostVariant, brief: Brief) -> str:
        formatted = self.format(variant, brief, with_media=False)
        text = formatted.first_text + (("\n\n" + formatted.second_text) if formatted.second_text else "")
        warnings = "\n".join(f"⚠️ {w}" for w in variant.warnings[:4])
        return text + ("\n\n" + warnings if warnings else "")

    def _format_title(self, title: str) -> str:
        title = re.sub(r"\*+", "", title).strip()
        return f"<b>{safe_html(title)}</b>"

    def _format_body(self, body: str) -> str:
        body = body.strip()
        body = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", body)
        body = re.sub(r"\*(.+?)\*", r"<i>\1</i>", body)
        # Escape only untagged angle brackets.
        body = body.replace("<b>", "§B§").replace("</b>", "§/B§").replace("<i>", "§I§").replace("</i>", "§/I§")
        body = safe_html(body)
        body = body.replace("§B§", "<b>").replace("§/B§", "</b>").replace("§I§", "<i>").replace("§/I§", "</i>")
        return body

    def _format_cta(self, cta: str) -> str:
        if not cta:
            return ""
        return "💬 <b>Что дальше</b>\n" + safe_html(cta.strip())

    def _format_hashtags(self, tags: list[str]) -> str:
        clean = []
        for tag in tags or []:
            tag = tag.strip()
            if tag and tag.startswith("#"):
                clean.append(tag)
        if not clean:
            clean = ["#мирналадони", "#турджин", "#Туры", "#travel"]
        return " ".join(dict.fromkeys(clean[:7]))

    def _remove_service_words(self, text: str) -> str:
        for word in ["CTA", "Лид", "лид", "Визуал", "визуал", "Подзаголовок", "подзаголовок"]:
            text = text.replace(word, "")
        return re.sub(r"\n{3,}", "\n\n", text).strip()

    def _split_for_photo(self, full: str) -> FormattedPost:
        limit = self.PHOTO_CAPTION_LIMIT - len(self.SPLIT_PHRASE) - 10
        first, second = self._split_text(full, limit)
        first = first.rstrip() + f"\n\n{self.SPLIT_PHRASE}"
        second = "<b>Продолжение</b>\n\n" + second.lstrip()
        return FormattedPost(first_text=first, second_text=second, buttons_on_second=True)

    def _split_for_message(self, full: str) -> FormattedPost:
        first, second = self._split_text(full, self.MESSAGE_LIMIT - len(self.SPLIT_PHRASE) - 10)
        first = first.rstrip() + f"\n\n{self.SPLIT_PHRASE}"
        second = "<b>Продолжение</b>\n\n" + second.lstrip()
        return FormattedPost(first_text=first, second_text=second, buttons_on_second=True)

    def _split_text(self, full: str, limit: int) -> tuple[str, str]:
        if len(full) <= limit:
            return full, ""
        paragraphs = full.split("\n\n")
        first_parts = []
        current = 0
        for p in paragraphs:
            add = len(p) + (2 if first_parts else 0)
            if current + add <= limit:
                first_parts.append(p)
                current += add
            else:
                break
        if first_parts:
            first = "\n\n".join(first_parts)
            second = full[len(first):].strip()
            if second:
                return first, second
        sentences = split_sentences(full)
        first = ""
        rest = []
        for s in sentences:
            if len(first) + len(s) + 1 <= limit:
                first += (" " if first else "") + s
            else:
                rest.append(s)
        if first and rest:
            return first, " ".join(rest)
        return full[:limit].rsplit(" ", 1)[0], full[len(full[:limit].rsplit(" ", 1)[0]):].strip()
