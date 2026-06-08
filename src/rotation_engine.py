from datetime import datetime
from .state_store import StateStore

class RotationEngine:
    def __init__(self, state: StateStore):
        self.state = state

    def current_slot(self) -> str:
        hour = datetime.now().hour
        if 6 <= hour < 12:
            return "morning"
        if 12 <= hour < 17:
            return "day"
        return "evening"

    def allowed(self, genre: str, city: str = "", country: str = "", source: str = "") -> tuple[bool, str]:
        data = self.state.load()
        last_genres = data.get("published_genres", [])[-2:]
        last_cities = data.get("published_cities", [])[-3:]
        last_sources = data.get("published_sources", [])[-2:]
        if genre in last_genres[-1:]:
            return False, "Этот жанр был в последней публикации."
        if city and city in last_cities:
            return False, "Этот город недавно уже был."
        if source and source in last_sources[-1:]:
            return False, "Этот источник был в последней публикации."
        return True, ""
