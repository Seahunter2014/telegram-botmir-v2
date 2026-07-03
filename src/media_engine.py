from __future__ import annotations

from .image_generation import ImageGeneration
from .media_sources import MediaSources
from .models import Brief, MediaAsset, PostVariant


class MediaEngine:
    def __init__(self, sources: MediaSources | None = None, generator: ImageGeneration | None = None):
        self.sources = sources
        self.generator = generator or ImageGeneration()

    def find_or_generate(self, brief: Brief, variant: PostVariant | None = None) -> MediaAsset:
        queries = self._queries(brief, variant)
        if self.sources:
            asset = self.sources.search(queries)
            if asset and (asset.url or asset.path):
                return asset
        query = queries[0] if queries else (brief.media_query_en or brief.topic)
        path = self.generator.generate(query, "generated")
        return MediaAsset(path=path, kind="photo", source="Generated fallback", generated=True, query_used=query, license_url="local_generated")

    def _queries(self, brief: Brief, variant: PostVariant | None = None) -> list[str]:
        ru = brief.media_query_ru or brief.topic
        en = brief.media_query_en or brief.topic
        title = variant.title.strip() if variant else ""
        topic = " ".join(x for x in [brief.city, brief.country, title or brief.topic, "travel"] if x)
        loc = " ".join(x for x in [brief.city, brief.country, "tourism landmark"] if x)
        broader = " ".join(x for x in [brief.country, title or brief.topic, "travel"] if x)
        return list(dict.fromkeys(x for x in [topic, loc, ru, en, broader] if x))
