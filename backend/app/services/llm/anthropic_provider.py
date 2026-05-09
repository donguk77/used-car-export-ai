from __future__ import annotations

from app.services.llm.base import LLMResponse


class AnthropicProvider:
    name = "anthropic"

    def __init__(self, api_key: str, model: str):
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY is empty")
        # Lazy import: optional dep
        import anthropic

        self._anthropic = anthropic
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    def complete(
        self,
        *,
        system: str,
        user: str,
        max_tokens: int = 2048,
        temperature: float = 0.4,
    ) -> LLMResponse:
        message = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=[
                {
                    "type": "text",
                    "text": system,
                    # 시스템 프롬프트가 시나리오·언어별로 재사용되므로 캐시 적용
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[{"role": "user", "content": user}],
        )
        text = "".join(block.text for block in message.content if block.type == "text")
        return LLMResponse(text=text, provider=self.name, model=self.model, raw=message)
