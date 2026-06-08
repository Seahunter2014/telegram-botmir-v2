from .state_store import StateStore
from .models import Signal
from .text_utils import hash_text, normalize_title

class DedupEngine:
    def __init__(self, state: StateStore):
        self.state = state

    def is_duplicate_signal(self, signal: Signal) -> tuple[bool, str]:
        data = self.state.load()
        if signal.url and signal.url in data.get("published_urls", []):
            return True, "URL уже публиковался."
        title_norm = normalize_title(signal.title)
        for old in data.get("published_titles", [])[-80:]:
            if title_norm and (title_norm in normalize_title(old) or normalize_title(old) in title_norm):
                return True, "Похожий заголовок уже был."
        return False, ""

    def is_duplicate_text(self, text: str) -> tuple[bool, str]:
        h = hash_text(text)
        if h in self.state.get("published_text_hashes", []):
            return True, "Такой текст уже публиковался."
        return False, ""
