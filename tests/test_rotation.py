from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.models import Signal
from src.rotation_engine import RotationEngine
from src.state_store import StateStore


def main():
    rot = RotationEngine(StateStore())
    signals = [Signal(id=str(i), source_key=f"s{i}", source_name=f"S{i}", source_url="", title=f"Тема {i}", text="travel море город", url=f"u{i}", genre="destination_post", score=70+i) for i in range(5)]
    ranked = rot.rank(signals, current_slot="morning")
    assert ranked, "нет ranked"
    assert len({s.source_key for s in ranked[:3]}) == 3, "источники должны отличаться"
    print("OK: rotation")

if __name__ == "__main__": main()
