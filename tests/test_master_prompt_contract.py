from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

ROOT = Path(__file__).resolve().parents[1]

def main():
    prompt = (ROOT / "prompts" / "master_writer_ru.md").read_text(encoding="utf-8")
    assert "ОДИН лучший" in prompt, "master prompt должен требовать один лучший пост"
    assert "не ставь себе оценку" in prompt.lower() or "ставить себе оценку" in prompt.lower(), "запрет самооценки обязателен"
    assert '"decision"' in prompt and '"title"' in prompt and '"body"' in prompt, "JSON contract неполный"
    ai = (ROOT / "src" / "ai_writer.py").read_text(encoding="utf-8")
    assert "master_writer_ru.md" in ai, "AIWriter должен использовать master_writer_ru.md"
    assert "self.local_fallback = False" in ai, "локальный fallback должен быть отключён"
    assert "_local_generate" not in ai, "локального генератора не должно быть в финальном коде"
    print("OK: master prompt contract")

if __name__ == "__main__": main()
