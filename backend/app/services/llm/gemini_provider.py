from __future__ import annotations

from app.services.llm.base import LLMResponse


class GeminiProvider:
    name = "gemini"

    def __init__(self, api_key: str, model: str):
        if not api_key:
            raise ValueError("GEMINI_API_KEY is empty")
        from google import genai
        from google.genai import types

        self._types = types
        self.client = genai.Client(api_key=api_key)
        self.model = model

    def complete(
        self,
        *,
        system: str,
        user: str,
        max_tokens: int = 2048,
        temperature: float = 0.4,
    ) -> LLMResponse:
        config = self._types.GenerateContentConfig(
            system_instruction=system,
            max_output_tokens=max_tokens,
            temperature=temperature,
        )
        response = self.client.models.generate_content(
            model=self.model,
            contents=user,
            config=config,
        )
        return LLMResponse(
            text=response.text or "",
            provider=self.name,
            model=self.model,
            raw=response,
        )
