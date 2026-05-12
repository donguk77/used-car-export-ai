import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";

import { COUNTRY_FLAG } from "@/lib/constants";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";

interface CountryOpt {
  code: string;
  name_en: string | null;
  name_ko: string | null;
  is_blocked: boolean;
  is_sanctioned: boolean;
}

/**
 * 28국 도착국 dropdown — GET /api/countries 동적.
 * Auto-blocked 국가는 disabled + (수출 불가) 표시.
 * Sanctioned 국가는 ⚠ 마크하지만 선택 가능 (warning 으로 거래 등록).
 *
 * CreateListingModal + QuoteRequestModal 두 곳에서 재사용.
 * Free-text ISO-2 Input 보다 UX 우수 + 오타 방지 + 28국 시인성.
 */
export function CountrySelect({
  id,
  value,
  onChange,
  required,
  className,
  disabled,
}: {
  id?: string;
  value: string;
  onChange: (code: string) => void;
  required?: boolean;
  className?: string;
  disabled?: boolean;
}) {
  const countriesQ = useQuery({
    queryKey: ["countries-list"],
    queryFn: async (): Promise<CountryOpt[]> => {
      const r = await api.get<CountryOpt[]>("/api/countries");
      return r.data;
    },
    staleTime: 5 * 60_000,
  });

  // 평가가능국 먼저, 자동차단 국가 (disabled) 그 다음 — 한국어 가나다 순
  const sorted = useMemo(() => {
    const list = countriesQ.data ?? [];
    return [...list].sort((a, b) => {
      // blocked 국가는 맨 아래
      if (a.is_blocked !== b.is_blocked) return a.is_blocked ? 1 : -1;
      // 그 외 한국어 이름 가나다
      const an = a.name_ko ?? a.name_en ?? a.code;
      const bn = b.name_ko ?? b.name_en ?? b.code;
      return an.localeCompare(bn, "ko");
    });
  }, [countriesQ.data]);

  if (countriesQ.isLoading) {
    return (
      <select
        id={id}
        disabled
        className={cn(
          "mt-1 flex h-9 w-full rounded-md border border-input bg-muted px-3 py-1 text-sm",
          className,
        )}
      >
        <option>국가 목록 로딩…</option>
      </select>
    );
  }

  if (countriesQ.isError) {
    return (
      <p className="mt-1 text-xs text-destructive">
        국가 목록 로딩 실패 — 백엔드 연결 확인
      </p>
    );
  }

  return (
    <select
      id={id}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      required={required}
      disabled={disabled}
      className={cn(
        "mt-1 flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm",
        "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring",
        "disabled:opacity-60",
        className,
      )}
    >
      <option value="">— 도착국을 선택하세요 —</option>
      {sorted.map((c) => {
        const flag = COUNTRY_FLAG[c.code] ?? "🌐";
        const name = c.name_ko ?? c.name_en ?? c.code;
        const suffix = c.is_blocked
          ? " (수출 불가)"
          : c.is_sanctioned
            ? " ⚠ 제재"
            : "";
        return (
          <option key={c.code} value={c.code} disabled={c.is_blocked}>
            {flag} {name} ({c.code}){suffix}
          </option>
        );
      })}
    </select>
  );
}
