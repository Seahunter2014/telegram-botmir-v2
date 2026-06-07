from .models import PostVariant
from .text_utils import html_escape

class TelegramPostWriter:
    def format_caption(self, variant: PostVariant) -> str:
        title = html_escape(variant.title.strip())
        body = html_escape(variant.body.strip())
        cta = html_escape(variant.cta_text.strip())
        parts = [f"<b>{title}</b>", body]
        if cta:
            parts.append(cta)
        caption = "\n\n".join(p for p in parts if p)
        if len(caption) > 980:
            caption = caption[:940].rstrip() + "…"
        return caption

    def format_preview(self, variant: PostVariant) -> str:
        caption = self.format_caption(variant)
        footer = f"\n\n<i>Оценка: {variant.score}/100 · стиль: {html_escape(variant.style)}</i>"
        if len(caption + footer) < 3900:
            return caption + footer
        return caption
