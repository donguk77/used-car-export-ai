import { useMemo, useState } from "react";
import { Car, Plus, Search } from "lucide-react";
import { Link } from "react-router-dom";

import { EmptyState } from "@/components/EmptyState";
import { VehicleCardSkeleton } from "@/components/Skeleton";
import { StatusFilter, type FilterOption } from "@/components/StatusFilter";
import { VehicleCard } from "@/components/VehicleCard";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useVehicles } from "@/hooks/useVehicles";
import { VEHICLE_STATUS_LABEL } from "@/lib/constants";
import { formatApiError } from "@/lib/utils";
import type { Vehicle } from "@/types/api";

export function VehiclesPage() {
  const [statusFilter, setStatusFilter] = useState<string | null>(null);
  const [search, setSearch] = useState("");

  // 전체를 한 번 받아 클라이언트 사이드 카운트 (PoC 단계 — 매물 적음)
  const { data: allVehicles, isLoading, isError, error } = useVehicles();

  const filtered = useMemo<Vehicle[]>(() => {
    if (!allVehicles) return [];
    let list = allVehicles;
    if (statusFilter) list = list.filter((v) => v.status === statusFilter);
    if (search.trim()) {
      const q = search.toLowerCase();
      list = list.filter((v) =>
        [v.vin, v.make, v.model, String(v.year), v.color_exterior]
          .filter(Boolean)
          .some((field) => field!.toLowerCase().includes(q)),
      );
    }
    return list;
  }, [allVehicles, statusFilter, search]);

  const filterOptions = useMemo<FilterOption[]>(() => {
    if (!allVehicles) return [{ value: null, label: "전체" }];
    const counts: Record<string, number> = {};
    for (const v of allVehicles) counts[v.status] = (counts[v.status] ?? 0) + 1;
    const opts: FilterOption[] = [{ value: null, label: "전체", count: allVehicles.length }];
    for (const [status, count] of Object.entries(counts)) {
      opts.push({
        value: status,
        label: VEHICLE_STATUS_LABEL[status] ?? status,
        count,
      });
    }
    return opts;
  }, [allVehicles]);

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight">매물</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            등록된 차량 {allVehicles?.length ?? 0}대 · 통관 가능 국가 자동 판정
          </p>
        </div>
        <Link
          to="/vehicles/new"
          className="inline-flex h-9 items-center gap-1.5 rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground shadow-sm transition-colors hover:bg-primary/90"
        >
          <Plus className="h-4 w-4" />
          새 매물 등록
        </Link>
      </header>

      {/* 필터 + 검색 */}
      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <StatusFilter options={filterOptions} value={statusFilter} onChange={setStatusFilter} />
        <div className="relative lg:w-72">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            type="search"
            placeholder="VIN · 제조사 · 모델 · 연식 검색"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
      </div>

      {/* 그리드 */}
      {isLoading && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <VehicleCardSkeleton key={i} />
          ))}
        </div>
      )}

      {isError && (
        <Card>
          <CardContent className="py-8 text-sm">
            <p className="font-medium text-destructive">매물을 불러오지 못했습니다.</p>
            <p className="mt-1 text-muted-foreground">
              백엔드 서버가 켜져 있는지 확인하세요.
            </p>
            <p className="mt-2 text-xs text-muted-foreground">
              {formatApiError(error)}
            </p>
          </CardContent>
        </Card>
      )}

      {!isLoading && !isError && filtered.length === 0 && (
        <EmptyState
          icon={Car}
          title={
            allVehicles && allVehicles.length === 0
              ? "등록된 매물이 없습니다"
              : "검색 결과가 없습니다"
          }
          description={
            allVehicles && allVehicles.length === 0
              ? "VIN 입력만으로 차량 정보가 자동 채워지고, 5개국 통관 가능성이 즉시 판정됩니다."
              : "필터를 해제하거나 다른 검색어를 입력해보세요."
          }
          action={
            allVehicles && allVehicles.length === 0 ? (
              <Link
                to="/vehicles/new"
                className="inline-flex h-9 items-center gap-1.5 rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground hover:bg-primary/90"
              >
                <Plus className="h-4 w-4" />첫 매물 등록
              </Link>
            ) : null
          }
        />
      )}

      {!isLoading && !isError && filtered.length > 0 && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {filtered.map((v) => (
            <VehicleCard key={v.id} vehicle={v} />
          ))}
        </div>
      )}
    </div>
  );
}
