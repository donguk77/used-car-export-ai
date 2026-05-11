import { useMemo } from "react";
import { useQueries, useQuery, type UseQueryResult } from "@tanstack/react-query";
import { AlertTriangle, CheckCircle2, Loader2, XCircle } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import { COUNTRY_FLAG } from "@/lib/constants";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";
import type { ImportCheckResponse } from "@/types/api";

// 백엔드 GET /api/countries 응답 shape — name_en/name_ko 만 사용
interface CountryListItem {
  code: string;
  name_en: string | null;
  name_ko: string | null;
  is_blocked: boolean;
  is_sanctioned: boolean;
}

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
  // findings #055 — 5국 hardcoded → 백엔드 GET /api/countries 28국 동적 fetch.
  // is_blocked 국가 (ZA/MM/TH/MY/SD) 는 미리 제외해서 import-check 호출 줄임.
  const countriesQ = useQuery({
    queryKey: ["countries-list"],
    queryFn: async (): Promise<CountryListItem[]> => {
      const r = await api.get<CountryListItem[]>("/api/countries");
      return r.data;
    },
    staleTime: 5 * 60_000,  // 5분 — 국가 마스터 데이터는 자주 안 바뀜
  });

  // 평가 대상 = is_blocked 아닌 국가 (auto-block 은 따로 표시 안 함)
  const evaluatable = useMemo(
    () => (countriesQ.data ?? []).filter((c) => !c.is_blocked),
    [countriesQ.data],
  );

  // queryKey 는 룰엔진에 영향을 주는 필드만 normalized 객체로 — TanStack 구조적 동등.
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
    queries: evaluatable.map((c) => ({
      queryKey: ["import-check", c.code, ruleAffectingFields],
      queryFn: async (): Promise<ImportCheckResponse> => {
        const r = await api.post<ImportCheckResponse>("/api/listings/import-check", {
          destination_country: c.code,
          vehicle,
        });
        return r.data;
      },
      enabled:
        enabled
        && Boolean(vehicle.steering && vehicle.body_type)
        && evaluatable.length > 0,
      staleTime: 60_000,
    })),
  });

  const total = countriesQ.data?.length ?? 0;
  const blockedCount = (countriesQ.data ?? []).filter((c) => c.is_blocked).length;

  return (
    <Card>
      <CardContent className="p-4">
        <div className="mb-3 flex items-center justify-between">
          <h3 className="text-sm font-semibold">
            통관 가능국 ({total}국 — 자동차단 {blockedCount}국 제외)
          </h3>
          <span className="text-[10px] uppercase tracking-wider text-muted-foreground">
            Live
          </span>
        </div>

        {countriesQ.isLoading && (
          <p className="rounded-md bg-muted/50 px-3 py-6 text-center text-xs text-muted-foreground">
            국가 목록 로딩…
          </p>
        )}

        {countriesQ.isError && (
          <p className="rounded-md bg-destructive/5 px-3 py-6 text-center text-xs text-destructive">
            국가 목록 로딩 실패 — 백엔드 연결 확인
          </p>
        )}

        {countriesQ.data && (!enabled || !vehicle.steering || !vehicle.body_type) && (
          <p className="rounded-md bg-muted/50 px-3 py-6 text-center text-xs text-muted-foreground">
            VIN 입력 또는 핸들·차종 입력 후 자동 평가
          </p>
        )}

        {countriesQ.data && enabled && vehicle.steering && vehicle.body_type && (
          <div className="grid grid-cols-1 gap-1.5 sm:grid-cols-2">
            {evaluatable.map((c, i) => (
              <CountryRow
                key={c.code}
                code={c.code}
                nameKo={c.name_ko ?? c.name_en ?? c.code}
                isSanctioned={c.is_sanctioned}
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
  nameKo,
  isSanctioned,
  query,
}: {
  code: string;
  nameKo: string;
  isSanctioned: boolean;
  query: UseQueryResult<ImportCheckResponse>;
}) {
  const flag = COUNTRY_FLAG[code] ?? "🌐";
  const name = nameKo;

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
        <span className="min-w-0 flex-1 truncate font-medium">{name}</span>
        {isSanctioned && (
          <AlertTriangle className="h-3 w-3 text-warning" aria-label="제재" />
        )}
        {ok ? (
          <span className="flex items-center gap-1 text-xs font-semibold text-success">
            <CheckCircle2 className="h-3.5 w-3.5" /> OK
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
