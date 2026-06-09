from openai import OpenAI
from .config_loader import env, env_float

class OpenAIClient:
    def __init__(self):
        self.api_key = env("OPENAI_API_KEY")
        self.model = env("OPENAI_MODEL", "gpt-4.1-mini")
        self.temperature = env_float("OPENAI_TEMPERATURE", 0.85)
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None

    def complete_json(self, messages: list[dict], max_tokens: int = 3500) -> str:
        if not self.client:
            raise RuntimeError("OPENAI_API_KEY не задан. Финальная версия не использует шаблонный fallback вместо AI-редактора.")
        response = self.client.chat.completions.create(
            model=self.model,
            temperature=self.temperature,
            response_format={"type": "json_object"},
            messages=messages,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""
