from __future__ import annotations

from .image_generation import ImageGeneration
from .media_sources import MediaSources
from .models import Brief, MediaAsset, PostVariant


class MediaEngine:
    def __init__(self, sources: MediaSources | None = None, generator: ImageGeneration | None = None):
        self.sources = sources
        self.generator = generator or ImageGeneration()

    def find_or_generate(self, brief: Brief, variant: PostVariant | None = None) -> MediaAsset:
        queries = self._queries(brief)
        if self.sources:
            asset = self.sources.search(queries)
            if asset and (asset.url or asset.path):
                return asset
        path = self.generator.generate(brief.media_query_en or brief.topic, "generated")
        return MediaAsset(path=path, kind="photo", source="Generated fallback", generated=True, query_used=brief.media_query_en or brief.topic, license_url="local_generated")

    def _queries(self, brief: Brief) -> list[str]:
        ru = brief.media_query_ru or brief.topic
        en = brief.media_query_en or brief.topic
        broader = " ".join(x for x in [brief.country, "travel landscape"] if x) or "beautiful travel landscape"
        loc = " ".join(x for x in [brief.city, brief.country, "tourism"] if x) or "premium travel destination"
        return [ru, en, broader, loc]
