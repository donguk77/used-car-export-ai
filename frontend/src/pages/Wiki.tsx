import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { BookOpen, Globe2, Loader2, Plus, Search } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";
import { cn, formatApiError } from "@/lib/utils";

interface CountryRow {
  code: string;
  name_en: string;
  name_ko: string | null;
  region: string | null;
  primary_language: string | null;
  business_language: string | null;
  steering: string | null;
  is_high_risk: boolean;
  is_russia_proxy_risk: boolean;
  is_sanctioned: boolean;
  is_blocked: boolean;
  pre_registration_system: string | null;
  consular_legalization: boolean;
}

const REGIONS: Record<string, string> = {
  africa: "아프리카",
  middle_east: "중동",
  central_asia: "중앙아시아",
  latin_america: "남미·중미",
  southeast_asia: "동남아",
  south_asia: "남아시아",
};

export function WikiPage() {
  const qc = useQueryClient();
  const [filter, setFilter] = useState("");
  const [showNew, setShowNew] = useState(false);

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["countries"],
    queryFn: async (): Promise<CountryRow[]> => {
      const r = await api.get<CountryRow[]>("/api/countries");
      return r.data;
    },
  });

  const countries = data ?? [];
  const filtered = useMemo(() => {
    const f = filter.trim().toLowerCase();
    if (!f) return countries;
    return countries.filter((c) =>
      [c.code, c.name_en, c.name_ko ?? "", c.region ?? ""]
        .some((s) => s.toLowerCase().includes(f)),
    );
  }, [countries, filter]);

  const grouped = useMemo(() => {
    const out: Record<string, CountryRow[]> = {};
    filtered.forEach((c) => {
      const r = c.region ?? "기타";
      out[r] = out[r] ?? [];
      out[r].push(c);
    });
    return out;
  }, [filtered]);

  return (
    <div className="space-y-6">
      <header className="flex items-start justify-between gap-4">
        <div>
          <h2 className="flex items-center gap-2 text-2xl font-semibold tracking-tight">
            <BookOpen className="h-6 w-6" /> LLM Wiki — 국가별 통관 규제
          </h2>
          <p className="mt-1 text-sm text-muted-foreground">
            28국 통관 룰 (연식·핸들·검사·영사관·서류). 룰 엔진과 LLM 메일 작성에 자동 반영됩니다.
          </p>
        </div>
        <Button onClick={() => setShowNew(true)} className="gap-2">
          <Plus className="h-4 w-4" /> 신규 국가
        </Button>
      </header>

      <div className="flex items-center gap-2">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="국가명 / 코드 / 지역 검색"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="pl-9"
          />
        </div>
        <span className="text-sm text-muted-foreground">
          {filtered.length} / {countries.length} 국
        </span>
      </div>

      {isLoading && (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <Card key={i}><CardContent className="h-24 animate-pulse" /></Card>
          ))}
        </div>
      )}

      {isError && (
        <Card>
          <CardContent className="py-8 text-sm">
            <p className="font-medium text-destructive">국가 목록을 불러오지 못했습니다</p>
            <p className="mt-1 text-muted-foreground">{formatApiError(error)}</p>
          </CardContent>
        </Card>
      )}

      {Object.entries(grouped).map(([region, items]) => (
        <section key={region} className="space-y-2">
          <h3 className="text-sm font-semibold text-muted-foreground">
            {REGIONS[region] ?? region} ({items.length})
          </h3>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {items.map((c) => (
              <CountryCard key={c.code} country={c} />
            ))}
          </div>
        </section>
      ))}

      {showNew && (
        <NewCountryModal
          onClose={() => setShowNew(false)}
          onCreated={() => {
            setShowNew(false);
            qc.invalidateQueries({ queryKey: ["countries"] });
          }}
        />
      )}
    </div>
  );
}

function CountryCard({ country: c }: { country: CountryRow }) {
  return (
    <Link
      to={`/wiki/${c.code}`}
      className={cn(
        "block rounded-lg border bg-card p-4 transition-colors hover:bg-accent",
        c.is_blocked && "border-destructive/40",
      )}
    >
      <div className="flex items-start justify-between">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <span className="rounded bg-muted px-1.5 py-0.5 font-mono text-xs">
              {c.code}
            </span>
            <h4 className="truncate text-sm font-semibold">
              {c.name_ko ?? c.name_en}
            </h4>
          </div>
          <p className="mt-0.5 truncate text-xs text-muted-foreground">{c.name_en}</p>
        </div>
        <Globe2 className="h-4 w-4 shrink-0 text-muted-foreground" />
      </div>
      <div className="mt-3 flex flex-wrap gap-1.5">
        {c.steering && (
          <Badge variant="outline" className="text-[10px]">{c.steering}</Badge>
        )}
        {c.business_language && (
          <Badge variant="outline" className="text-[10px]">
            {c.business_language.toUpperCase()}
          </Badge>
        )}
        {c.is_blocked && (
          <Badge variant="destructive" className="text-[10px]">차단</Badge>
        )}
        {c.is_sanctioned && (
          <Badge className="bg-amber-500 text-[10px]">제재</Badge>
        )}
        {c.is_russia_proxy_risk && (
          <Badge className="bg-orange-500 text-[10px]">러우회</Badge>
        )}
        {c.consular_legalization && (
          <Badge variant="outline" className="text-[10px]">영사인증</Badge>
        )}
      </div>
    </Link>
  );
}

function NewCountryModal({
  onClose,
  onCreated,
}: {
  onClose: () => void;
  onCreated: () => void;
}) {
  const [code, setCode] = useState("");
  const [nameEn, setNameEn] = useState("");
  const [nameKo, setNameKo] = useState("");
  const [region, setRegion] = useState("");

  const mutation = useMutation({
    mutationFn: async () => {
      const r = await api.post("/api/countries", {
        code: code.toUpperCase(),
        name_en: nameEn,
        name_ko: nameKo || null,
        region: region || null,
      });
      return r.data;
    },
    onSuccess: onCreated,
  });

  const valid = code.trim().length === 2 && nameEn.trim();

  return (
    <div
      role="dialog"
      aria-modal
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
      onClick={onClose}
    >
      <div
        className="w-full max-w-md rounded-lg border bg-card p-6 shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <h3 className="text-lg font-semibold">신규 국가 추가</h3>
        <p className="mt-1 text-xs text-muted-foreground">
          ISO 3166-1 alpha-2 (예: KW = 쿠웨이트)
        </p>
        <div className="mt-4 space-y-3">
          <div>
            <label className="text-xs font-medium">코드 (2자리) *</label>
            <Input
              value={code}
              onChange={(e) => setCode(e.target.value.toUpperCase().slice(0, 2))}
              placeholder="KW"
              className="font-mono"
              maxLength={2}
            />
          </div>
          <div>
            <label className="text-xs font-medium">영문명 *</label>
            <Input value={nameEn} onChange={(e) => setNameEn(e.target.value)} placeholder="Kuwait" />
          </div>
          <div>
            <label className="text-xs font-medium">한글명</label>
            <Input value={nameKo} onChange={(e) => setNameKo(e.target.value)} placeholder="쿠웨이트" />
          </div>
          <div>
            <label className="text-xs font-medium">지역</label>
            <select
              value={region}
              onChange={(e) => setRegion(e.target.value)}
              className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm"
            >
              <option value="">— 미선택 —</option>
              {Object.entries(REGIONS).map(([k, v]) => (
                <option key={k} value={k}>{v}</option>
              ))}
            </select>
          </div>
        </div>
        {mutation.isError && (
          <p className="mt-3 text-xs text-destructive">{formatApiError(mutation.error)}</p>
        )}
        <div className="mt-5 flex justify-end gap-2">
          <Button variant="ghost" onClick={onClose}>취소</Button>
          <Button
            onClick={() => mutation.mutate()}
            disabled={!valid || mutation.isPending}
            className="gap-2"
          >
            {mutation.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
            추가
          </Button>
        </div>
      </div>
    </div>
  );
}
