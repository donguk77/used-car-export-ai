import { useEffect, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AxiosError } from "axios";
import {
  ArrowLeft,
  CheckCircle2,
  ChevronDown,
  Dice5,
  Loader2,
  Wand2,
} from "lucide-react";
import { Link, useNavigate } from "react-router-dom";

import { CountryMatrix } from "@/components/CountryMatrix";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useDebouncedValue } from "@/hooks/useDebouncedValue";
import { api } from "@/lib/api";
import { DEMO_PRESETS, generateRandomVehicle, type VehicleFormData } from "@/lib/demoVehicles";
import { cn } from "@/lib/utils";
import type { DecodedVin, Vehicle } from "@/types/api";

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

export function VehicleNewPage() {
  const navigate = useNavigate();
  const qc = useQueryClient();

  const [form, setForm] = useState<VehicleFormData>(EMPTY_FORM);
  const [showPresets, setShowPresets] = useState(false);

  const set = <K extends keyof VehicleFormData>(key: K, value: VehicleFormData[K]) => {
    setForm((f) => ({ ...f, [key]: value }));
  };

  // 통관 매트릭스용 — form 안정화 후 평가 (~600ms debounce). 매 키스트로크 폭주 방지.
  const debouncedForm = useDebouncedValue(form, 600);

  // VIN 17자리 입력 시 NHTSA 디코드 (debounced)
  const debouncedVin = useDebouncedValue(form.vin.length === 17 ? form.vin : "", 500);

  const decodeQuery = useQuery({
    queryKey: ["decode-vin", debouncedVin],
    queryFn: async (): Promise<DecodedVin> => {
      const r = await api.get<DecodedVin>(`/api/vehicles/decode-vin/${debouncedVin}`);
      return r.data;
    },
    enabled: debouncedVin.length === 17,
    staleTime: Infinity,
  });

  // 디코드 결과 자동 채움 — race condition 방지:
  //   1. 디코드된 VIN 이 현재 form.vin 과 일치하는지 (사용자가 그 사이 다른 VIN 입력했으면 무시)
  //   2. 같은 VIN 을 두 번 적용하지 않도록 ref 로 마킹
  const lastAppliedDecodeVinRef = useRef<string | null>(null);
  useEffect(() => {
    const d = decodeQuery.data;
    if (!d || !d.vin) return;
    if (d.vin !== form.vin) return;
    if (lastAppliedDecodeVinRef.current === d.vin) return;

    lastAppliedDecodeVinRef.current = d.vin;
    setForm((f) => ({
      ...f,
      make: f.make || d.make || "",
      model: f.model || d.model || "",
      year: f.year || d.year || 0,
      body_type: f.body_type || d.body_type || "",
      fuel_type: f.fuel_type || d.fuel_type || "",
      engine_cc: f.engine_cc || d.engine_cc || 0,
      transmission: f.transmission || d.transmission || "",
    }));
  }, [decodeQuery.data, form.vin]);

  // POST /api/vehicles
  const createMutation = useMutation({
    mutationFn: async (data: VehicleFormData): Promise<Vehicle> => {
      const r = await api.post<Vehicle>("/api/vehicles", {
        ...data,
        // 빈/0 값은 제외해서 보냄
        year: data.year || null,
        engine_cc: data.engine_cc || null,
        mileage_km: data.mileage_km || null,
        list_price_usd: data.list_price_usd || null,
        manufacture_date: data.manufacture_date || null,
        registration_date: data.registration_date || null,
        auto_decode_vin: false, // 이미 클라이언트에서 디코드함
      });
      return r.data;
    },
    onSuccess: (vehicle) => {
      qc.invalidateQueries({ queryKey: ["vehicles"] });
      qc.invalidateQueries({ queryKey: ["dashboard-summary"] });
      navigate(`/vehicles/${vehicle.id}`);
    },
  });

  const applyPreset = (data: VehicleFormData) => {
    setForm(data);
    lastAppliedDecodeVinRef.current = null; // 같은 VIN 재입력 시 디코드 다시 적용되도록
    setShowPresets(false);
  };

  const applyRandom = () => {
    setForm(generateRandomVehicle());
    lastAppliedDecodeVinRef.current = null;
    setShowPresets(false);
  };

  const canSubmit = Boolean(form.make && form.model && form.year && form.steering);

  // 드롭다운 a11y — Esc 키 + 외부 클릭으로 닫기
  const presetMenuRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!showPresets) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setShowPresets(false);
    };
    const onPointer = (e: PointerEvent) => {
      if (presetMenuRef.current && !presetMenuRef.current.contains(e.target as Node)) {
        setShowPresets(false);
      }
    };
    document.addEventListener("keydown", onKey);
    document.addEventListener("pointerdown", onPointer);
    return () => {
      document.removeEventListener("keydown", onKey);
      document.removeEventListener("pointerdown", onPointer);
    };
  }, [showPresets]);

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <Link
            to="/vehicles"
            className="mb-1 inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground"
          >
            <ArrowLeft className="h-3 w-3" /> 매물 목록
          </Link>
          <h2 className="text-2xl font-semibold tracking-tight">매물 등록</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            VIN 17자리 입력하면 NHTSA 가 자동 채움 · 5개국 통관 결과 실시간 미리보기
          </p>
        </div>

        {/* Demo 데이터 드롭다운 (Esc·외부클릭으로 닫힘) */}
        <div ref={presetMenuRef} className="relative">
          <Button
            type="button"
            variant="outline"
            onClick={() => setShowPresets((s) => !s)}
            aria-haspopup="menu"
            aria-expanded={showPresets}
            className="gap-2"
          >
            <Wand2 className="h-4 w-4" />
            데모 데이터 채우기
            <ChevronDown className="h-3 w-3" />
          </Button>
          {showPresets && (
            <div
              role="menu"
              className="absolute right-0 top-full z-10 mt-1 w-80 rounded-md border bg-card shadow-lg"
            >
              <div className="border-b px-3 py-2 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                시연 시나리오 프리셋
              </div>
              {DEMO_PRESETS.map((p) => (
                <button
                  key={p.label}
                  type="button"
                  role="menuitem"
                  onClick={() => applyPreset(p.data)}
                  className="block w-full px-3 py-2.5 text-left hover:bg-accent focus:bg-accent focus:outline-none"
                >
                  <div className="text-sm font-medium">{p.label}</div>
                  <div className="mt-0.5 text-[11px] text-muted-foreground">{p.hint}</div>
                </button>
              ))}
              <div className="border-t">
                <button
                  type="button"
                  role="menuitem"
                  onClick={applyRandom}
                  className="flex w-full items-center gap-2 px-3 py-2.5 text-sm hover:bg-accent focus:bg-accent focus:outline-none"
                >
                  <Dice5 className="h-4 w-4 text-primary" />
                  <span className="font-medium">랜덤 차량 생성</span>
                  <span className="text-[11px] text-muted-foreground">VIN·사양 무작위</span>
                </button>
              </div>
            </div>
          )}
        </div>
      </header>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1fr_360px]">
        {/* 왼쪽 — 폼 */}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            if (!canSubmit) return;
            createMutation.mutate(form);
          }}
          className="space-y-6"
        >
          {/* 1. VIN + auto-decode 상태 */}
          <Card>
            <CardContent className="space-y-3 p-5">
              <FormLabel>VIN (차대번호) — 17자리</FormLabel>
              <Input
                value={form.vin}
                onChange={(e) => set("vin", e.target.value.toUpperCase())}
                placeholder="예: KMHE41LBXLA000901"
                maxLength={17}
                className="font-mono uppercase"
              />
              <div className="flex items-center gap-2 text-xs">
                {form.vin.length === 0 && (
                  <span className="text-muted-foreground">선택 — VIN 없으면 수동 입력</span>
                )}
                {form.vin.length > 0 && form.vin.length < 17 && (
                  <span className="text-muted-foreground">
                    {form.vin.length} / 17 — {17 - form.vin.length}자 남음
                  </span>
                )}
                {form.vin.length === 17 && decodeQuery.isLoading && (
                  <span className="flex items-center gap-1 text-primary">
                    <Loader2 className="h-3 w-3 animate-spin" /> NHTSA 디코딩...
                  </span>
                )}
                {decodeQuery.data?.make && (
                  <span className="flex items-center gap-1 text-success">
                    <CheckCircle2 className="h-3 w-3" />
                    NHTSA 자동 채움: {decodeQuery.data.make} {decodeQuery.data.model}{" "}
                    {decodeQuery.data.year}
                  </span>
                )}
              </div>
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
                to="/vehicles"
                className="inline-flex h-9 items-center rounded-md border border-input bg-background px-4 text-sm font-medium hover:bg-accent"
              >
                취소
              </Link>
              <Button
                type="submit"
                disabled={!canSubmit || createMutation.isPending}
                className="gap-2"
              >
                {createMutation.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
                매물 등록
              </Button>
            </div>
          </div>

          {createMutation.isError && (
            <div className="rounded-md border border-destructive/30 bg-destructive/5 p-3 text-sm text-destructive">
              <p className="font-medium">등록 실패</p>
              <p className="mt-1 text-xs">
                {createMutation.error instanceof AxiosError
                  ? (createMutation.error.response?.data?.detail ?? createMutation.error.message)
                  : (createMutation.error as Error)?.message}
              </p>
            </div>
          )}
        </form>

        {/* 오른쪽 — 통관 매트릭스 (live preview, 600ms debounce) */}
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
