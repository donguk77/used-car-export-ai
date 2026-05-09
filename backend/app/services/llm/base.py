from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass
class LLMResponse:
    text: str
    provider: str
    model: str
    raw: object | None = None


class LLMProvider(Protocol):
    """공통 LLM 인터페이스. Anthropic·Gemini·Stub 모두 이 시그니처를 따른다."""

    name: str
    model: str

    def complete(
        self,
        *,
        system: str,
        user: str,
        max_tokens: int = 2048,
        temperature: float = 0.4,
    ) -> LLMResponse: ...
