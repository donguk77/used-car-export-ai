import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Car, FileText, Loader2, Pencil, Plus, Trash2 } from "lucide-react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { CountryMatrix } from "@/components/CountryMatrix";
import { CreateListingModal } from "@/components/CreateListingModal";
import { PriceSuggestion } from "@/components/PriceSuggestion";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";
import { FUEL_LABEL, VEHICLE_STATUS_LABEL, VEHICLE_STATUS_VARIANT } from "@/lib/constants";
import { formatApiError, formatPrice } from "@/lib/utils";
import type { Vehicle } from "@/types/api";

export function VehicleDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [createListingOpen, setCreateListingOpen] = useState(false);

  const { data: vehicle, isLoading, isError, error } = useQuery({
    queryKey: ["vehicles", "detail", id],
    queryFn: async (): Promise<Vehicle> => {
      const r = await api.get<Vehicle>(`/api/vehicles/${id}`);
      return r.data;
    },
    enabled: Boolean(id),
  });

  const deleteMutation = useMutation({
    mutationFn: async () => {
      await api.delete(`/api/vehicles/${id}`);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["vehicles"] });
      qc.invalidateQueries({ queryKey: ["dashboard-summary"] });
      navigate("/vehicles");
    },
  });

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="h-8 w-1/3 animate-pulse rounded bg-muted" />
        <Card>
          <CardContent className="h-64 animate-pulse" />
        </Card>
      </div>
    );
  }

  if (isError || !vehicle) {
    return (
      <Card>
        <CardContent className="py-8 text-sm">
          <p className="font-medium text-destructive">매물을 찾을 수 없습니다</p>
          <p className="mt-1 text-muted-foreground">
            {formatApiError(error) || "이미 삭제됐거나 ID가 잘못됐을 수 있습니다."}
          </p>
          <Link
            to="/vehicles"
            className="mt-3 inline-flex items-center gap-1 text-xs underline"
          >
            <ArrowLeft className="h-3 w-3" /> 매물 목록으로
          </Link>
        </CardContent>
      </Card>
    );
  }

  const statusVariant = VEHICLE_STATUS_VARIANT[vehicle.status] ?? "outline";
  const fuelLabel = FUEL_LABEL[vehicle.fuel_type ?? ""] ?? vehicle.fuel_type ?? "—";

  return (
    <div className="space-y-6">
      <header>
        <Link
          to="/vehicles"
          className="mb-1 inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="h-3 w-3" /> 매물 목록
        </Link>
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <h2 className="text-2xl font-semibold tracking-tight">
              {vehicle.make} {vehicle.model} {vehicle.year}
            </h2>
            <p className="mt-1 flex items-center gap-2 text-sm text-muted-foreground">
              <Badge variant={statusVariant}>
                {VEHICLE_STATUS_LABEL[vehicle.status] ?? vehicle.status}
              </Badge>
              {vehicle.steering && <Badge variant="outline">{vehicle.steering}</Badge>}
              {vehicle.vin && (
                <span className="font-mono text-xs">VIN {vehicle.vin}</span>
              )}
            </p>
          </div>
          <div className="flex gap-2">
            <Button onClick={() => setCreateListingOpen(true)} className="gap-2">
              <Plus className="h-4 w-4" /> 이 매물로 거래 만들기
            </Button>
            <Link
              to={`/vehicles/${vehicle.id}/edit`}
              className="inline-flex h-9 items-center gap-2 rounded-md border border-input bg-background px-4 text-sm font-medium hover:bg-accent"
            >
              <Pencil className="h-4 w-4" /> 수정
            </Link>
            <Button
              variant="destructive"
              onClick={() => {
                if (confirm("이 매물을 삭제하시겠습니까? 되돌릴 수 없습니다.")) {
                  deleteMutation.mutate();
                }
              }}
              disabled={deleteMutation.isPending}
              className="gap-2"
            >
              {deleteMutation.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Trash2 className="h-4 w-4" />
              )}
              삭제
            </Button>
          </div>
        </div>
      </header>

      {deleteMutation.isError && (
        <div className="flex items-start justify-between gap-3 rounded-md border border-destructive/30 bg-destructive/5 p-3 text-sm">
          <div>
            <p className="font-medium text-destructive">삭제 실패</p>
            <p className="mt-1 text-xs text-muted-foreground">
              {formatApiError(deleteMutation.error)}
            </p>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => deleteMutation.mutate()}
            disabled={deleteMutation.isPending}
          >
            다시 시도
          </Button>
        </div>
      )}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1fr_360px]">
        {/* 좌측 — 차량 상세 */}
        <div className="space-y-4">
          {/* 차량 이미지 placeholder */}
          <Card>
            <CardContent className="p-0">
              <div className="relative aspect-video overflow-hidden bg-gradient-to-br from-muted to-muted/40">
                {vehicle.image_url ? (
                  <img
                    src={vehicle.image_url}
                    alt={`${vehicle.make ?? ""} ${vehicle.model ?? ""} ${vehicle.year ?? ""}`.trim()}
                    className="h-full w-full object-cover"
                  />
                ) : (
                  <div className="flex h-full w-full items-center justify-center">
                    <Car className="h-32 w-32 text-muted-foreground/40" />
                  </div>
                )}
                <div className="absolute right-3 top-3 flex gap-2">
                  <Badge variant={statusVariant}>
                    {VEHICLE_STATUS_LABEL[vehicle.status] ?? vehicle.status}
                  </Badge>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* 사양 표 */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">차량 사양</CardTitle>
            </CardHeader>
            <CardContent className="grid grid-cols-2 gap-x-4 gap-y-3 sm:grid-cols-3">
              <Spec label="제조사" value={vehicle.make} />
              <Spec label="모델" value={vehicle.model} />
              <Spec label="연식" value={vehicle.year} />
              <Spec label="차종" value={vehicle.body_type} />
              <Spec label="연료" value={fuelLabel} />
              <Spec label="배기량" value={vehicle.engine_cc ? `${vehicle.engine_cc}cc` : "—"} />
              <Spec label="변속기" value={vehicle.transmission} />
              <Spec label="핸들" value={vehicle.steering} />
              <Spec
                label="주행거리"
                value={vehicle.mileage_km ? `${vehicle.mileage_km.toLocaleString()} km` : "—"}
              />
              <Spec label="외장색" value={vehicle.color_exterior} />
              <Spec label="HS Code" value={vehicle.hs_code} />
              <Spec label="가격" value={formatPrice(vehicle.list_price_usd)} />
              <Spec label="제조일" value={vehicle.manufacture_date} />
              <Spec label="최초등록일" value={vehicle.registration_date} />
              <Spec label="선적항" value={vehicle.port_of_loading ?? "Incheon"} />
            </CardContent>
          </Card>

          {/* 다음 단계 CTA */}
          <Card>
            <CardContent className="flex items-center gap-4 py-5">
              <FileText className="h-8 w-8 shrink-0 text-primary" />
              <div className="flex-1">
                <p className="font-medium">바이어 매칭 + 거래 시작</p>
                <p className="text-xs text-muted-foreground">
                  통관 OK 인 국가의 바이어와 매칭해서 거래(listing)를 만들면
                  메일·서류 자동화가 시작됩니다.
                </p>
              </div>
              <Button onClick={() => setCreateListingOpen(true)} className="gap-2">
                <Plus className="h-4 w-4" /> 거래 만들기
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* 우측 — 시세 + 통관 매트릭스 */}
        <aside className="space-y-4 lg:sticky lg:top-6 lg:self-start">
          <PriceSuggestion
            vehicleId={vehicle.id}
            currentListPriceUsd={vehicle.list_price_usd ?? null}
          />
          <CountryMatrix vehicle={vehicle} />
        </aside>
      </div>

      <CreateListingModal
        open={createListingOpen}
        onClose={() => setCreateListingOpen(false)}
        prefillVehicleId={vehicle.id}
      />
    </div>
  );
}

function Spec({ label, value }: { label: string; value: string | number | null | undefined }) {
  return (
    <div>
      <p className="text-[10px] uppercase tracking-wider text-muted-foreground">{label}</p>
      <p className="text-sm font-medium">{value ?? "—"}</p>
    </div>
  );
}
