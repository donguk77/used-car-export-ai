import { useQueries, type UseQueryResult } from "@tanstack/react-query";
import { AlertTriangle, CheckCircle2, Loader2, XCircle } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import { COUNTRY_FLAG } from "@/lib/constants";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";
import type { ImportCheckResponse } from "@/types/api";

// PoC 시드된 5개국
const POC_COUNTRIES = ["DO", "KE", "LY", "KG", "SY"] as const;
const COUNTRY_NAME: Record<string, string> = {
  DO: "도미니카공화국",
  KE: "케냐",
  LY: "리비아",
  KG: "키르기스스탄",
  SY: "시리아",
};

export interface VehicleSnapshot {
  vin?: string | null;
  make?: string | null;
  model?: string | null;
  year?: number | null;
  body_type?: string | null;
  fuel_type?: string | null;
  engine_cc?: number | null;
  steering?: string | null;
  list_price_usd?: number | null;
  manufacture_date?: string | null;
  registration_date?: string | null;
}

export function CountryMatrix({
  vehicle,
  enabled = true,
}: {
  vehicle: VehicleSnapshot;
  enabled?: boolean;
}) {
  // 5개국에 대해 동시 import-check.
  // queryKey 는 룰엔진에 영향을 주는 필드만 normalized 객체로 — TanStack 이 구조적 동등 비교.
  // (이전: JSON.stringify(vehicle) 는 키 순서 변경·매 키스트로크마다 새 캐시 = 폭주.)
  const ruleAffectingFields = {
    body_type: vehicle.body_type ?? null,
    fuel_type: vehicle.fuel_type ?? null,
    engine_cc: vehicle.engine_cc ?? null,
    steering: vehicle.steering ?? null,
    list_price_usd: vehicle.list_price_usd ?? null,
    manufacture_date: vehicle.manufacture_date ?? null,
    registration_date: vehicle.registration_date ?? null,
    year: vehicle.year ?? null,
  };
  const queries = useQueries({
    queries: POC_COUNTRIES.map((code) => ({
      queryKey: ["import-check", code, ruleAffectingFields],
      queryFn: async (): Promise<ImportCheckResponse> => {
        const r = await api.post<ImportCheckResponse>("/api/listings/import-check", {
          destination_country: code,
          vehicle,
        });
        return r.data;
      },
      enabled: enabled && Boolean(vehicle.steering && vehicle.body_type),
      staleTime: 60_000,
    })),
  });

  return (
    <Card>
      <CardContent className="p-4">
        <div className="mb-3 flex items-center justify-between">
          <h3 className="text-sm font-semibold">통관 가능국 (5개국 PoC)</h3>
          <span className="text-[10px] uppercase tracking-wider text-muted-foreground">
            Live
          </span>
        </div>

        {!enabled || !vehicle.steering || !vehicle.body_type ? (
          <p className="rounded-md bg-muted/50 px-3 py-6 text-center text-xs text-muted-foreground">
            VIN 입력 또는 핸들·차종 입력 후 자동 평가
          </p>
        ) : (
          <div className="space-y-2">
            {POC_COUNTRIES.map((code, i) => (
              <CountryRow
                key={code}
                code={code}
                query={queries[i] as UseQueryResult<ImportCheckResponse>}
              />
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function CountryRow({
  code,
  query,
}: {
  code: string;
  query: UseQueryResult<ImportCheckResponse>;
}) {
  const flag = COUNTRY_FLAG[code] ?? "🌐";
  const name = COUNTRY_NAME[code] ?? code;

  if (query.isLoading) {
    return (
      <div className="flex items-center gap-3 rounded-md border bg-muted/20 px-3 py-2 text-sm">
        <span className="text-base">{flag}</span>
        <span className="flex-1 font-medium">{name}</span>
        <Loader2 className="h-3.5 w-3.5 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (query.isError || !query.data) {
    return (
      <div className="flex items-center gap-3 rounded-md border border-destructive/30 bg-destructive/5 px-3 py-2 text-sm">
        <span className="text-base">{flag}</span>
        <span className="flex-1 font-medium">{name}</span>
        <span className="text-[10px] text-destructive">평가 실패</span>
      </div>
    );
  }

  const data = query.data;
  const ok = data.can_import;
  const reasons = data.rule_check?.reasons ?? [];
  const warnings = data.rule_check?.warnings ?? [];

  return (
    <details
      className={cn(
        "rounded-md border transition-colors",
        ok
          ? "border-success/30 bg-success/5"
          : reasons.length > 0
            ? "border-destructive/30 bg-destructive/5"
            : "border-warning/30 bg-warning/5",
      )}
    >
      <summary className="flex cursor-pointer items-center gap-3 px-3 py-2 text-sm">
        <span className="text-base">{flag}</span>
        <span className="flex-1 font-medium">{name}</span>
        {ok ? (
          <span className="flex items-center gap-1 text-xs font-semibold text-success">
            <CheckCircle2 className="h-3.5 w-3.5" /> 통관 OK
          </span>
        ) : (
          <span className="flex items-center gap-1 text-xs font-semibold text-destructive">
            <XCircle className="h-3.5 w-3.5" /> 차단
          </span>
        )}
      </summary>
      {(reasons.length > 0 || warnings.length > 0) && (
        <div className="space-y-1 border-t px-3 py-2 text-xs">
          {reasons.map((r, idx) => (
            <p key={`r-${idx}`} className="flex items-start gap-1.5 text-destructive">
              <XCircle className="mt-0.5 h-3 w-3 shrink-0" />
              <span>{r}</span>
            </p>
          ))}
          {warnings.map((w, idx) => (
            <p key={`w-${idx}`} className="flex items-start gap-1.5 text-warning">
              <AlertTriangle className="mt-0.5 h-3 w-3 shrink-0" />
              <span>{w}</span>
            </p>
          ))}
        </div>
      )}
    </details>
  );
}
