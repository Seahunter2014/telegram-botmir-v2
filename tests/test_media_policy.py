from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.media_engine import MediaEngine
from src.models import Brief


def main():
    asset = MediaEngine().find_or_generate(Brief(source_key="x", source_name="x", source_url="", topic="Марокко", genre="destination_post", slot="morning", media_query_en="Morocco travel"))
    assert asset.generated and Path(asset.path).exists(), "должна генерироваться fallback-картинка"
    print("OK: media")

if __name__ == "__main__": main()
