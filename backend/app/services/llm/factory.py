from __future__ import annotations

from app.config import get_settings
from app.services.llm.base import LLMProvider


def create_provider(name: str | None = None) -> LLMProvider:
    """LLM_PROVIDER 환경변수 또는 명시 인자에 따라 provider 인스턴스화."""
    settings = get_settings()
    name = (name or settings.llm_provider or "stub").lower()

    if name == "anthropic":
        from app.services.llm.anthropic_provider import AnthropicProvider

        return AnthropicProvider(settings.anthropic_api_key, settings.anthropic_model)

    if name == "gemini":
        from app.services.llm.gemini_provider import GeminiProvider

        return GeminiProvider(settings.gemini_api_key, settings.gemini_model)

    if name == "stub":
        from app.services.llm.stub_provider import StubProvider

        return StubProvider()

    raise ValueError(f"unknown LLM provider: {name!r} (use anthropic|gemini|stub)")
