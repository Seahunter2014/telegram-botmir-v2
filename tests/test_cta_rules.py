from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.cta_engine import CTAEngine
from src.models import Brief, PostVariant


def main():
    engine = CTAEngine(channel_url="https://t.me/NadoTurKrd")
    brief = Brief(source_key="x", source_name="x", source_url="", topic="Анталья", genre="flight_deal", slot="day", city="Анталья", allowed_services=["flights"])
    v = engine.apply(PostVariant(1,"test",90,"title","body"), brief)
    assert v.buttons and "t.me/s" not in v.buttons[0].url, "flight_deal не должен вести на чужой Telegram"
    brief2 = Brief(source_key="x", source_name="x", source_url="", topic="Красивые места", genre="inspiration_story", slot="morning")
    v2 = engine.apply(PostVariant(1,"test",90,"title","body"), brief2)
    assert v2.buttons, "универсальные кнопки должны быть"
    print("OK: cta")

if __name__ == "__main__": main()
