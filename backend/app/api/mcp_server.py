"""MCP HTTP server + 채팅 에이전트 endpoints.

제안서 명시 "Claude Code + MCP 기반 백엔드 자동화 워크플로우" + "채팅 기반
대시보드 UI" 두 가지 모두 충족.

- /api/mcp/tools/list   : MCP 표준 tool 목록 (외부 client 용)
- /api/mcp/tools/call   : tool 직접 호출 (외부 client 용)
- /api/agent/chat       : 자연어 입력 → LLM tool-use → 응답 (내부 채팅 UI)
"""

from __future__ import annotations

import json
import logging
import re
import uuid
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id
from app.db import get_db
from app.mcp import get_dispatcher
from app.mcp.tools import TOOLS, mcp_tools_list

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["mcp"])


# ── MCP HTTP endpoints (외부 client 용) ──────────────────────────


class MCPToolListResponse(BaseModel):
    tools: list[dict[str, Any]]


class MCPCallRequest(BaseModel):
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class MCPCallResponse(BaseModel):
    ok: bool
    data: Any = None
    error: str | None = None


@router.get("/mcp/tools/list", response_model=MCPToolListResponse)
def mcp_list_tools() -> MCPToolListResponse:
    return MCPToolListResponse(tools=mcp_tools_list())


@router.post("/mcp/tools/call", response_model=MCPCallResponse)
def mcp_call_tool(
    payload: MCPCallRequest,
    db: Annotated[Session, Depends(get_db)],
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
) -> MCPCallResponse:
    dispatcher = get_dispatcher(db, user_id)
    result = dispatcher.call(payload.name, payload.arguments)
    return MCPCallResponse(ok=result.ok, data=result.data, error=result.error)


# ── 채팅 에이전트 (내부 UI 용) ──────────────────────────────────


class ChatStep(BaseModel):
    """대화 한 턴의 결과 — UI 가 그대로 표시."""

    type: Literal["text", "tool_call", "tool_result", "error"]
    content: str | dict[str, Any]


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    history: list[dict[str, Any]] = Field(default_factory=list, description="이전 turn 들 (role/content)")


class ChatResponse(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    reply: str
    steps: list[ChatStep] = Field(default_factory=list)
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)
    suggested_actions: list[dict[str, str]] = Field(default_factory=list)


# ── 자연어 → tool 라우팅 (intent classifier 패턴) ──────────────
# Anthropic / Gemini 가 native tool-use 를 지원하지만, 단순 의도 라우팅은
# 키워드 + LLM 보조로 충분히 빠르고 결정론적. LLM 은 응답 자연어만 생성.


# 시드된 28국 ISO 코드 — chat 패턴 매칭 false positive 방지용 화이트리스트.
# 영어 두 글자 단어 (IS/OK/NO/AS/TO/OF/BMW의 부분 등) 가 국가코드로 잘못
# 잡히는 것 차단. yaml 시드와 일치 — 신규 국가는 Wiki 추가 시 DB 에서 동적
# fetch 하지 않고 정적 list 유지 (chat 우선순위 = 빠른 fast-path).
_KNOWN_COUNTRY_CODES = {
    "AE", "AZ", "BD", "CL", "CR", "DO", "DZ", "EG", "GH", "JO",
    "KE", "KG", "KH", "KZ", "LK", "LY", "MM", "MX", "MY", "NG",
    "PH", "SD", "SY", "TH", "TZ", "UAE", "UZ", "VN", "ZA", "ZW",
}


def _make_country_extractor(group_idx: int):
    """국가코드 추출 + 화이트리스트 검증."""
    def extractor(m: re.Match) -> dict[str, Any] | None:
        code = m.group(group_idx).upper()
        if code not in _KNOWN_COUNTRY_CODES:
            return None  # 매칭 무효
        return {"country_code": code}
    return extractor


_INTENT_PATTERNS = [
    # (regex, tool_name, arg_extractor) — extractor 가 None 반환 시 다음 패턴 시도
    (
        re.compile(r"VIN[\s:=]+([A-HJ-NPR-Z0-9]{17})", re.IGNORECASE),
        "decode_vin",
        lambda m: {"vin": m.group(1).upper()},
    ),
    (
        re.compile(r"\b(?:OFAC|제재|sanctions?)\b.*?[\"']([^\"']+)[\"']", re.IGNORECASE),
        "check_ofac_sdn",
        lambda m: {"name": m.group(1)},
    ),
    (
        re.compile(r"\b([A-Z]{2})\b.*?(?:통관|규제|룰|rule)"),
        "lookup_country_rules",
        _make_country_extractor(1),
    ),
    (
        re.compile(r"(?:통관|규제|룰|rule).*?\b([A-Z]{2})\b"),
        "lookup_country_rules",
        _make_country_extractor(1),
    ),
    (
        re.compile(r"(?:매물|차량|vehicle).*?(?:목록|리스트|list|보여)", re.IGNORECASE),
        "list_vehicles",
        lambda m: {"limit": 10},
    ),
    (
        re.compile(r"(?:대시보드|dashboard|요약|summary)", re.IGNORECASE),
        "dashboard_summary",
        lambda m: {},
    ),
]


@router.post("/agent/chat", response_model=ChatResponse)
def agent_chat(
    payload: ChatRequest,
    db: Annotated[Session, Depends(get_db)],
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
) -> ChatResponse:
    """자연어 채팅 → MCP tool 라우팅 + LLM 응답.

    하이브리드:
    1. 키워드 패턴으로 명확한 의도는 즉시 tool 호출 (빠름·결정론)
    2. 모호하면 LLM 에 tool 목록 + history 줘서 자연어 응답 생성
    """
    dispatcher = get_dispatcher(db, user_id)
    msg = payload.message.strip()
    steps: list[ChatStep] = []
    tool_calls: list[dict[str, Any]] = []
    suggested: list[dict[str, str]] = []

    # 1. 패턴 매칭 시도 (extractor 가 None 반환 시 다음 패턴 계속)
    matched_tool = None
    matched_args: dict[str, Any] = {}
    for pattern, tool_name, extractor in _INTENT_PATTERNS:
        m = pattern.search(msg)
        if not m:
            continue
        extracted = extractor(m)
        if extracted is None:
            continue
        matched_tool = tool_name
        matched_args = extracted
        break

    if matched_tool:
        steps.append(ChatStep(type="tool_call", content={
            "tool": matched_tool, "arguments": matched_args,
        }))
        result = dispatcher.call(matched_tool, matched_args)
        tool_calls.append({
            "tool": matched_tool,
            "arguments": matched_args,
            "ok": result.ok,
            "data": result.data,
            "error": result.error,
        })
        steps.append(ChatStep(
            type="tool_result" if result.ok else "error",
            content=result.to_dict(),
        ))
        reply = _format_tool_reply(matched_tool, result.to_dict(), msg)
        suggested = _suggest_followups(matched_tool, result.to_dict())
        return ChatResponse(reply=reply, steps=steps, tool_calls=tool_calls, suggested_actions=suggested)

    # 2. LLM 에 위임 (자연어 안내 + tool 추천)
    reply = _llm_general_reply(msg, payload.history)
    steps.append(ChatStep(type="text", content=reply))
    suggested = _general_suggestions()
    return ChatResponse(reply=reply, steps=steps, tool_calls=tool_calls, suggested_actions=suggested)


# ── helpers ──────────────────────────────────────────────────────


def _format_tool_reply(tool: str, result: dict[str, Any], user_msg: str) -> str:
    """Tool 결과를 자연어로 포맷 (LLM 안 거치는 fast path)."""
    if not result.get("ok"):
        return f"⚠️ {tool} 실행 중 오류: {result.get('error')}"

    data = result.get("data") or {}

    if tool == "decode_vin":
        return (
            f"VIN {data.get('vin')} 디코드 완료 — "
            f"{data.get('make') or '?'} {data.get('model') or '?'} "
            f"{data.get('year') or ''}, {data.get('fuel_type') or '?'}, "
            f"{data.get('engine_cc') or '?'}cc, {data.get('drivetrain') or ''}. "
            "‘매물 등록’ 페이지에서 자동 채움 가능합니다."
        )
    if tool == "check_ofac_sdn":
        if data.get("match_type") == "exact":
            return (
                f"🚨 OFAC SDN exact match: '{data.get('matched_name')}' "
                f"(uid={data.get('uid')}, programs={data.get('programs')}). "
                "이 거래는 차단해야 합니다."
            )
        if data.get("match_type") == "fuzzy":
            return (
                f"⚠️ OFAC SDN fuzzy match (score {data.get('score'):.0f}%): "
                f"'{data.get('matched_name')}'. 수동 검토 권장."
            )
        return f"✓ OFAC SDN 18,947건 조회 완료 — 매치 없음. 안전합니다."
    if tool == "lookup_country_rules":
        rules = data.get("rules") or []
        return (
            f"{data.get('name_ko') or data.get('name_en')} ({data.get('code')}) — "
            f"{data.get('steering') or '핸들 미정'}, 비즈니스 언어 {data.get('business_language') or '미정'}, "
            f"룰 {len(rules)}건. "
            f"{'영사인증 필요. ' if data.get('consular_legalization') else ''}"
            f"{'러우회 위험. ' if data.get('is_russia_proxy_risk') else ''}"
            f"상세는 LLM Wiki 페이지에서 편집 가능합니다."
        )
    if tool == "list_vehicles":
        items = data if isinstance(data, list) else []
        if not items:
            return "등록된 매물이 없습니다. ‘매물 등록’ 페이지에서 추가하세요."
        lines = [
            f"• {v.get('make')} {v.get('model')} {v.get('year')} "
            f"({v.get('vin') or 'VIN 없음'}) — {v.get('status')}"
            for v in items[:10]
        ]
        return f"매물 {len(items)}건:\n" + "\n".join(lines)
    if tool == "dashboard_summary":
        return (
            f"대시보드 요약 — 차량 {data.get('vehicles_total')}건, "
            f"바이어 {data.get('buyers_total')}명, 거래 {data.get('listings_total')}건."
        )
    if tool == "suggest_price":
        return (
            f"적정 FOB 추천: ${data.get('suggested_fob_usd'):,.0f} "
            f"(${data.get('range_low'):,.0f}~${data.get('range_high'):,.0f}). "
            f"신뢰도 {data.get('confidence')}, 동급 표본 {data.get('n_samples')}건."
        )
    return f"{tool} 결과:\n```json\n{json.dumps(data, ensure_ascii=False, indent=2)[:600]}\n```"


def _suggest_followups(tool: str, result: dict[str, Any]) -> list[dict[str, str]]:
    """Tool 결과 기반 다음 액션 추천 (UI 버튼)."""
    if not result.get("ok"):
        return []
    data = result.get("data") or {}
    if tool == "decode_vin":
        return [
            {"label": "이 VIN 으로 매물 등록", "to": "/vehicles/new"},
            {"label": "Wiki — NHTSA 데이터 출처", "to": "/wiki"},
        ]
    if tool == "lookup_country_rules":
        code = data.get("code")
        return [{"label": f"{code} 룰 편집", "to": f"/wiki/{code}"}] if code else []
    if tool == "list_vehicles":
        return [
            {"label": "매물 페이지", "to": "/vehicles"},
            {"label": "신규 매물 등록", "to": "/vehicles/new"},
        ]
    if tool == "dashboard_summary":
        return [{"label": "대시보드", "to": "/"}]
    return []


def _general_suggestions() -> list[dict[str, str]]:
    return [
        {"label": "VIN 디코드", "to": ""},
        {"label": "통관 룰 조회 (예: DO 통관)", "to": ""},
        {"label": "매물 목록", "to": ""},
        {"label": "Wiki 편집", "to": "/wiki"},
    ]


def _llm_general_reply(msg: str, history: list[dict[str, Any]]) -> str:
    """Tool 매칭 실패 시 LLM 에 짧은 안내 응답 생성 위임.

    LLM 호출 실패 시 기본 안내 문구로 fallback (데모 안전성).
    """
    from app.services.llm import create_provider

    tool_descs = "\n".join(f"- {t.name}: {t.description}" for t in TOOLS)
    system = (
        "당신은 한국 영세 중고차 수출업체용 AI 에이전트입니다. "
        "사용자 메시지를 짧게 (3-5문장) 한국어로 안내하세요. "
        "구체적 액션이 필요하면 아래 tool 중 하나를 사용자가 호출하도록 유도하세요. "
        "tool 호출은 사용자 메시지에 키워드(VIN/국가코드/매물 등)가 포함될 때만 자동 매칭됩니다.\n\n"
        f"사용 가능 tool 목록:\n{tool_descs}"
    )
    try:
        provider = create_provider()
        resp = provider.complete(
            system=system,
            user=msg,
            max_tokens=500,
            temperature=0.3,
        )
        return resp.text.strip() or _fallback_help()
    except Exception as e:  # noqa: BLE001
        logger.warning("agent chat LLM call failed: %s", e)
        return _fallback_help()


def _fallback_help() -> str:
    return (
        "안녕하세요. 다음 중 하나를 시도해보세요:\n"
        "• VIN 디코드: 'VIN: KMHE41LBXJA000001' 같이 입력\n"
        "• 통관 룰 조회: 'DO 통관 가능 조건' 또는 '케냐 룰'\n"
        "• 매물 목록: '내 매물 보여줘'\n"
        "• OFAC 제재 조회: '제재 \"Volga Group\"'\n"
        "• 대시보드 요약: '대시보드 요약'\n\n"
        "LLM Wiki 페이지에서 28국 통관 룰을 직접 편집할 수 있습니다."
    )
