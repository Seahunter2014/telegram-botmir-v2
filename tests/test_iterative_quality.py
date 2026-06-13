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
from src.models import PostVariant


async def run():
    pipe = EditorialPipeline(load_settings(), bot=None)
    calls = {"generate": 0, "improve": 0}

    async def fake_generate(brief):
        calls["generate"] += 1
        return [PostVariant(1, "bad", 0, "Слабый пост", "Короткий сплошной текст без структуры.", "", hashtags=["#travel"])], 1, []

    async def fake_improve(brief, previous, feedback, attempt):
        calls["improve"] += 1
        body = (
            "Летний перелёт может выглядеть выгодно, но итоговая цена зависит от дат, багажа и пересадок.\n\n"
            "──────✦──────\n\n"
            "✈️ **Что проверить перед покупкой**\n"
            "✅ даты вылета и возвращения;\n✅ багаж;\n✅ длительность пересадки;\n✅ условия возврата.\n\n"
            "💡 **Как не переплатить**\n"
            "Сравните соседние даты и 2–3 сервиса. Иногда сдвиг поездки на несколько дней заметно меняет итоговую цену.\n\n"
            "🗓 **Когда действовать**\n"
            "Если направление подходит, лучше включить уведомления и проверять тарифы до оплаты."
        )
        return [PostVariant(1, "improved", 0, "Билеты дешевле: как проверить цену перед покупкой", body, "Сравните соседние даты и условия багажа перед бронированием.", hashtags=["#мирналадони", "#авиабилеты", "#путешествия"])], 1, []

    pipe.writer.generate = fake_generate
    pipe.writer.improve = fake_improve
    prepared, report = await pipe.prepare_post()
    assert prepared is not None, report.admin_text()
    assert calls["improve"] >= 1, "низкое качество должно запускать переписывание"
    assert prepared.best_variant().score >= 85, prepared.best_variant().score
    print("OK: iterative quality")

if __name__ == "__main__":
    asyncio.run(run())
