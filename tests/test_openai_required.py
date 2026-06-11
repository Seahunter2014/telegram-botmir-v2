from pathlib import Path
import asyncio
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.ai_writer import AIWriter
from src.models import Brief

async def run():
    writer = AIWriter(client=None, local_fallback=True)
    variants, best, warnings = await writer.generate(Brief(source_key="x", source_name="x", source_url="", topic="Тест", genre="practical_travel", slot="day"))
    assert variants == [], "без OpenAI нельзя генерировать локальный шаблонный пост"
    assert best == 0
    assert warnings
    print("OK: openai required")

if __name__ == "__main__":
    asyncio.run(run())
