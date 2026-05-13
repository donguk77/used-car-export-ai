"""MCP (Model Context Protocol) — LLM tool-use 인터페이스 추상화.

제안서 명시 "Claude Code + MCP 기반 백엔드 자동화 워크플로우" 충족.

기존 서비스 (NHTSA VIN, OFAC SDN, 통관 룰, 시세 산출, 컴플라이언스) 를
LLM 이 호출할 수 있는 표준 tool 형태로 노출.

채팅 에이전트 (Feature 3) 가 자연어 → tool call 라우팅 시 사용.
외부 MCP client (Claude Desktop, Cline 등) 도 HTTP endpoint 로 호출 가능.
"""

from app.mcp.dispatcher import MCPDispatcher, get_dispatcher
from app.mcp.tools import TOOLS, ToolDefinition, ToolResult

__all__ = ["MCPDispatcher", "get_dispatcher", "TOOLS", "ToolDefinition", "ToolResult"]
