import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Building2, CheckCircle2, Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";
import { cn, formatApiError } from "@/lib/utils";

interface User {
  id: string;
  email: string;
  company_name: string;
  business_no: string | null;
  phone: string | null;
  address: string | null;
  port_of_loading: string;
  default_language: string;
  default_currency: string;
}

interface FormState {
  company_name: string;
  business_no: string;
  phone: string;
  address: string;
  port_of_loading: string;
  default_language: string;
  default_currency: string;
}

const EMPTY: FormState = {
  company_name: "",
  business_no: "",
  phone: "",
  address: "",
  port_of_loading: "Incheon",
  default_language: "ko",
  default_currency: "USD",
};

const PORT_OPTIONS = [
  "Incheon", "Busan", "Pyeongtaek", "Mokpo", "Ulsan", "Pohang", "Gunsan",
];

const LANG_OPTIONS = [
  { value: "ko", label: "한국어" },
  { value: "en", label: "English" },
  { value: "es", label: "Español" },
  { value: "ar", label: "العربية" },
  { value: "ru", label: "Русский" },
];

const CURRENCY_OPTIONS = ["USD", "KRW", "EUR", "JPY", "AED", "SAR"];

export function SettingsPage() {
  const qc = useQueryClient();
  const [form, setForm] = useState<FormState>(EMPTY);
  const [prefilled, setPrefilled] = useState(false);
  const [savedAt, setSavedAt] = useState<number | null>(null);

  const set = <K extends keyof FormState>(key: K, value: FormState[K]) => {
    setForm((f) => ({ ...f, [key]: value }));
    setSavedAt(null);
  };

  const { data: user, isLoading, isError, error } = useQuery({
    queryKey: ["users", "me"],
    queryFn: async (): Promise<User> => {
      const r = await api.get<User>("/api/users/me");
      return r.data;
    },
  });

  useEffect(() => {
    if (!user || prefilled) return;
    setForm({
      company_name: user.company_name ?? "",
      business_no: user.business_no ?? "",
      phone: user.phone ?? "",
      address: user.address ?? "",
      port_of_loading: user.port_of_loading ?? "Incheon",
      default_language: user.default_language ?? "ko",
      default_currency: user.default_currency ?? "USD",
    });
    setPrefilled(true);
  }, [user, prefilled]);

  const updateMutation = useMutation({
    mutationFn: async (data: FormState): Promise<User> => {
      const r = await api.patch<User>("/api/users/me", data);
      return r.data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["users", "me"] });
      setSavedAt(Date.now());
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

  if (isError) {
    return (
      <Card>
        <CardContent className="py-8 text-sm">
          <p className="font-medium text-destructive">설정을 불러오지 못했습니다</p>
          <p className="mt-1 text-muted-foreground">{formatApiError(error)}</p>
        </CardContent>
      </Card>
    );
  }

  const canSave = Boolean(form.company_name.trim());
  const dirty =
    user
    && (user.company_name !== form.company_name
      || (user.business_no ?? "") !== form.business_no
      || (user.phone ?? "") !== form.phone
      || (user.address ?? "") !== form.address
      || user.port_of_loading !== form.port_of_loading
      || user.default_language !== form.default_language
      || user.default_currency !== form.default_currency);

  return (
    <div className="space-y-6">
      <header>
        <h2 className="text-2xl font-semibold tracking-tight">설정</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          프로필 · 기본 항구 · 기본 언어 · 기본 통화 — 신규 거래·메일·서류에 자동 적용됩니다
        </p>
      </header>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          if (!canSave) return;
          updateMutation.mutate(form);
        }}
        className="space-y-6"
      >
        {/* 1. 회사 정보 */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Building2 className="h-4 w-4" /> 회사 정보
            </CardTitle>
          </CardHeader>
          <CardContent className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <Field
              label="회사명 *"
              value={form.company_name}
              onChange={(v) => set("company_name", v)}
              placeholder="동강그린모터스"
            />
            <Field
              label="사업자등록번호"
              value={form.business_no}
              onChange={(v) => set("business_no", v)}
              placeholder="123-45-67890"
            />
            <Field
              label="대표 연락처"
              value={form.phone}
              onChange={(v) => set("phone", v)}
              placeholder="+82-32-555-1234"
            />
            <Field
              label="이메일 (변경 불가)"
              value={user?.email ?? ""}
              onChange={() => {}}
              disabled
            />
            <div className="sm:col-span-2">
              <Field
                label="주소"
                value={form.address}
                onChange={(v) => set("address", v)}
                placeholder="123-4 Songdo-dong, Yeonsu-gu, Incheon 21984"
              />
            </div>
          </CardContent>
        </Card>

        {/* 2. 기본값 */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">신규 거래 기본값</CardTitle>
          </CardHeader>
          <CardContent className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <Select
              label="기본 선적항"
              value={form.port_of_loading}
              onChange={(v) => set("port_of_loading", v)}
              options={PORT_OPTIONS.map((p) => ({ value: p, label: p }))}
            />
            <Select
              label="기본 메일 언어"
              value={form.default_language}
              onChange={(v) => set("default_language", v)}
              options={LANG_OPTIONS}
            />
            <Select
              label="기본 통화"
              value={form.default_currency}
              onChange={(v) => set("default_currency", v)}
              options={CURRENCY_OPTIONS.map((c) => ({ value: c, label: c }))}
            />
          </CardContent>
        </Card>

        {/* 3. 액션 */}
        <div className="flex items-center justify-between">
          <p className="text-xs text-muted-foreground">
            * 필수 항목 · 변경사항은 즉시 저장됩니다
          </p>
          <div className="flex items-center gap-3">
            {savedAt && !dirty && (
              <span className="flex items-center gap-1 text-xs text-success">
                <CheckCircle2 className="h-3 w-3" /> 저장됨
              </span>
            )}
            <Button
              type="submit"
              disabled={!canSave || !dirty || updateMutation.isPending}
              className="gap-2"
            >
              {updateMutation.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
              {dirty ? "변경사항 저장" : "저장됨"}
            </Button>
          </div>
        </div>

        {updateMutation.isError && (
          <div className="rounded-md border border-destructive/30 bg-destructive/5 p-3 text-sm text-destructive">
            <p className="font-medium">저장 실패</p>
            <p className="mt-1 text-xs">{formatApiError(updateMutation.error)}</p>
          </div>
        )}
      </form>

      {/* Phase 2 안내 */}
      <Card className="border-dashed bg-muted/30">
        <CardContent className="py-4 text-xs text-muted-foreground">
          <p className="font-medium text-foreground">Phase 2 예정</p>
          <ul className="mt-2 ml-4 list-disc space-y-0.5">
            <li>비밀번호 변경 + JWT 인증</li>
            <li>LLM provider 선택 (현재 Gemini-2.5-flash 고정)</li>
            <li>회사 로고 업로드 (PDF 헤더 삽입)</li>
            <li>API 토큰 발급 (외부 시스템 연동)</li>
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}

// ── 폼 헬퍼 ──────────────────────────────────────────────
function Field({
  label,
  value,
  onChange,
  placeholder,
  disabled,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  disabled?: boolean;
}) {
  return (
    <div className="space-y-1.5">
      <label className="text-sm font-medium">{label}</label>
      <Input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        disabled={disabled}
        className={disabled ? "bg-muted" : undefined}
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
