"""API 키 없이 demo_mail_writer.py 가 돌도록 하는 stub. 실제 LLM 호출 안 함."""

from __future__ import annotations

import json

from app.services.llm.base import LLMResponse


class StubProvider:
    name = "stub"
    model = "stub-mock-model"

    def complete(
        self,
        *,
        system: str,
        user: str,
        max_tokens: int = 2048,
        temperature: float = 0.4,
    ) -> LLMResponse:
        # mail_writer 가 JSON 을 기대하니 같은 형태로 돌려준다
        payload = {
            "subject": "[STUB] Mock email subject — set LLM_PROVIDER to anthropic|gemini",
            "body": (
                "[STUB MODE] No real LLM call was made.\n\n"
                "system prompt (first 200 chars):\n"
                + system[:200]
                + "\n\nuser prompt (first 400 chars):\n"
                + user[:400]
            ),
        }
        return LLMResponse(
            text=json.dumps(payload, ensure_ascii=False),
            provider=self.name,
            model=self.model,
        )
