from .models import PostVariant

class EditorialPolisher:
    def polish(self, variant: PostVariant) -> PostVariant:
        # Лёгкая локальная чистка: не заменяет GPT, а убирает технические хвосты и лишние пробелы.
        variant.title = self._clean(variant.title).replace("**", "")
        variant.body = self._clean_multiline(variant.body)
        variant.cta_text = self._clean(variant.cta_text)
        return variant

    def _clean(self, text: str) -> str:
        return " ".join((text or "").split()).strip()

    def _clean_multiline(self, text: str) -> str:
        lines = [" ".join(line.split()).strip() for line in (text or "").splitlines()]
        lines = [line for line in lines if line]
        return "\n\n".join(lines)
