from __future__ import annotations

import asyncio
import json
from typing import Any

from .config_loader import Settings
from .json_repair import loads_json_lenient


class OpenAIClient:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._client = None
        if settings.openai_api_key:
            try:
                from openai import AsyncOpenAI
                self._client = AsyncOpenAI(api_key=settings.openai_api_key)
            except Exception:
                self._client = None

    async def generate_json(self, system: str, prompt: str, timeout: int = 45) -> dict[str, Any] | None:
        if not self._client:
            return None
        try:
            async def call():
                resp = await self._client.chat.completions.create(
                    model=self.settings.openai_model,
                    temperature=self.settings.openai_temperature,
                    messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
                    response_format={"type": "json_object"},
                )
                content = resp.choices[0].message.content or "{}"
                return loads_json_lenient(content)
            return await asyncio.wait_for(call(), timeout=timeout)
        except Exception:
            return None

    @staticmethod
    def dumps(data: Any) -> str:
        return json.dumps(data, ensure_ascii=False, indent=2)
