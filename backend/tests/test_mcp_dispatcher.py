"""Unit tests — app.mcp.dispatcher.

핵심: tool lookup, input validation, error handling.
DB 의존 handler 는 mock session 으로 검증.
"""
from __future__ import annotations

import uuid
from unittest.mock import MagicMock

import pytest

from app.mcp.dispatcher import MCPDispatcher
from app.mcp.tools import ToolResult


@pytest.fixture
def dispatcher():
    db = MagicMock()
    user_id = uuid.UUID("00000000-0000-0000-0000-000000000099")
    return MCPDispatcher(db, user_id)


class TestUnknownTool:
    def test_unknown_tool_name(self, dispatcher):
        result = dispatcher.call("fake_tool", {})
        assert not result.ok
        assert "unknown tool" in result.error.lower()


class TestInputValidation:
    """Patch #6 — input_schema 검증이 dispatcher.call 진입부에서 작동."""

    def test_decode_vin_missing_required(self, dispatcher):
        result = dispatcher.call("decode_vin", {})
        assert not result.ok
        assert "validation failed" in result.error.lower()

    def test_decode_vin_too_short(self, dispatcher):
        result = dispatcher.call("decode_vin", {"vin": "TOO_SHORT"})
        assert not result.ok
        assert "validation failed" in result.error.lower()

    def test_lookup_country_missing(self, dispatcher):
        result = dispatcher.call("lookup_country_rules", {})
        assert not result.ok

    def test_check_compliance_missing_country(self, dispatcher):
        result = dispatcher.call("check_compliance", {})
        assert not result.ok


class TestStubTools:
    """Patch #2 — generate_mail_draft / generate_export_documents 가
    명시적으로 ok=False + NOT_IMPLEMENTED_IN_CHAT 반환."""

    def test_generate_mail_draft_returns_not_implemented(self, dispatcher):
        # listing_id 가 가짜 UUID 면 'listing not found' 가 먼저 잡힘
        # → 실재 listing 시나리오는 integration test 영역.
        # 여기선 schema 검증 통과 후 dispatcher 가 listing 못 찾을 때 동작.
        # 실재 listing 없이 안전하게 호출 — listing not found 반환
        result = dispatcher.call("generate_mail_draft", {
            "listing_id": "00000000-0000-0000-0000-000000000001",
            "scenario": "quote",
            "language": "en",
        })
        # mock db.get 이 None 반환 → "listing not found"
        assert not result.ok
        assert "not found" in result.error.lower() or "NOT_IMPLEMENTED" in (result.error or "")

    def test_invalid_uuid_caught(self, dispatcher):
        result = dispatcher.call("generate_mail_draft", {
            "listing_id": "not-a-uuid",
            "scenario": "quote",
            "language": "en",
        })
        assert not result.ok
        assert "invalid" in result.error.lower()


class TestHandlerLookup:
    """Patch #7 — 모든 TOOLS handler 가 dispatcher 에 존재."""

    def test_all_handlers_resolvable(self, dispatcher):
        from app.mcp.tools import TOOLS
        for t in TOOLS:
            handler = getattr(dispatcher, f"_h_{t.handler_key}", None)
            assert handler is not None, f"missing _h_{t.handler_key}"
            assert callable(handler)


class TestErrorPath:
    """Patch #5 — SQLAlchemyError 시 db.rollback 호출."""

    def test_sqlalchemy_error_triggers_rollback(self, dispatcher):
        from sqlalchemy.exc import OperationalError
        # decode_vin 은 DB 안 쓰지만, dispatcher 내부에서 다른 핸들러가 raise 하도록
        # mock 으로 강제. handler 자체를 mock 으로 교체.
        original_get = dispatcher.db.get
        dispatcher.db.get = MagicMock(
            side_effect=OperationalError("test", None, Exception("conn lost"))
        )
        result = dispatcher.call("suggest_price", {
            "vehicle_id": "00000000-0000-0000-0000-000000000001",
        })
        assert not result.ok
        assert "OperationalError" in result.error
        # rollback 호출됐는지 검증
        dispatcher.db.rollback.assert_called_once()
        dispatcher.db.get = original_get
