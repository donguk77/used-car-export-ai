import { useEffect, useRef, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import {
  Bot,
  Loader2,
  Send,
  Sparkles,
  Terminal,
  User as UserIcon,
  Wrench,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";
import { cn, formatApiError } from "@/lib/utils";

interface ToolCall {
  tool: string;
  arguments: Record<string, unknown>;
  ok: boolean;
  data: unknown;
  error: string | null;
}

interface SuggestedAction {
  label: string;
  to: string;
}

interface ChatResponse {
  reply: string;
  steps: { type: string; content: unknown }[];
  tool_calls: ToolCall[];
  suggested_actions: SuggestedAction[];
}

interface ChatTurn {
  id: string;
  role: "user" | "assistant";
  text: string;
  tool_calls?: ToolCall[];
  suggested_actions?: SuggestedAction[];
  pending?: boolean;
  error?: string;
}

interface MCPTool {
  name: string;
  description: string;
}

const QUICK_PROMPTS = [
  "VIN: KMHE41LBXJA000001",
  "DO 통관 가능 조건",
  "내 매물 보여줘",
  "대시보드 요약",
  "제재 \"Volga Group\"",
];

export function ChatPage() {
  const [input, setInput] = useState("");
  const [turns, setTurns] = useState<ChatTurn[]>([
    {
      id: "welcome",
      role: "assistant",
      text:
        "안녕하세요. 중고차 수출 AI 에이전트입니다. 자연어로 명령하세요.\n" +
        "예: 'VIN: KMHE41LBXJA000001 디코드' / 'DO 통관 룰' / '내 매물 목록'",
      suggested_actions: QUICK_PROMPTS.map((label) => ({ label, to: "" })),
    },
  ]);
  const scrollRef = useRef<HTMLDivElement>(null);

  const { data: tools } = useQuery({
    queryKey: ["mcp-tools"],
    queryFn: async (): Promise<{ tools: MCPTool[] }> => {
      const r = await api.get<{ tools: MCPTool[] }>("/api/mcp/tools/list");
      return r.data;
    },
    staleTime: 60_000,
  });

  const sendMutation = useMutation({
    mutationFn: async (msg: string): Promise<ChatResponse> => {
      const r = await api.post<ChatResponse>("/api/agent/chat", {
        message: msg,
        history: turns.slice(-6).map((t) => ({ role: t.role, content: t.text })),
      });
      return r.data;
    },
  });

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [turns]);

  const send = async (text: string) => {
    const trimmed = text.trim();
    if (!trimmed) return;
    setInput("");
    const userId = crypto.randomUUID();
    const assistantId = crypto.randomUUID();
    setTurns((t) => [
      ...t,
      { id: userId, role: "user", text: trimmed },
      { id: assistantId, role: "assistant", text: "", pending: true },
    ]);
    try {
      const res = await sendMutation.mutateAsync(trimmed);
      setTurns((t) =>
        t.map((turn) =>
          turn.id === assistantId
            ? {
                ...turn,
                text: res.reply,
                tool_calls: res.tool_calls,
                suggested_actions: res.suggested_actions,
                pending: false,
              }
            : turn,
        ),
      );
    } catch (e) {
      setTurns((t) =>
        t.map((turn) =>
          turn.id === assistantId
            ? { ...turn, text: "응답 실패", error: formatApiError(e), pending: false }
            : turn,
        ),
      );
    }
  };

  return (
    <div className="grid h-[calc(100vh-128px)] grid-cols-1 gap-4 lg:grid-cols-[1fr_280px]">
      {/* 메인 채팅 영역 */}
      <Card className="flex flex-col overflow-hidden">
        <CardHeader className="border-b">
          <CardTitle className="flex items-center gap-2 text-base">
            <Bot className="h-4 w-4" /> AI 에이전트 채팅
            <Badge variant="outline" className="ml-2 text-[10px]">
              MCP {tools?.tools.length ?? "—"} tools
            </Badge>
          </CardTitle>
        </CardHeader>

        <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-4">
          {turns.map((turn) => (
            <Turn key={turn.id} turn={turn} onQuickAction={send} />
          ))}
        </div>

        <form
          className="border-t bg-card p-3"
          onSubmit={(e) => {
            e.preventDefault();
            send(input);
          }}
        >
          <div className="flex items-end gap-2">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  send(input);
                }
              }}
              placeholder="메시지 입력 (Enter 전송, Shift+Enter 줄바꿈)…"
              rows={2}
              className="flex-1 resize-none rounded-md border border-input bg-transparent px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-ring"
              disabled={sendMutation.isPending}
            />
            <Button
              type="submit"
              disabled={!input.trim() || sendMutation.isPending}
              className="gap-1"
            >
              {sendMutation.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Send className="h-4 w-4" />
              )}
              전송
            </Button>
          </div>
          <div className="mt-2 flex flex-wrap gap-1">
            {QUICK_PROMPTS.map((p) => (
              <button
                key={p}
                type="button"
                onClick={() => send(p)}
                disabled={sendMutation.isPending}
                className="rounded-md border border-dashed border-border px-2 py-0.5 text-[11px] text-muted-foreground hover:bg-accent hover:text-foreground"
              >
                {p}
              </button>
            ))}
          </div>
        </form>
      </Card>

      {/* 사이드 — MCP tools 목록 */}
      <aside className="space-y-3">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-sm">
              <Wrench className="h-4 w-4" /> MCP Tools
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-xs">
            <p className="text-muted-foreground">
              에이전트가 호출할 수 있는 비즈니스 액션. Claude Code / 외부 MCP client
              에서도 동일하게 호출 가능.
            </p>
            <div className="space-y-1">
              {(tools?.tools ?? []).map((t) => (
                <div key={t.name} className="rounded-md border border-border/60 bg-muted/30 p-2">
                  <p className="font-mono text-[11px] font-semibold text-primary">{t.name}</p>
                  <p className="mt-0.5 text-[10px] leading-snug text-muted-foreground">
                    {t.description}
                  </p>
                </div>
              ))}
            </div>
            <div className="border-t pt-2 text-[10px] text-muted-foreground">
              <p className="font-medium">엔드포인트:</p>
              <p>GET /api/mcp/tools/list</p>
              <p>POST /api/mcp/tools/call</p>
              <p>POST /api/agent/chat</p>
            </div>
          </CardContent>
        </Card>

        <Card className="border-dashed">
          <CardContent className="py-3 text-[10px] text-muted-foreground">
            <p className="flex items-center gap-1 font-medium text-foreground">
              <Sparkles className="h-3 w-3" /> 동작 방식
            </p>
            <ol className="mt-1.5 ml-4 list-decimal space-y-0.5">
              <li>키워드 패턴 매칭 (VIN/국가/명령어) → 즉시 tool 호출</li>
              <li>매칭 실패 시 LLM 이 자연어 응답 + tool 추천</li>
              <li>Tool 결과는 자연어로 포맷, UI 에 액션 버튼 노출</li>
            </ol>
          </CardContent>
        </Card>
      </aside>
    </div>
  );
}

function Turn({
  turn,
  onQuickAction,
}: {
  turn: ChatTurn;
  onQuickAction: (text: string) => void;
}) {
  const isUser = turn.role === "user";
  return (
    <div className={cn("flex gap-3", isUser && "flex-row-reverse")}>
      <div
        className={cn(
          "flex h-7 w-7 shrink-0 items-center justify-center rounded-full",
          isUser ? "bg-primary text-primary-foreground" : "bg-muted",
        )}
      >
        {isUser ? <UserIcon className="h-3.5 w-3.5" /> : <Bot className="h-3.5 w-3.5" />}
      </div>
      <div className={cn("flex max-w-[75%] flex-col gap-2", isUser && "items-end")}>
        <div
          className={cn(
            "rounded-lg px-3 py-2 text-sm",
            isUser ? "bg-primary text-primary-foreground" : "bg-muted",
          )}
        >
          {turn.pending ? (
            <span className="flex items-center gap-1 text-xs text-muted-foreground">
              <Loader2 className="h-3 w-3 animate-spin" />
              처리 중…
            </span>
          ) : (
            <p className="whitespace-pre-wrap leading-relaxed">{turn.text}</p>
          )}
          {turn.error && (
            <p className="mt-2 rounded bg-destructive/10 p-2 text-xs text-destructive">
              {turn.error}
            </p>
          )}
        </div>

        {turn.tool_calls && turn.tool_calls.length > 0 && (
          <div className="space-y-1">
            {turn.tool_calls.map((tc, i) => (
              <details key={i} className="rounded-md border border-border/60 bg-card text-xs">
                <summary className="flex cursor-pointer items-center gap-2 px-2 py-1.5">
                  <Terminal className="h-3 w-3" />
                  <span className="font-mono">{tc.tool}</span>
                  <Badge
                    variant={tc.ok ? "default" : "destructive"}
                    className={cn("text-[9px]", tc.ok && "bg-emerald-500")}
                  >
                    {tc.ok ? "ok" : "err"}
                  </Badge>
                </summary>
                <div className="border-t bg-muted/30 px-2 py-1.5">
                  <p className="text-[10px] font-medium text-muted-foreground">arguments</p>
                  <pre className="overflow-x-auto text-[10px]">
                    {JSON.stringify(tc.arguments, null, 2)}
                  </pre>
                  <p className="mt-1 text-[10px] font-medium text-muted-foreground">
                    {tc.ok ? "data" : "error"}
                  </p>
                  <pre className="max-h-48 overflow-auto text-[10px]">
                    {JSON.stringify(tc.ok ? tc.data : tc.error, null, 2)}
                  </pre>
                </div>
              </details>
            ))}
          </div>
        )}

        {turn.suggested_actions && turn.suggested_actions.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {turn.suggested_actions.map((a, i) =>
              a.to ? (
                <Link
                  key={i}
                  to={a.to}
                  className="rounded-md border border-primary/40 bg-primary/5 px-2 py-0.5 text-[11px] text-primary hover:bg-primary/10"
                >
                  → {a.label}
                </Link>
              ) : (
                <button
                  key={i}
                  type="button"
                  onClick={() => onQuickAction(a.label)}
                  className="rounded-md border border-dashed border-border px-2 py-0.5 text-[11px] text-muted-foreground hover:bg-accent hover:text-foreground"
                >
                  {a.label}
                </button>
              ),
            )}
          </div>
        )}
      </div>
    </div>
  );
}
