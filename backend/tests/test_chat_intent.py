"""Unit tests — mcp_server._match_intent regex 패턴.

자연어 → tool_name + arguments 매핑 정확성 + false positive 차단 검증.
DB 호출은 mock (시드 28국 + 추가 ZK).
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.api.mcp_server import (
    _COUNTRY_RULE_RE_1,
    _COUNTRY_RULE_RE_2,
    _DASHBOARD_RE,
    _OFAC_RE,
    _VEHICLES_LIST_RE,
    _VIN_RE,
    _match_intent,
)


# 28국 시드 화이트리스트 mock
SEEDED_CODES = frozenset({
    "AE", "AZ", "BD", "CL", "CR", "DO", "DZ", "EG", "GH", "JO",
    "KE", "KG", "KH", "KZ", "LK", "LY", "MM", "MX", "MY", "NG",
    "PH", "SD", "SY", "TH", "TZ", "UZ", "VN", "ZA",
})


def _mock_db_with_codes(codes=SEEDED_CODES):
    """_known_country_codes 를 mock — db.execute 호출 없이 codes 반환."""
    db = MagicMock()
    with patch("app.api.mcp_server._known_country_codes", return_value=codes):
        return db


class TestVinPattern:
    def test_extracts_valid_vin(self):
        assert _VIN_RE.search("VIN: KMHE41LBXJA000001 디코드해줘") is not None

    def test_extracts_with_equals(self):
        assert _VIN_RE.search("VIN=KMHE41LBXJA000001") is not None

    def test_case_insensitive(self):
        assert _VIN_RE.search("vin: KMHE41LBXJA000001") is not None

    def test_rejects_short_vin(self):
        """16자리는 매칭 안돼야."""
        assert _VIN_RE.search("VIN: KMHE41LBXJA00000") is None

    def test_rejects_no_prefix(self):
        """VIN: 없이 그냥 17자리만 → 매칭 안됨 (오탐 방지)."""
        assert _VIN_RE.search("KMHE41LBXJA000001 디코드") is None


class TestOfacPattern:
    def test_korean_제재(self):
        m = _OFAC_RE.search('제재 "Volga Group" 조회')
        assert m and m.group(1) == "Volga Group"

    def test_english_ofac(self):
        m = _OFAC_RE.search('OFAC check "Test LLC"')
        assert m and m.group(1) == "Test LLC"

    def test_single_quotes(self):
        m = _OFAC_RE.search("제재 'Bad Company' 확인")
        assert m and m.group(1) == "Bad Company"


class TestCountryRulePatternsWithWhitelist:
    """Patch #3 — DB 화이트리스트 검증 (정적 set 아님)."""

    def test_seeded_country_matches(self):
        """시드 국가 코드는 매칭."""
        with patch("app.api.mcp_server._known_country_codes", return_value=SEEDED_CODES):
            result = _match_intent("DO 통관 가능 조건", db=MagicMock())
        assert result == ("lookup_country_rules", {"country_code": "DO"})

    def test_unseeded_country_blocked(self):
        """시드에 없는 국가 코드 → 매칭 차단."""
        with patch("app.api.mcp_server._known_country_codes", return_value=SEEDED_CODES):
            # US 는 시드에 없음
            result = _match_intent("US 통관 가능", db=MagicMock())
        assert result is None or result[0] != "lookup_country_rules"

    def test_english_word_false_positive_blocked(self):
        """OK/AS/IS/NO 등 영어 두 글자 단어 차단."""
        with patch("app.api.mcp_server._known_country_codes", return_value=SEEDED_CODES):
            for word in ("OK", "AS", "IS", "NO", "TO", "OF"):
                result = _match_intent(f"{word} 룰 어떻게 되나요", db=MagicMock())
                # lookup_country_rules 가 매칭되면 안됨
                assert result is None or result[0] != "lookup_country_rules", \
                    f"{word!r} false positive!"

    def test_wiki_added_country_matches(self):
        """Wiki 에서 추가된 신규 국가 (예: KW) 도 매칭."""
        extended = SEEDED_CODES | {"KW"}
        with patch("app.api.mcp_server._known_country_codes", return_value=extended):
            result = _match_intent("KW 통관 룰", db=MagicMock())
        assert result == ("lookup_country_rules", {"country_code": "KW"})

    def test_reverse_word_order(self):
        """'통관 DO' 어순도 매칭."""
        with patch("app.api.mcp_server._known_country_codes", return_value=SEEDED_CODES):
            result = _match_intent("케냐 룰 알려줘 KE", db=MagicMock())
        assert result == ("lookup_country_rules", {"country_code": "KE"})


class TestVehiclesListPattern:
    def test_korean_매물(self):
        assert _VEHICLES_LIST_RE.search("내 매물 보여줘") is not None

    def test_korean_차량_목록(self):
        assert _VEHICLES_LIST_RE.search("차량 목록 알려줘") is not None

    def test_english_vehicles_list(self):
        assert _VEHICLES_LIST_RE.search("show me vehicles list") is not None


class TestDashboardPattern:
    def test_korean(self):
        assert _DASHBOARD_RE.search("대시보드 요약") is not None
        assert _DASHBOARD_RE.search("요약 보여줘") is not None

    def test_english(self):
        assert _DASHBOARD_RE.search("show dashboard summary") is not None


class TestMatchIntentFallback:
    """매칭 실패 시 None 반환."""

    def test_no_match_returns_none(self):
        with patch("app.api.mcp_server._known_country_codes", return_value=SEEDED_CODES):
            assert _match_intent("안녕하세요", db=MagicMock()) is None

    def test_empty_string(self):
        with patch("app.api.mcp_server._known_country_codes", return_value=SEEDED_CODES):
            assert _match_intent("", db=MagicMock()) is None

    def test_vin_priority(self):
        """VIN + 통관 둘 다 포함 → VIN 우선 (먼저 정의된 패턴)."""
        with patch("app.api.mcp_server._known_country_codes", return_value=SEEDED_CODES):
            result = _match_intent(
                "VIN: KMHE41LBXJA000001 DO 통관 확인", db=MagicMock()
            )
        assert result[0] == "decode_vin"
