import time
from .state_store import StateStore

class AnalyticsStore:
    def __init__(self, state: StateStore):
        self.state = state

    def record_publication(self, payload: dict):
        data = self.state.load()
        arr = data.setdefault("analytics", [])
        payload["ts"] = int(time.time())
        arr.append(payload)
        data["analytics"] = arr[-500:]
        self.state.save(data)
