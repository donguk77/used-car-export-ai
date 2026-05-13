"""MCP Tool registry — LLM 이 호출할 수 있는 비즈니스 액션.

JSON Schema 형태로 input 정의 (Anthropic tool-use / MCP 표준 호환).
실제 실행 로직은 dispatcher.py.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Callable

logger = logging.getLogger(__name__)


@dataclass
class ToolResult:
    ok: bool
    data: Any  # dict | list | str
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "data": self.data,
            "error": self.error,
        }


@dataclass
class ToolDefinition:
    name: str
    description: str
    input_schema: dict[str, Any]  # JSON Schema (object)
    handler_key: str  # dispatcher 의 메소드명

    def to_anthropic_tool(self) -> dict[str, Any]:
        """Anthropic tool-use 포맷."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
        }

    def to_mcp_tool(self) -> dict[str, Any]:
        """MCP 표준 (tools/list 응답 형태)."""
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema,
        }


# ── 노출 가능한 tool 정의 ─────────────────────────────────────────

TOOLS: list[ToolDefinition] = [
    ToolDefinition(
        name="decode_vin",
        description=(
            "VIN(차대번호 17자리)을 NHTSA vPIC API로 디코딩해 차량 사양을 반환. "
            "Hyundai/Kia/Genesis/KGM 등 한국 제조사 대부분 커버."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "vin": {
                    "type": "string",
                    "description": "17자리 차대번호. 한국차는 K로 시작.",
                    "minLength": 17,
                    "maxLength": 17,
                },
            },
            "required": ["vin"],
        },
        handler_key="decode_vin",
    ),
    ToolDefinition(
        name="lookup_country_rules",
        description=(
            "ISO 3166-1 alpha-2 국가코드 → 통관 룰 (연식·핸들·검사·영사관·서류) 조회. "
            "28국 시드 + 사용자가 추가한 국가."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "country_code": {
                    "type": "string",
                    "description": "ISO 2자리 코드. 예: DO, KE, LY, KG, SY",
                    "minLength": 2,
                    "maxLength": 2,
                },
            },
            "required": ["country_code"],
        },
        handler_key="lookup_country_rules",
    ),
    ToolDefinition(
        name="check_compliance",
        description=(
            "바이어(국가/회사명/tax_id) + 차량(배기량/연료/가격) → OFAC SDN + Russia-proxy + "
            "Yestrade 종합 컴플라이언스 평가. 2025.10 부산경찰청 적발 패턴 자동 차단."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "buyer_country": {"type": "string", "description": "바이어 국가 ISO 코드"},
                "buyer_company_name": {"type": "string", "description": "회사명 (OFAC 매칭)"},
                "buyer_tax_id": {"type": "string", "description": "사업자번호 (Yestrade)"},
                "vehicle_engine_cc": {"type": "integer", "description": "배기량 (cc)"},
                "vehicle_fuel_type": {"type": "string", "description": "Gasoline/Diesel/EV/HEV"},
                "vehicle_list_price_usd": {"type": "number", "description": "표시가 USD"},
            },
            "required": ["buyer_country"],
        },
        handler_key="check_compliance",
    ),
    ToolDefinition(
        name="suggest_price",
        description=(
            "차량 ID + (선택) 도착국 → 동급 통계 + baseline + 시장 보정으로 적정 FOB USD 산출. "
            "신뢰도와 산출 근거 factor 포함."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "vehicle_id": {"type": "string", "description": "Vehicle UUID"},
                "destination_country": {
                    "type": "string",
                    "description": "도착국 ISO 코드 (선택)",
                },
            },
            "required": ["vehicle_id"],
        },
        handler_key="suggest_price",
    ),
    ToolDefinition(
        name="check_ofac_sdn",
        description=(
            "회사명/개인명 → OFAC SDN List (18,947 entries) exact + fuzzy match (rapidfuzz). "
            "match 시 entry uid + program + score 반환."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "회사명 또는 개인명"},
                "fuzzy_threshold": {
                    "type": "integer",
                    "description": "0-100, 기본 85 (강한 매치)",
                    "default": 85,
                },
            },
            "required": ["name"],
        },
        handler_key="check_ofac_sdn",
    ),
    ToolDefinition(
        name="evaluate_import",
        description=(
            "차량 + 도착국 → 통관 가능 여부 (can_import) + 사유 + 필수 서류 list. "
            "룰 엔진 호출. UI '국가 매트릭스'와 동일 로직."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "vehicle_id": {"type": "string"},
                "destination_country": {"type": "string"},
            },
            "required": ["vehicle_id", "destination_country"],
        },
        handler_key="evaluate_import",
    ),
    ToolDefinition(
        name="list_vehicles",
        description=(
            "사용자의 매물 목록 조회. 상태 필터 + 검색어 옵션. 채팅에서 '내 매물 보여줘' 응대."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "description": "available / reserved / sold / shipping / delivered",
                },
                "search": {
                    "type": "string",
                    "description": "make/model/VIN 부분 일치 검색",
                },
                "limit": {"type": "integer", "default": 10, "maximum": 50},
            },
        },
        handler_key="list_vehicles",
    ),
    ToolDefinition(
        name="generate_mail_draft",
        description=(
            "[HTTP-only] 거래(listing) ID + 시나리오 + 언어 → 다국어 격식 메일 자동 작성. "
            "비용·시간 (~15초/건) 때문에 채팅/MCP 에서는 직접 실행하지 않고 호출 안내 metadata 만 "
            "반환합니다. 실제 생성은 POST /api/listings/{id}/mail-draft 또는 admin UI 의 "
            "'AI로 메일 생성하기' 버튼으로 진행하세요. (한국어 검증 패널 옵션 포함)"
        ),
        input_schema={
            "type": "object",
            "properties": {
                "listing_id": {"type": "string"},
                "scenario": {
                    "type": "string",
                    "description": "quote / negotiate / shipping / inquiry / dispute",
                },
                "language": {
                    "type": "string",
                    "description": "en / es / ar / ru",
                },
                "include_korean_translation": {"type": "boolean", "default": False},
            },
            "required": ["listing_id", "scenario", "language"],
        },
        handler_key="generate_mail_draft",
    ),
    ToolDefinition(
        name="generate_export_documents",
        description=(
            "[HTTP-only] 거래(listing) ID → Invoice/Packing List/Shipping Instruction/C/O 4종 PDF "
            "자동 생성. Playwright Chromium 호출 (~7초/건) 때문에 채팅/MCP 에서는 직접 실행하지 "
            "않고 호출 안내 metadata 만 반환합니다. 실제 생성은 POST /api/listings/{id}/documents "
            "또는 admin UI 의 '4종 PDF 생성하기' 버튼으로 진행하세요. (Document.version 자동 increment)"
        ),
        input_schema={
            "type": "object",
            "properties": {
                "listing_id": {"type": "string"},
            },
            "required": ["listing_id"],
        },
        handler_key="generate_export_documents",
    ),
    ToolDefinition(
        name="dashboard_summary",
        description="대시보드 종합 — 차량/바이어/거래 단계별 카운트 + 최근 5건 거래.",
        input_schema={"type": "object", "properties": {}},
        handler_key="dashboard_summary",
    ),
]


def get_tool(name: str) -> ToolDefinition | None:
    for t in TOOLS:
        if t.name == name:
            return t
    return None


# Anthropic provider 가 직접 사용할 수 있는 tools 배열
def anthropic_tools() -> list[dict[str, Any]]:
    return [t.to_anthropic_tool() for t in TOOLS]


# MCP 표준 tools/list 응답
def mcp_tools_list() -> list[dict[str, Any]]:
    return [t.to_mcp_tool() for t in TOOLS]


# Handler 등록 표 (dispatcher 가 사용)
HandlerType = Callable[[dict[str, Any]], ToolResult]


def validate_arguments(tool: ToolDefinition, args: dict[str, Any]) -> str | None:
    """input_schema 검증. 위반 시 사람이 읽을 수 있는 에러 메시지 반환.

    jsonschema 라이브러리는 backend 의존성에 이미 포함됨 (FastAPI/openapi 가
    transient 로 사용). 외부 MCP client (Claude Desktop 등) 가 잘못된 payload 를
    보낼 때 silently 통과 방지.
    """
    try:
        from jsonschema import Draft202012Validator, ValidationError
    except ImportError:
        # jsonschema 없으면 검증 skip (graceful degrade — PoC 단계)
        logger.warning("jsonschema not installed — input_schema validation skipped")
        return None

    try:
        Draft202012Validator(tool.input_schema).validate(args)
        return None
    except ValidationError as e:
        # jsonpath + 짧은 메시지로 변환
        path = ".".join(str(p) for p in e.absolute_path) or "(root)"
        return f"{path}: {e.message}"
    except Exception as e:  # noqa: BLE001
        logger.warning("input_schema validation error for tool %s: %s", tool.name, e)
        return f"schema validation error: {e}"
