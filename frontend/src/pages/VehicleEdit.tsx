import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Loader2 } from "lucide-react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { CountryMatrix } from "@/components/CountryMatrix";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useDebouncedValue } from "@/hooks/useDebouncedValue";
import { api } from "@/lib/api";
import type { VehicleFormData } from "@/lib/demoVehicles";
import { cn, formatApiError } from "@/lib/utils";
import type { Vehicle } from "@/types/api";

const EMPTY_FORM: VehicleFormData = {
  vin: "",
  make: "",
  model: "",
  year: 0,
  body_type: "",
  fuel_type: "",
  engine_cc: 0,
  transmission: "",
  steering: "LHD",
  mileage_km: 0,
  color_exterior: "",
  list_price_usd: 0,
  hs_code: "",
  manufacture_date: "",
  registration_date: "",
};

export function VehicleEditPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const qc = useQueryClient();

  const [form, setForm] = useState<VehicleFormData>(EMPTY_FORM);
  const set = <K extends keyof VehicleFormData>(key: K, value: VehicleFormData[K]) => {
    setForm((f) => ({ ...f, [key]: value }));
  };

  // 1. 기존 차량 fetch + 폼 prefill
  const { data: vehicle, isLoading, isError, error } = useQuery({
    queryKey: ["vehicles", "detail", id],
    queryFn: async (): Promise<Vehicle> => {
      const r = await api.get<Vehicle>(`/api/vehicles/${id}`);
      return r.data;
    },
    enabled: Boolean(id),
  });

  // vehicle 도착 → form 한 번만 prefill (이후 사용자 편집 보존)
  const [prefilled, setPrefilled] = useState(false);
  useEffect(() => {
    if (!vehicle || prefilled) return;
    setForm({
      vin: vehicle.vin ?? "",
      make: vehicle.make ?? "",
      model: vehicle.model ?? "",
      year: vehicle.year ?? 0,
      body_type: vehicle.body_type ?? "",
      fuel_type: vehicle.fuel_type ?? "",
      engine_cc: vehicle.engine_cc ?? 0,
      transmission: vehicle.transmission ?? "",
      steering: (vehicle.steering as "LHD" | "RHD") ?? "LHD",
      mileage_km: vehicle.mileage_km ?? 0,
      color_exterior: vehicle.color_exterior ?? "",
      list_price_usd: vehicle.list_price_usd ?? 0,
      hs_code: vehicle.hs_code ?? "",
      manufacture_date: vehicle.manufacture_date ?? "",
      registration_date: vehicle.registration_date ?? "",
    });
    setPrefilled(true);
  }, [vehicle, prefilled]);

  // 통관 매트릭스용 — 폼 안정화 후 평가 (~600ms debounce)
  const debouncedForm = useDebouncedValue(form, 600);

  // PATCH /api/vehicles/{id} — 변경된 필드만 보낼 수도 있지만,
  // PoC 단순성 위해 폼 전체 전송 (백엔드 partial update 라 OK)
  const updateMutation = useMutation({
    mutationFn: async (data: VehicleFormData): Promise<Vehicle> => {
      const r = await api.patch<Vehicle>(`/api/vehicles/${id}`, {
        ...data,
        year: data.year || null,
        engine_cc: data.engine_cc || null,
        mileage_km: data.mileage_km || null,
        list_price_usd: data.list_price_usd || null,
        manufacture_date: data.manufacture_date || null,
        registration_date: data.registration_date || null,
      });
      return r.data;
    },
    onSuccess: (v) => {
      qc.invalidateQueries({ queryKey: ["vehicles"] });
      qc.invalidateQueries({ queryKey: ["vehicles", "detail", id] });
      qc.invalidateQueries({ queryKey: ["dashboard-summary"] });
      navigate(`/vehicles/${v.id}`);
    },
  });

  const canSubmit = Boolean(form.make && form.model && form.year && form.steering);

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

  return (
    <div className="space-y-6">
      <header>
        <Link
          to={`/vehicles/${id}`}
          className="mb-1 inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="h-3 w-3" /> 매물 상세
        </Link>
        <h2 className="text-2xl font-semibold tracking-tight">
          매물 수정 — {vehicle.make} {vehicle.model} {vehicle.year}
        </h2>
        <p className="mt-1 text-sm text-muted-foreground">
          VIN 은 등록 후 변경 불가 · 사양·가격·이력 수정 가능
        </p>
      </header>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1fr_360px]">
        {/* 왼쪽 — 폼 */}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            if (!canSubmit) return;
            updateMutation.mutate(form);
          }}
          className="space-y-6"
        >
          {/* 1. VIN (read-only) */}
          <Card>
            <CardContent className="space-y-3 p-5">
              <FormLabel>VIN (차대번호) — 등록 후 변경 불가</FormLabel>
              <Input
                value={form.vin}
                disabled
                className="font-mono uppercase bg-muted"
              />
              <p className="text-[11px] text-muted-foreground">
                VIN 변경이 필요하면 매물을 삭제 후 재등록하세요.
              </p>
            </CardContent>
          </Card>

          {/* 2. 차량 사양 */}
          <Card>
            <CardContent className="grid grid-cols-1 gap-4 p-5 sm:grid-cols-2">
              <Field label="제조사" value={form.make} onChange={(v) => set("make", v)} placeholder="Hyundai" />
              <Field label="모델" value={form.model} onChange={(v) => set("model", v)} placeholder="Sonata" />
              <Field
                label="연식"
                type="number"
                value={form.year || ""}
                onChange={(v) => set("year", Number(v) || 0)}
                placeholder="2020"
              />
              <Select
                label="차종"
                value={form.body_type}
                onChange={(v) => set("body_type", v)}
                options={[
                  { value: "", label: "선택..." },
                  { value: "passenger", label: "승용" },
                  { value: "truck", label: "트럭" },
                  { value: "van", label: "승합/밴" },
                ]}
              />
              <Select
                label="연료"
                value={form.fuel_type}
                onChange={(v) => set("fuel_type", v)}
                options={[
                  { value: "", label: "선택..." },
                  { value: "Gasoline", label: "가솔린" },
                  { value: "Diesel", label: "디젤" },
                  { value: "Hybrid", label: "하이브리드" },
                  { value: "EV", label: "전기" },
                  { value: "LPG", label: "LPG" },
                ]}
              />
              <Field
                label="배기량 (cc)"
                type="number"
                value={form.engine_cc || ""}
                onChange={(v) => set("engine_cc", Number(v) || 0)}
                placeholder="2000"
              />
              <Select
                label="변속기"
                value={form.transmission}
                onChange={(v) => set("transmission", v)}
                options={[
                  { value: "", label: "선택..." },
                  { value: "A/T", label: "자동" },
                  { value: "M/T", label: "수동" },
                  { value: "CVT", label: "CVT" },
                ]}
              />
              <Select
                label="핸들 *"
                value={form.steering}
                onChange={(v) => set("steering", v as "LHD" | "RHD")}
                options={[
                  { value: "LHD", label: "LHD (좌핸들)" },
                  { value: "RHD", label: "RHD (우핸들)" },
                ]}
              />
            </CardContent>
          </Card>

          {/* 3. 가격 · 이력 */}
          <Card>
            <CardContent className="grid grid-cols-1 gap-4 p-5 sm:grid-cols-2">
              <Field
                label="주행거리 (km)"
                type="number"
                value={form.mileage_km || ""}
                onChange={(v) => set("mileage_km", Number(v) || 0)}
                placeholder="58000"
              />
              <Field label="외장색" value={form.color_exterior} onChange={(v) => set("color_exterior", v)} placeholder="Pearl White" />
              <Field
                label="가격 (USD)"
                type="number"
                value={form.list_price_usd || ""}
                onChange={(v) => set("list_price_usd", Number(v) || 0)}
                placeholder="14000"
              />
              <Field label="HS Code" value={form.hs_code} onChange={(v) => set("hs_code", v)} placeholder="8703.23" />
              <Field
                label="제조일"
                type="date"
                value={form.manufacture_date}
                onChange={(v) => set("manufacture_date", v)}
              />
              <Field
                label="최초등록일"
                type="date"
                value={form.registration_date}
                onChange={(v) => set("registration_date", v)}
              />
            </CardContent>
          </Card>

          {/* 4. 액션 */}
          <div className="flex items-center justify-between">
            <p className="text-xs text-muted-foreground">
              * 필수 — 제조사·모델·연식·핸들
            </p>
            <div className="flex gap-2">
              <Link
                to={`/vehicles/${id}`}
                className="inline-flex h-9 items-center rounded-md border border-input bg-background px-4 text-sm font-medium hover:bg-accent"
              >
                취소
              </Link>
              <Button
                type="submit"
                disabled={!canSubmit || updateMutation.isPending}
                className="gap-2"
              >
                {updateMutation.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
                저장
              </Button>
            </div>
          </div>

          {updateMutation.isError && (
            <div className="rounded-md border border-destructive/30 bg-destructive/5 p-3 text-sm text-destructive">
              <p className="font-medium">저장 실패</p>
              <p className="mt-1 text-xs">
                {formatApiError(updateMutation.error)}
              </p>
            </div>
          )}
        </form>

        {/* 오른쪽 — 통관 매트릭스 (live preview) */}
        <aside className="lg:sticky lg:top-6 lg:self-start">
          <CountryMatrix vehicle={debouncedForm} enabled={Boolean(debouncedForm.steering && debouncedForm.body_type)} />
          <p className="mt-2 text-[11px] text-muted-foreground">
            폼 값 변경 후 ~600ms 안정화되면 자동 재평가
          </p>
        </aside>
      </div>
    </div>
  );
}

// ── 폼 헬퍼들 ──────────────────────────────────────────────
function FormLabel({ children }: { children: React.ReactNode }) {
  return <label className="text-sm font-medium">{children}</label>;
}

function Field({
  label,
  value,
  onChange,
  type = "text",
  placeholder,
}: {
  label: string;
  value: string | number;
  onChange: (v: string) => void;
  type?: string;
  placeholder?: string;
}) {
  return (
    <div className="space-y-1.5">
      <FormLabel>{label}</FormLabel>
      <Input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
      />
    </div>
  );
}

function Select({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: { value: string; label: string }[];
}) {
  return (
    <div className="space-y-1.5">
      <FormLabel>{label}</FormLabel>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className={cn(
          "flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm",
          "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring",
        )}
      >
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>{opt.label}</option>
        ))}
      </select>
    </div>
  );
}
