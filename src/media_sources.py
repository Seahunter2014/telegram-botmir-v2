from __future__ import annotations

import requests

from .config_loader import Settings
from .models import MediaAsset


class MediaSources:
    def __init__(self, settings: Settings):
        self.settings = settings

    def search(self, queries: list[str]) -> MediaAsset | None:
        for q in [x for x in queries if x]:
            asset = self._pexels(q) or self._unsplash(q) or self._pixabay(q)
            if asset:
                return asset
        return None

    def _pexels(self, query: str) -> MediaAsset | None:
        if not self.settings.pexels_api_key:
            return None
        try:
            r = requests.get("https://api.pexels.com/v1/search", params={"query": query, "per_page": 1, "orientation": "landscape"}, headers={"Authorization": self.settings.pexels_api_key}, timeout=8)
            r.raise_for_status()
            data = r.json()
            photos = data.get("photos") or []
            if not photos:
                return None
            p = photos[0]
            return MediaAsset(url=p.get("src", {}).get("large2x") or p.get("src", {}).get("large") or "", source="Pexels", author=p.get("photographer", ""), license_url="https://www.pexels.com/license/", query_used=query)
        except Exception:
            return None

    def _unsplash(self, query: str) -> MediaAsset | None:
        if not self.settings.unsplash_access_key:
            return None
        try:
            r = requests.get("https://api.unsplash.com/search/photos", params={"query": query, "per_page": 1, "orientation": "landscape", "client_id": self.settings.unsplash_access_key}, timeout=8)
            r.raise_for_status()
            results = r.json().get("results") or []
            if not results:
                return None
            p = results[0]
            return MediaAsset(url=p.get("urls", {}).get("regular", ""), source="Unsplash", author=(p.get("user") or {}).get("name", ""), license_url="https://unsplash.com/license", query_used=query)
        except Exception:
            return None

    def _pixabay(self, query: str) -> MediaAsset | None:
        if not self.settings.pixabay_api_key:
            return None
        try:
            r = requests.get("https://pixabay.com/api/", params={"key": self.settings.pixabay_api_key, "q": query, "image_type": "photo", "orientation": "horizontal", "per_page": 3}, timeout=8)
            r.raise_for_status()
            hits = r.json().get("hits") or []
            if not hits:
                return None
            p = hits[0]
            return MediaAsset(url=p.get("largeImageURL") or p.get("webformatURL") or "", source="Pixabay", author=p.get("user", ""), license_url="https://pixabay.com/service/license-summary/", query_used=query)
        except Exception:
            return None
