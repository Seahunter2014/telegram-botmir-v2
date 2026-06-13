from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.models import Brief, PostVariant
from src.telegram_post_writer import TelegramPostWriter


def main():
    body = "\n\n".join(["Абзац с полезной информацией о путешествии, сезоне, маршруте и бюджете." for _ in range(80)])
    v = PostVariant(1,"test",90,"Очень длинный пост",body,"Сохраните пост",hashtags=["#мирналадони","#travel"])
    brief = Brief(source_key="x", source_name="x", source_url="", topic="x", genre="route", slot="morning")
    post = TelegramPostWriter().format(v, brief, with_media=True)
    assert post.second_text, "должна быть вторая часть"
    assert "Продолжение следует 👇" in post.first_text, "нет фразы продолжения"
    assert "#мирналадони" in post.second_text, "хештеги должны быть во второй части"
    print("OK: split")

if __name__ == "__main__": main()
