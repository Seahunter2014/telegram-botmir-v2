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
        self.last_error = ""
        if settings.openai_api_key:
            try:
                from openai import AsyncOpenAI
                self._client = AsyncOpenAI(api_key=settings.openai_api_key)
            except Exception as exc:
                self.last_error = f"OpenAI client init error: {type(exc).__name__}: {exc}"
                self._client = None
        else:
            self.last_error = "OPENAI_API_KEY is empty"

    async def generate_json(self, system: str, prompt: str, timeout: int = 45) -> dict[str, Any] | None:
        if not self._client:
            return None
        self.last_error = ""
        try:
            async def call():
                resp = await self._client.chat.completions.create(
                    model=self.settings.openai_model,
                    temperature=self.settings.openai_temperature,
                    messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
                    response_format={"type": "json_object"},
                )
                content = resp.choices[0].message.content or "{}"
                data = loads_json_lenient(content)
                if not isinstance(data, dict):
                    self.last_error = "OpenAI returned non-JSON response"
                    return None
                return data
            return await asyncio.wait_for(call(), timeout=timeout)
        except Exception as exc:
            self.last_error = f"{type(exc).__name__}: {exc}"
            return None

    @staticmethod
    def dumps(data: Any) -> str:
        return json.dumps(data, ensure_ascii=False, indent=2)
