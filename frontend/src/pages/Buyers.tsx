import { useMemo, useState } from "react";
import { Building2, Phone, Plus, Search, ShieldAlert, ShieldCheck, ShieldX } from "lucide-react";
import { Link } from "react-router-dom";

import { EmptyState } from "@/components/EmptyState";
import { Skeleton } from "@/components/Skeleton";
import { StatusFilter, type FilterOption } from "@/components/StatusFilter";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useBuyers } from "@/hooks/useBuyers";
import { COUNTRY_FLAG, SANCTIONS_LABEL, SANCTIONS_VARIANT } from "@/lib/constants";
import { formatApiError } from "@/lib/utils";
import type { Buyer, SanctionsStatus } from "@/types/api";

const SANCTIONS_FILTER_LABELS: Record<string, string> = {
  clean: "정상",
  warning: "주의",
  blocked: "차단",
  unchecked: "미검사",
};

export function BuyersPage() {
  const [filter, setFilter] = useState<string | null>(null);
  const [search, setSearch] = useState("");

  const { data, isLoading, isError, error } = useBuyers();

  const filtered = useMemo<Buyer[]>(() => {
    if (!data) return [];
    let list = data;
    if (filter) list = list.filter((b) => b.sanctions_status === filter);
    if (search.trim()) {
      const q = search.toLowerCase();
      list = list.filter((b) =>
        [b.company_name, b.contact_person, b.country_code, b.tax_id, b.email]
          .filter(Boolean)
          .some((field) => field!.toLowerCase().includes(q)),
      );
    }
    return list;
  }, [data, filter, search]);

  const filterOptions = useMemo<FilterOption[]>(() => {
    if (!data) return [{ value: null, label: "전체" }];
    const counts: Record<string, number> = {};
    for (const b of data) counts[b.sanctions_status] = (counts[b.sanctions_status] ?? 0) + 1;
    const opts: FilterOption[] = [{ value: null, label: "전체", count: data.length }];
    for (const [status, n] of Object.entries(counts)) {
      opts.push({
        value: status,
        label: SANCTIONS_FILTER_LABELS[status] ?? status,
        count: n,
      });
    }
    return opts;
  }, [data]);

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight">바이어</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            등록된 바이어 {data?.length ?? 0}명 · 등록 시 자동 compliance 검사
          </p>
        </div>
        <Link
          to="/buyers/new"
          className="inline-flex h-9 items-center gap-1.5 rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground shadow-sm hover:bg-primary/90"
        >
          <Plus className="h-4 w-4" />
          새 바이어 등록
        </Link>
      </header>

      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <StatusFilter options={filterOptions} value={filter} onChange={setFilter} />
        <div className="relative lg:w-72">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            type="search"
            placeholder="회사명 · 담당자 · 국가 · Tax ID 검색"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
      </div>

      {isLoading && (
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <Card key={i}>
              <CardContent className="space-y-3 p-4">
                <Skeleton className="h-5 w-2/3" />
                <Skeleton className="h-4 w-1/2" />
                <Skeleton className="h-4 w-3/4" />
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {isError && (
        <Card>
          <CardContent className="py-8 text-sm">
            <p className="font-medium text-destructive">바이어를 불러오지 못했습니다.</p>
            <p className="mt-2 text-xs text-muted-foreground">
              {formatApiError(error)}
            </p>
          </CardContent>
        </Card>
      )}

      {!isLoading && !isError && filtered.length === 0 && (
        <EmptyState
          icon={Building2}
          title={data && data.length === 0 ? "등록된 바이어가 없습니다" : "검색 결과가 없습니다"}
          description={
            data && data.length === 0
              ? "회사 정보 입력 즉시 OFAC·러시아 우회·Yestrade 자동 검사가 실행됩니다."
              : "필터를 해제하거나 다른 검색어를 입력해보세요."
          }
          action={
            data && data.length === 0 ? (
              <Link
                to="/buyers/new"
                className="inline-flex h-9 items-center gap-1.5 rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground hover:bg-primary/90"
              >
                <Plus className="h-4 w-4" /> 첫 바이어 등록
              </Link>
            ) : null
          }
        />
      )}

      {!isLoading && !isError && filtered.length > 0 && (
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map((b) => (
            <BuyerCard key={b.id} buyer={b} />
          ))}
        </div>
      )}
    </div>
  );
}

function BuyerCard({ buyer }: { buyer: Buyer }) {
  const flag = COUNTRY_FLAG[buyer.country_code] ?? "🌐";
  const variant = SANCTIONS_VARIANT[buyer.sanctions_status as SanctionsStatus] ?? "outline";
  const SanctionsIcon = sanctionsIcon(buyer.sanctions_status);

  return (
    <Link
      to={`/buyers/${buyer.id}`}
      className="group rounded-lg border bg-card p-4 shadow-sm transition-all hover:border-primary/40 hover:shadow-md"
    >
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <span className="text-xl">{flag}</span>
            <p className="truncate font-semibold leading-tight">{buyer.company_name ?? "—"}</p>
          </div>
          {buyer.contact_person && (
            <p className="mt-1 truncate text-xs text-muted-foreground">{buyer.contact_person}</p>
          )}
        </div>
        <Badge variant={variant}>
          <SanctionsIcon className="mr-1 h-3 w-3" />
          {SANCTIONS_LABEL[buyer.sanctions_status as SanctionsStatus] ?? buyer.sanctions_status}
        </Badge>
      </div>

      <div className="mt-3 space-y-1 text-xs text-muted-foreground">
        {buyer.city && <p className="truncate">{buyer.city}, {buyer.country_code}</p>}
        {buyer.tax_id && (
          <p className="truncate font-mono">Tax: {buyer.tax_id}</p>
        )}
        {buyer.phone && (
          <p className="flex items-center gap-1 truncate">
            <Phone className="h-3 w-3" /> {buyer.phone}
          </p>
        )}
      </div>

      <div className="mt-3 flex items-center justify-between border-t pt-3 text-xs">
        <span className="text-muted-foreground">
          거래 <strong className="text-foreground">{buyer.total_orders}</strong>건
        </span>
        {buyer.russia_proxy_risk_score !== null && buyer.russia_proxy_risk_score > 0 && (
          <span className="text-warning">
            risk score {buyer.russia_proxy_risk_score}
          </span>
        )}
      </div>
    </Link>
  );
}

function sanctionsIcon(status: string): typeof ShieldCheck {
  if (status === "blocked") return ShieldX;
  if (status === "warning") return ShieldAlert;
  return ShieldCheck;
}
