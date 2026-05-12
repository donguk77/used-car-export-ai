from __future__ import annotations

import logging

from app.config import get_settings
from app.services.llm.base import LLMProvider

logger = logging.getLogger(__name__)


def create_provider(name: str | None = None) -> LLMProvider:
    """LLM_PROVIDER 환경변수 또는 명시 인자에 따라 provider 인스턴스화.

    데모 안전성: API 키 없거나 init 실패 시 stub 으로 자동 fallback
    (mentor 데모 중 Gemini quota 초과 같은 사고 방지). 로그로 사용자 경고.
    """
    settings = get_settings()
    name = (name or settings.llm_provider or "stub").lower()

    if name == "anthropic":
        try:
            from app.services.llm.anthropic_provider import AnthropicProvider
            if not settings.anthropic_api_key:
                raise ValueError("ANTHROPIC_API_KEY is empty")
            return AnthropicProvider(settings.anthropic_api_key, settings.anthropic_model)
        except Exception as e:  # noqa: BLE001
            logger.warning(
                f"⚠ Anthropic provider init failed ({type(e).__name__}: {e}). "
                f"Falling back to STUB — UI will show '[STUB MODE] ...' content."
            )
            return _stub()

    if name == "gemini":
        try:
            from app.services.llm.gemini_provider import GeminiProvider
            if not settings.gemini_api_key:
                raise ValueError("GEMINI_API_KEY is empty")
            return GeminiProvider(settings.gemini_api_key, settings.gemini_model)
        except Exception as e:  # noqa: BLE001
            logger.warning(
                f"⚠ Gemini provider init failed ({type(e).__name__}: {e}). "
                f"Falling back to STUB — UI will show '[STUB MODE] ...' content. "
                f"Demo 시 mail-draft 가 의미 있는 내용을 안 보여줄 수 있음 — "
                f".env 의 GEMINI_API_KEY 확인 권장."
            )
            return _stub()

    if name == "stub":
        return _stub()

    raise ValueError(f"unknown LLM provider: {name!r} (use anthropic|gemini|stub)")


def _stub() -> LLMProvider:
    from app.services.llm.stub_provider import StubProvider
    return StubProvider()
