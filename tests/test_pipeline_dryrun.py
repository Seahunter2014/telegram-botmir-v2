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
os.environ.setdefault("LOCAL_WRITER_FALLBACK", "true")
os.environ.setdefault("MIRNALA_SKIP_SOURCE_FETCH", "true")

from src.pipeline import EditorialPipeline
from src.config_loader import load_settings


async def run():
    pipe = EditorialPipeline(load_settings(), bot=None)
    # Чтобы тест не зависел от интернета: принудительно подготовим через fallback, если источники не дадут результата.
    prepared, result, report = await pipe.run_once(channels=["@dry_run"], dry_run=True)
    assert prepared is not None, report.admin_text()
    assert result.get("@dry_run", {}).get("ok"), result
    assert report.result == "published", report.admin_text()
    print("OK: pipeline dryrun")

if __name__ == "__main__": asyncio.run(run())
