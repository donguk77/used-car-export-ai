import { useEffect, useRef, useState } from "react";
import { AxiosError } from "axios";
import {
  AlertTriangle,
  ArrowLeft,
  CheckCircle2,
  ChevronDown,
  Dice5,
  Loader2,
  ShieldAlert,
  ShieldCheck,
  ShieldX,
  Wand2,
  XCircle,
} from "lucide-react";
import { Link, useNavigate } from "react-router-dom";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useCreateBuyer } from "@/hooks/useBuyers";
import { COUNTRY_FLAG } from "@/lib/constants";
import {
  DEMO_BUYER_PRESETS,
  EMPTY_BUYER_FORM,
  generateRandomBuyer,
  type BuyerFormData,
} from "@/lib/demoBuyers";
import { cn } from "@/lib/utils";
import type { ComplianceReport } from "@/types/api";

export function BuyerNewPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState<BuyerFormData>(EMPTY_BUYER_FORM);
  const [showPresets, setShowPresets] = useState(false);
  const [result, setResult] = useState<ComplianceReport | null>(null);
  const [createdId, setCreatedId] = useState<string | null>(null);

  const createMutation = useCreateBuyer();

  const set = <K extends keyof BuyerFormData>(key: K, value: BuyerFormData[K]) => {
    setForm((f) => ({ ...f, [key]: value }));
  };

  const applyPreset = (data: BuyerFormData) => {
    setForm(data);
    setResult(null);
    setCreatedId(null);
    setShowPresets(false);
  };

  const applyRandom = () => {
    setForm(generateRandomBuyer());
    setResult(null);
    setCreatedId(null);
    setShowPresets(false);
  };

  // Esc + 외부클릭 dropdown 닫기 (VehicleNew 와 같은 패턴)
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

  const canSubmit = Boolean(form.company_name && form.country_code);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!canSubmit) return;
    try {
      // 빈 string 들 제거 — 백엔드가 null 처리
      const payload = Object.fromEntries(
        Object.entries(form).filter(([, v]) => v !== ""),
      ) as BuyerFormData;
      const r = await createMutation.mutateAsync(payload);
      setResult(r.compliance);
      setCreatedId(r.buyer.id);
    } catch {
      // 에러는 createMutation.error 에서 표면화
    }
  };

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <Link
            to="/buyers"
            className="mb-1 inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground"
          >
            <ArrowLeft className="h-3 w-3" /> 바이어 목록
          </Link>
          <h2 className="text-2xl font-semibold tracking-tight">바이어 등록</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            정보 입력 → 자동 compliance (OFAC · 러시아 우회 · Yestrade) → 결과 즉시 표시
          </p>
        </div>

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
              className="absolute right-0 top-full z-10 mt-1 w-96 rounded-md border bg-card shadow-lg"
            >
              <div className="border-b px-3 py-2 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                시연 시나리오 프리셋 (compliance 결과 미리보기)
              </div>
              {DEMO_BUYER_PRESETS.map((p) => (
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
                  <span className="font-medium">랜덤 바이어 생성</span>
                  <span className="text-[11px] text-muted-foreground">국가·이름 무작위</span>
                </button>
              </div>
            </div>
          )}
        </div>
      </header>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1fr_360px]">
        {/* 폼 */}
        <form onSubmit={onSubmit} className="space-y-6">
          <Card>
            <CardContent className="grid grid-cols-1 gap-4 p-5 sm:grid-cols-2">
              <Field
                label="회사명 *"
                value={form.company_name}
                onChange={(v) => set("company_name", v)}
                placeholder="Rodriguez Motors S.R.L."
              />
              <Field
                label="담당자"
                value={form.contact_person}
                onChange={(v) => set("contact_person", v)}
                placeholder="Mr. Carlos Rodríguez"
              />
              <Field
                label="국가 코드 (ISO 2자리) *"
                value={form.country_code}
                onChange={(v) => set("country_code", v.toUpperCase().slice(0, 2))}
                placeholder="DO"
                className="font-mono uppercase"
              />
              <Field
                label="도시"
                value={form.city}
                onChange={(v) => set("city", v)}
                placeholder="Santo Domingo"
              />
              <div className="sm:col-span-2">
                <Field
                  label="주소"
                  value={form.address}
                  onChange={(v) => set("address", v)}
                  placeholder="Av. Winston Churchill 123, ..."
                />
              </div>
              <Field label="Tax ID" value={form.tax_id} onChange={(v) => set("tax_id", v)} placeholder="DO-987654321" />
              <Field label="이메일" type="email" value={form.email} onChange={(v) => set("email", v)} placeholder="contact@buyer.com" />
              <Field label="전화" value={form.phone} onChange={(v) => set("phone", v)} placeholder="+1-809-555-0123" />
              <Field label="WhatsApp" value={form.whatsapp} onChange={(v) => set("whatsapp", v)} placeholder="+1-809-555-0123" />
            </CardContent>
          </Card>

          <Card>
            <CardContent className="grid grid-cols-1 gap-4 p-5 sm:grid-cols-2">
              <Select
                label="선호 언어"
                value={form.preferred_language}
                onChange={(v) => set("preferred_language", v)}
                options={[
                  { value: "", label: "선택..." },
                  { value: "en", label: "영어 (EN)" },
                  { value: "es", label: "스페인어 (ES)" },
                  { value: "ar", label: "아랍어 (AR)" },
                  { value: "ru", label: "러시아어 (RU)" },
                  { value: "fr", label: "프랑스어 (FR)" },
                ]}
              />
              <Select
                label="선호 통화"
                value={form.preferred_currency}
                onChange={(v) => set("preferred_currency", v)}
                options={[
                  { value: "USD", label: "USD" },
                  { value: "EUR", label: "EUR" },
                  { value: "JPY", label: "JPY" },
                ]}
              />
              <Select
                label="선호 결제"
                value={form.preferred_payment}
                onChange={(v) => set("preferred_payment", v)}
                options={[
                  { value: "T/T", label: "T/T (전신환)" },
                  { value: "L/C", label: "L/C (신용장)" },
                  { value: "D/P", label: "D/P" },
                  { value: "D/A", label: "D/A" },
                ]}
              />
              <Select
                label="선호 Incoterm"
                value={form.preferred_incoterm}
                onChange={(v) => set("preferred_incoterm", v)}
                options={[
                  { value: "CIF", label: "CIF" },
                  { value: "FOB", label: "FOB" },
                  { value: "CFR", label: "CFR" },
                  { value: "EXW", label: "EXW" },
                ]}
              />
              <div className="sm:col-span-2">
                <Field label="선호 항구" value={form.preferred_port} onChange={(v) => set("preferred_port", v)} placeholder="Rio Haina / Mombasa / Misrata 등" />
              </div>
            </CardContent>
          </Card>

          {createMutation.isError && (
            <div className="rounded-md border border-destructive/30 bg-destructive/5 p-3 text-sm">
              <p className="font-medium text-destructive">등록 실패</p>
              <p className="mt-1 text-xs text-muted-foreground">
                {createMutation.error instanceof AxiosError
                  ? (createMutation.error.response?.data?.detail ?? createMutation.error.message)
                  : (createMutation.error as Error)?.message}
              </p>
            </div>
          )}

          <div className="flex items-center justify-between">
            <p className="text-xs text-muted-foreground">* 필수 — 회사명·국가코드</p>
            <div className="flex gap-2">
              <Link
                to="/buyers"
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
                등록 + Compliance 검사
              </Button>
            </div>
          </div>
        </form>

        {/* Compliance 결과 패널 */}
        <aside className="lg:sticky lg:top-6 lg:self-start">
          <ComplianceResultCard
            country={form.country_code}
            result={result}
            createdId={createdId}
            onView={() => createdId && navigate(`/buyers/${createdId}`)}
            onAnother={() => {
              setForm(EMPTY_BUYER_FORM);
              setResult(null);
              setCreatedId(null);
            }}
          />
        </aside>
      </div>
    </div>
  );
}

function ComplianceResultCard({
  country,
  result,
  createdId,
  onView,
  onAnother,
}: {
  country: string;
  result: ComplianceReport | null;
  createdId: string | null;
  onView: () => void;
  onAnother: () => void;
}) {
  if (!result) {
    return (
      <Card>
        <CardContent className="space-y-3 p-5">
          <h3 className="text-sm font-semibold">Compliance 검사 결과</h3>
          <p className="rounded-md bg-muted/50 px-3 py-6 text-center text-xs text-muted-foreground">
            등록 클릭 시 자동 검사:
            <br />OFAC SDN · 러시아 우회 위험 · Yestrade 우려거래자
          </p>
          {country && (
            <div className="flex items-center gap-2 text-xs">
              <span className="text-base">{COUNTRY_FLAG[country] ?? "🌐"}</span>
              <span className="font-mono">{country}</span>
              {country === "RU" && (
                <Badge variant="destructive" className="ml-auto">미리보기: 직접 차단</Badge>
              )}
              {["KG", "KZ", "TJ", "AM", "UZ"].includes(country) && (
                <Badge variant="warning" className="ml-auto">미리보기: 경고</Badge>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    );
  }

  const Icon = result.overall === "blocked" ? ShieldX : result.overall === "warning" ? ShieldAlert : ShieldCheck;
  const colorClass =
    result.overall === "blocked" ? "border-destructive/40 bg-destructive/5"
    : result.overall === "warning" ? "border-warning/40 bg-warning/5"
    : "border-success/40 bg-success/5";

  return (
    <Card className={cn("space-y-0", colorClass)}>
      <CardContent className="space-y-4 p-5">
        <div className="flex items-center gap-2">
          <Icon className={cn(
            "h-6 w-6",
            result.overall === "blocked" ? "text-destructive"
            : result.overall === "warning" ? "text-warning"
            : "text-success",
          )} />
          <div className="flex-1">
            <p className="text-sm font-bold">
              {result.overall === "blocked" ? "거래 차단됨" : result.overall === "warning" ? "주의 — 검토 필요" : "거래 가능"}
            </p>
            <p className="text-xs text-muted-foreground">
              종합 점수 <strong className="text-foreground">{result.score}</strong>/100
            </p>
          </div>
        </div>

        {result.findings.length > 0 && (
          <div className="space-y-2">
            <p className="text-xs font-semibold text-muted-foreground">발견된 항목</p>
            {result.findings.map((f, i) => (
              <div key={i} className="flex items-start gap-2 rounded-md bg-background/60 p-2 text-xs">
                {f.severity === "blocked" && <XCircle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-destructive" />}
                {f.severity === "warning" && <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-warning" />}
                {f.severity === "clean" && <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-success" />}
                <div className="flex-1">
                  <p className="font-mono text-[10px] uppercase text-muted-foreground">{f.code}</p>
                  <p className="mt-0.5">{f.message}</p>
                </div>
              </div>
            ))}
          </div>
        )}

        {result.findings.length === 0 && (
          <p className="rounded-md bg-success/10 px-3 py-2 text-center text-xs text-success">
            모든 검사 통과 — 별도 액션 불필요
          </p>
        )}

        {createdId && (
          <div className="flex flex-col gap-2 border-t pt-4">
            <Button onClick={onView} className="w-full">
              바이어 상세 보기
            </Button>
            <Button onClick={onAnother} variant="outline" className="w-full">
              다른 바이어 등록
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function Field({
  label,
  value,
  onChange,
  type = "text",
  placeholder,
  className,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  type?: string;
  placeholder?: string;
  className?: string;
}) {
  return (
    <div className="space-y-1.5">
      <label className="text-sm font-medium">{label}</label>
      <Input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className={className}
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
      <label className="text-sm font-medium">{label}</label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
      >
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>{opt.label}</option>
        ))}
      </select>
    </div>
  );
}
