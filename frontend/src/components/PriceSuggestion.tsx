import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { DollarSign, Info, Loader2, TrendingDown, TrendingUp } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";

interface PriceFactor {
  label: string;
  delta_pct: number;
  reason: string;
}

interface PriceSuggestionData {
  suggested_fob_usd: number;
  range_low: number;
  range_high: number;
  confidence: "high" | "medium" | "low";
  method: string;
  n_samples: number;
  baseline_usd: number;
  factors: PriceFactor[];
  notes: string[];
}

interface CountryRow {
  code: string;
  name_ko: string | null;
  name_en: string;
  is_blocked: boolean;
}

interface Props {
  vehicleId: string;
  currentListPriceUsd?: number | null;
}

export function PriceSuggestion({ vehicleId, currentListPriceUsd }: Props) {
  const [country, setCountry] = useState<string>("");

  const { data: countries } = useQuery({
    queryKey: ["countries"],
    queryFn: async (): Promise<CountryRow[]> => {
      const r = await api.get<CountryRow[]>("/api/countries");
      return r.data;
    },
    staleTime: 5 * 60_000,
  });

  const { data, isLoading, isError } = useQuery({
    queryKey: ["vehicles", "price", vehicleId, country],
    queryFn: async (): Promise<PriceSuggestionData> => {
      const url = country
        ? `/api/vehicles/${vehicleId}/price-suggestion?destination_country=${country}`
        : `/api/vehicles/${vehicleId}/price-suggestion`;
      const r = await api.get<PriceSuggestionData>(url);
      return r.data;
    },
    enabled: Boolean(vehicleId),
  });

  const diff = useMemo(() => {
    if (!data || !currentListPriceUsd) return null;
    const d = currentListPriceUsd - data.suggested_fob_usd;
    return {
      delta: d,
      pct: (d / data.suggested_fob_usd) * 100,
      direction: d > 0 ? "high" : "low",
    };
  }, [data, currentListPriceUsd]);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between text-base">
          <span className="flex items-center gap-2">
            <DollarSign className="h-4 w-4" /> 적정 수출가 산출
          </span>
          {data && (
            <ConfidenceBadge confidence={data.confidence} />
          )}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <label className="text-xs font-medium text-muted-foreground">
            도착국 (시장 보정 적용)
          </label>
          <select
            value={country}
            onChange={(e) => setCountry(e.target.value)}
            className="mt-1 flex h-8 w-full rounded-md border border-input bg-transparent px-2 text-xs"
          >
            <option value="">— 도착국 미선택 (기준가만) —</option>
            {(countries ?? [])
              .filter((c) => !c.is_blocked)
              .map((c) => (
                <option key={c.code} value={c.code}>
                  {c.code} · {c.name_ko ?? c.name_en}
                </option>
              ))}
          </select>
        </div>

        {isLoading && (
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Loader2 className="h-3 w-3 animate-spin" /> 시세 분석 중…
          </div>
        )}

        {isError && (
          <p className="text-xs text-destructive">시세 산출 실패. 차종·연료·연식이 입력됐는지 확인하세요.</p>
        )}

        {data && (
          <>
            <div className="rounded-lg bg-primary/5 p-4 text-center">
              <p className="text-[10px] uppercase tracking-wider text-muted-foreground">
                추천 FOB USD
              </p>
              <p className="mt-1 text-3xl font-bold text-primary">
                ${data.suggested_fob_usd.toLocaleString(undefined, { maximumFractionDigits: 0 })}
              </p>
              <p className="mt-1 text-xs text-muted-foreground">
                ${data.range_low.toLocaleString(undefined, { maximumFractionDigits: 0 })} ~
                ${data.range_high.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                {" "}(±15%)
              </p>
            </div>

            {diff && (
              <div className={cn(
                "flex items-center gap-2 rounded-md border px-3 py-2 text-xs",
                diff.direction === "high"
                  ? "border-amber-300 bg-amber-50 text-amber-800"
                  : "border-blue-300 bg-blue-50 text-blue-800",
              )}>
                {diff.direction === "high" ? (
                  <TrendingUp className="h-3 w-3" />
                ) : (
                  <TrendingDown className="h-3 w-3" />
                )}
                <span>
                  현재 등록가 ${currentListPriceUsd?.toLocaleString()}
                  {" — "}추천가 대비 <strong>{diff.pct >= 0 ? "+" : ""}{diff.pct.toFixed(1)}%</strong>
                </span>
              </div>
            )}

            <div className="space-y-1.5">
              <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                산출 근거
              </p>
              <div className="rounded-md bg-muted/40 px-3 py-2 text-xs">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Baseline (시세표)</span>
                  <span className="font-mono">${data.baseline_usd.toLocaleString(undefined, { maximumFractionDigits: 0 })}</span>
                </div>
                <div className="mt-1 flex justify-between text-[10px] text-muted-foreground">
                  <span>방법: {data.method}</span>
                  <span>동급 표본 {data.n_samples}건</span>
                </div>
              </div>

              {data.factors.length > 0 && (
                <ul className="space-y-1">
                  {data.factors.map((f, i) => (
                    <li key={i} className="flex items-start justify-between rounded border border-border/50 px-2 py-1.5 text-xs">
                      <div>
                        <p className="font-medium">{f.label}</p>
                        <p className="text-[10px] text-muted-foreground">{f.reason}</p>
                      </div>
                      <Badge
                        variant={f.delta_pct >= 0 ? "default" : "outline"}
                        className={cn(
                          "shrink-0 text-[10px]",
                          f.delta_pct >= 0 ? "bg-emerald-500" : "border-rose-300 text-rose-600",
                        )}
                      >
                        {f.delta_pct >= 0 ? "+" : ""}{f.delta_pct.toFixed(1)}%
                      </Badge>
                    </li>
                  ))}
                </ul>
              )}

              {data.notes.length > 0 && (
                <div className="flex items-start gap-1.5 pt-1 text-[10px] text-muted-foreground">
                  <Info className="mt-0.5 h-3 w-3 shrink-0" />
                  <ul className="space-y-0.5">
                    {data.notes.map((n, i) => (
                      <li key={i}>{n}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            {currentListPriceUsd == null && (
              <ApplyButton vehicleId={vehicleId} suggested={data.suggested_fob_usd} />
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}

function ConfidenceBadge({ confidence }: { confidence: string }) {
  const colors: Record<string, string> = {
    high: "bg-emerald-500",
    medium: "bg-amber-500",
    low: "bg-slate-400",
  };
  const labels: Record<string, string> = {
    high: "신뢰도 높음",
    medium: "신뢰도 보통",
    low: "신뢰도 낮음",
  };
  return (
    <Badge className={cn("text-[10px]", colors[confidence] ?? "bg-slate-400")}>
      {labels[confidence] ?? confidence}
    </Badge>
  );
}

function ApplyButton({ vehicleId, suggested }: { vehicleId: string; suggested: number }) {
  const qc = useQueryClient();
  const [error, setError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: async () => {
      const r = await api.patch(`/api/vehicles/${vehicleId}`, {
        list_price_usd: Math.round(suggested),
      });
      return r.data;
    },
    onSuccess: () => {
      // window.location.reload() 안티패턴 제거 — TanStack Query invalidate 로
      // 영향 받는 쿼리만 갱신 (cache 보존, chat state 등 유지)
      qc.invalidateQueries({ queryKey: ["vehicles"] });
      qc.invalidateQueries({ queryKey: ["vehicles", "detail", vehicleId] });
      qc.invalidateQueries({ queryKey: ["vehicles", "price", vehicleId] });
      setError(null);
    },
    onError: (e) => {
      setError(e instanceof Error ? e.message : String(e));
    },
  });

  return (
    <div className="space-y-1">
      <Button
        onClick={() => mutation.mutate()}
        disabled={mutation.isPending}
        className="w-full gap-2"
        variant="outline"
        size="sm"
      >
        {mutation.isPending && <Loader2 className="h-3 w-3 animate-spin" />}
        추천가를 등록가로 반영
      </Button>
      {error && (
        <p className="text-[10px] text-destructive">{error}</p>
      )}
    </div>
  );
}
