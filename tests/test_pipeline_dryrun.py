from pathlib import Path
import asyncio
import os
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

os.environ.setdefault("TELEGRAM_BOT_TOKEN", "dummy")
os.environ.setdefault("TELEGRAM_ADMIN_ID", "1")
os.environ.setdefault("TELEGRAM_CHANNEL_ID", "@dummy")
os.environ.setdefault("TEST_CHANNEL_ID", "@dummy_test")
os.environ.setdefault("ALLOW_FALLBACK_AUTOPUBLISH", "true")
os.environ.setdefault("LOCAL_WRITER_FALLBACK", "false")
os.environ.setdefault("MIRNALA_SKIP_SOURCE_FETCH", "true")
os.environ.setdefault("OPENAI_API_KEY", "test-key")

from src.pipeline import EditorialPipeline
from src.config_loader import load_settings


async def run():
    pipe = EditorialPipeline(load_settings(), bot=None)

    async def fake_generate(brief):
        from src.models import PostVariant
        body = (
            "Это тестовый редакционный пост, который имитирует успешный ответ OpenAI.\n\n"
            "──────✦──────\n\n"
            "📌 Конкретика: тема раскрыта без локального fallback-генератора.\n\n"
            "💡 Польза: читатель получает понятный следующий шаг и проверяет детали перед поездкой."
        )
        return [PostVariant(1, "тест OpenAI", 92, "Тестовый пост OpenAI", body, "Проверьте детали перед бронированием.", hashtags=["#мирналадони", "#travel"])], 1, []

    pipe.writer.generate = fake_generate
    prepared, result, report = await pipe.run_once(channels=["@dry_run"], dry_run=True)
    assert prepared is not None, report.admin_text()
    assert result.get("@dry_run", {}).get("ok"), result
    assert report.result == "published", report.admin_text()
    print("OK: pipeline dryrun")

if __name__ == "__main__": asyncio.run(run())
