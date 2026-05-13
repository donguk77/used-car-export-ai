"""Unit tests — app.mcp.tools.

input_schema 검증, ToolDefinition 정합성, anthropic/mcp 포맷 호환.
"""
from __future__ import annotations

import pytest

from app.mcp.tools import (
    TOOLS,
    anthropic_tools,
    get_tool,
    mcp_tools_list,
    validate_arguments,
)


class TestToolRegistry:
    def test_ten_tools_registered(self):
        assert len(TOOLS) == 10

    def test_get_tool_existing(self):
        t = get_tool("decode_vin")
        assert t is not None
        assert t.name == "decode_vin"

    def test_get_tool_unknown(self):
        assert get_tool("fake_tool") is None

    def test_all_tools_have_handler_key(self):
        for t in TOOLS:
            assert t.handler_key, f"{t.name} missing handler_key"

    def test_all_tools_have_description(self):
        for t in TOOLS:
            assert len(t.description) >= 20, f"{t.name} description too short"

    def test_unique_names(self):
        names = [t.name for t in TOOLS]
        assert len(names) == len(set(names)), "tool names not unique"

    def test_input_schema_structure(self):
        """모든 tool input_schema 가 valid JSON Schema object."""
        for t in TOOLS:
            schema = t.input_schema
            assert schema.get("type") == "object", f"{t.name} schema not object"
            assert "properties" in schema, f"{t.name} missing properties"


class TestSchemaFormats:
    def test_anthropic_format(self):
        tools = anthropic_tools()
        assert len(tools) == 10
        first = tools[0]
        # Anthropic tool-use format
        assert "name" in first
        assert "description" in first
        assert "input_schema" in first

    def test_mcp_format(self):
        tools = mcp_tools_list()
        assert len(tools) == 10
        first = tools[0]
        # MCP standard format
        assert "name" in first
        assert "description" in first
        assert "inputSchema" in first  # camelCase per MCP spec


class TestValidateArguments:
    def test_valid_decode_vin(self):
        tool = get_tool("decode_vin")
        err = validate_arguments(tool, {"vin": "KMHE41LBXJA000001"})
        assert err is None

    def test_missing_required(self):
        tool = get_tool("decode_vin")
        err = validate_arguments(tool, {})
        assert err is not None
        assert "vin" in err.lower()
        assert "required" in err.lower()

    def test_vin_too_short(self):
        tool = get_tool("decode_vin")
        err = validate_arguments(tool, {"vin": "TOOSHORT"})
        assert err is not None
        assert "short" in err.lower() or "vin" in err.lower()

    def test_vin_too_long(self):
        tool = get_tool("decode_vin")
        err = validate_arguments(tool, {"vin": "K" * 20})
        assert err is not None

    def test_country_code_valid(self):
        tool = get_tool("lookup_country_rules")
        assert validate_arguments(tool, {"country_code": "DO"}) is None
        assert validate_arguments(tool, {"country_code": "KE"}) is None

    def test_country_code_missing(self):
        tool = get_tool("lookup_country_rules")
        err = validate_arguments(tool, {})
        assert err is not None

    def test_check_compliance_minimal(self):
        """buyer_country 만 있으면 valid (vehicle fields optional)."""
        tool = get_tool("check_compliance")
        assert validate_arguments(tool, {"buyer_country": "KG"}) is None

    def test_check_compliance_full(self):
        tool = get_tool("check_compliance")
        err = validate_arguments(tool, {
            "buyer_country": "KG",
            "buyer_company_name": "Test LLC",
            "vehicle_engine_cc": 3300,
            "vehicle_fuel_type": "Gasoline",
            "vehicle_list_price_usd": 58000,
        })
        assert err is None

    def test_dashboard_summary_empty_valid(self):
        """params 없는 tool 도 빈 dict 통과."""
        tool = get_tool("dashboard_summary")
        assert validate_arguments(tool, {}) is None

    def test_extra_fields_allowed(self):
        """schema 에 additionalProperties=false 명시 안하면 추가 필드 OK."""
        tool = get_tool("decode_vin")
        err = validate_arguments(tool, {
            "vin": "KMHE41LBXJA000001",
            "unknown_field": "ignored",
        })
        assert err is None  # JSON Schema default = additional OK
