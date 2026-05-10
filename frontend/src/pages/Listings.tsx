import { useMemo, useState } from "react";
import { AxiosError } from "axios";
import { CheckCircle2, FileText, Plus, Search, XCircle } from "lucide-react";
import { Link } from "react-router-dom";

import { CreateListingModal } from "@/components/CreateListingModal";
import { EmptyState } from "@/components/EmptyState";
import { Skeleton } from "@/components/Skeleton";
import { StatusFilter, type FilterOption } from "@/components/StatusFilter";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useListings } from "@/hooks/useListings";
import { COUNTRY_FLAG, LISTING_STATUS_LABEL } from "@/lib/constants";
import { formatPrice, shortId } from "@/lib/utils";
import type { Listing, ListingStatus } from "@/types/api";

const STATUS_VARIANT: Record<ListingStatus, "secondary" | "success" | "warning" | "destructive" | "outline"> = {
  inquiry: "outline",
  quoted: "secondary",
  negotiating: "secondary",
  agreed: "secondary",
  documenting: "secondary",
  shipping: "warning",
  in_transit: "warning",
  arrived: "warning",
  cleared: "warning",
  delivered: "success",
  disputed: "destructive",
  closed: "outline",
};

export function ListingsPage() {
  const [statusFilter, setStatusFilter] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [createOpen, setCreateOpen] = useState(false);

  const { data, isLoading, isError, error } = useListings();

  const filtered = useMemo<Listing[]>(() => {
    if (!data) return [];
    let list = data;
    if (statusFilter) list = list.filter((l) => l.status === statusFilter);
    if (search.trim()) {
      const q = search.toLowerCase();
      list = list.filter((l) =>
        [l.destination_country, l.id, l.notes].filter(Boolean).some((field) => field!.toLowerCase().includes(q)),
      );
    }
    return list;
  }, [data, statusFilter, search]);

  const filterOptions = useMemo<FilterOption[]>(() => {
    if (!data) return [{ value: null, label: "전체" }];
    const counts: Record<string, number> = {};
    for (const l of data) counts[l.status] = (counts[l.status] ?? 0) + 1;
    const opts: FilterOption[] = [{ value: null, label: "전체", count: data.length }];
    for (const [status, n] of Object.entries(counts)) {
      opts.push({
        value: status,
        label: LISTING_STATUS_LABEL[status as ListingStatus] ?? status,
        count: n,
      });
    }
    return opts;
  }, [data]);

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight">거래 파이프라인</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            전체 {data?.length ?? 0}건 · 상태별 진행 추적 · 클릭하여 메일·서류 작업
          </p>
        </div>
        <Button onClick={() => setCreateOpen(true)} className="gap-2">
          <Plus className="h-4 w-4" /> 새 거래 만들기
        </Button>
      </header>

      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <StatusFilter options={filterOptions} value={statusFilter} onChange={setStatusFilter} />
        <div className="relative lg:w-72">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            type="search"
            placeholder="국가 · ID · 메모 검색"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
      </div>

      {isLoading && (
        <div className="space-y-2">
          {Array.from({ length: 5 }).map((_, i) => (
            <Card key={i}>
              <CardContent className="space-y-2 p-4">
                <Skeleton className="h-5 w-2/3" />
                <Skeleton className="h-4 w-1/2" />
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {isError && (
        <Card>
          <CardContent className="py-8 text-sm">
            <p className="font-medium text-destructive">거래를 불러오지 못했습니다.</p>
            <p className="mt-2 text-xs text-muted-foreground">
              {error instanceof AxiosError
                ? (error.response?.data?.detail ?? error.message)
                : (error as Error)?.message}
            </p>
          </CardContent>
        </Card>
      )}

      {!isLoading && !isError && filtered.length === 0 && (
        <EmptyState
          icon={FileText}
          title={data && data.length === 0 ? "거래가 없습니다" : "검색 결과가 없습니다"}
          description={
            data && data.length === 0
              ? "매물 + 바이어 + 도착국을 골라 첫 거래를 만들어보세요."
              : "필터를 해제하거나 다른 검색어를 입력해보세요."
          }
          action={
            data && data.length === 0 ? (
              <Button onClick={() => setCreateOpen(true)} className="gap-2">
                <Plus className="h-4 w-4" /> 새 거래 만들기
              </Button>
            ) : undefined
          }
        />
      )}

      {!isLoading && !isError && filtered.length > 0 && (
        <div className="space-y-2">
          {filtered.map((l) => (
            <ListingRow key={l.id} listing={l} />
          ))}
        </div>
      )}

      <CreateListingModal open={createOpen} onClose={() => setCreateOpen(false)} />
    </div>
  );
}

function ListingRow({ listing }: { listing: Listing }) {
  const flag = COUNTRY_FLAG[listing.destination_country ?? ""] ?? "🌐";
  const variant = STATUS_VARIANT[listing.status] ?? "outline";

  return (
    <Link
      to={`/listings/${listing.id}`}
      className="block rounded-lg border bg-card p-4 shadow-sm transition-all hover:border-primary/40 hover:shadow-md"
    >
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <span className="text-lg">{flag}</span>
            <span className="font-mono text-xs text-muted-foreground">
              {shortId(listing.id, 8)}
            </span>
            <span className="text-xs text-muted-foreground">→</span>
            <span className="text-sm font-semibold">{listing.destination_country ?? "—"}</span>
          </div>
          <div className="mt-2 flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
            {listing.incoterm && <span>Incoterm: <strong className="text-foreground">{listing.incoterm}</strong></span>}
            {listing.shipping_method && <span>운송: <strong className="text-foreground">{listing.shipping_method}</strong></span>}
            {listing.port_of_discharge && <span>도착항: <strong className="text-foreground">{listing.port_of_discharge}</strong></span>}
          </div>
        </div>

        <div className="flex flex-col items-end gap-1">
          <Badge variant={variant}>
            {LISTING_STATUS_LABEL[listing.status] ?? listing.status}
          </Badge>
          {listing.can_import === true && (
            <span className="flex items-center gap-1 text-xs text-success">
              <CheckCircle2 className="h-3 w-3" /> 통관 OK
            </span>
          )}
          {listing.can_import === false && (
            <span className="flex items-center gap-1 text-xs text-destructive">
              <XCircle className="h-3 w-3" /> 통관 차단
            </span>
          )}
        </div>
      </div>

      {listing.agreed_price_usd && (
        <div className="mt-3 flex items-baseline justify-between border-t pt-3">
          <span className="text-xs text-muted-foreground">합의 가격</span>
          <span className="text-base font-bold tabular-nums text-primary">
            {formatPrice(listing.agreed_price_usd)}
          </span>
        </div>
      )}
    </Link>
  );
}
