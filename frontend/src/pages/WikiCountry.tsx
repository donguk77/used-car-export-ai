import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  ArrowLeft,
  CheckCircle2,
  Loader2,
  Plus,
  Save,
  Trash2,
  X,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";
import { cn, formatApiError } from "@/lib/utils";

interface Rule {
  id: string;
  country_code: string;
  body_type_filter: string | null;
  age_limit_years: number | null;
  age_basis: string | null;
  age_effective_from: string | null;
  registration_after_date: string | null;
  steering_required: string | null;
  max_engine_cc: number | null;
  max_cylinders: number | null;
  fuel_blocked_json: string[];
  psi_required: string[];
  doc_translation_lang: string | null;
  consular_required: boolean;
  pre_registration: string | null;
  blocked_conditions_json: unknown[];
  required_documents_json: string[];
  effective_from: string | null;
  effective_to: string | null;
  source_url: string | null;
  last_verified_at: string | null;
  notes: string | null;
}

interface CountryDetail {
  code: string;
  name_en: string;
  name_ko: string | null;
  name_local: string | null;
  region: string | null;
  primary_language: string | null;
  business_language: string | null;
  steering: string | null;
  is_high_risk: boolean;
  is_russia_proxy_risk: boolean;
  is_sanctioned: boolean;
  is_blocked: boolean;
  main_ports_json: string[];
  pre_registration_system: string | null;
  consular_legalization: boolean;
  notes: string | null;
  rules: Rule[];
}

const BODY_TYPES = ["passenger", "bus", "truck", "van", "motorcycle"];
const AGE_BASIS_OPTIONS = ["manufacture_year", "first_registration", "shipping_date"];
const STEERING_OPTIONS = ["LHD_only", "RHD_only", "MIXED"];
const FUELS = ["EV", "BEV", "HEV", "PHEV", "Hybrid"];
const COMMON_DOCS = [
  "commercial_invoice",
  "packing_list",
  "bill_of_lading",
  "certificate_of_origin",
  "consular_legalization",
  "end_user_certificate",
  "translation_ar",
  "translation_es",
  "translation_ru",
  "translation_fr",
  "situational_license",
];

export function WikiCountryPage() {
  const { code = "" } = useParams();
  const upperCode = code.toUpperCase();
  const navigate = useNavigate();
  const qc = useQueryClient();

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["country-full", upperCode],
    queryFn: async (): Promise<CountryDetail> => {
      const r = await api.get<CountryDetail>(`/api/countries/${upperCode}/full`);
      return r.data;
    },
  });

  const [meta, setMeta] = useState<CountryDetail | null>(null);
  const [savedAt, setSavedAt] = useState<number | null>(null);

  useEffect(() => { if (data) setMeta(data); }, [data]);

  const updateCountry = useMutation({
    mutationFn: async () => {
      if (!meta) return;
      const r = await api.put<CountryDetail>(`/api/countries/${upperCode}`, {
        name_en: meta.name_en,
        name_ko: meta.name_ko,
        name_local: meta.name_local,
        region: meta.region,
        primary_language: meta.primary_language,
        business_language: meta.business_language,
        steering: meta.steering,
        is_high_risk: meta.is_high_risk,
        is_russia_proxy_risk: meta.is_russia_proxy_risk,
        is_sanctioned: meta.is_sanctioned,
        is_blocked: meta.is_blocked,
        main_ports_json: meta.main_ports_json ?? [],
        pre_registration_system: meta.pre_registration_system,
        consular_legalization: meta.consular_legalization,
        notes: meta.notes,
      });
      return r.data;
    },
    onSuccess: (d) => {
      if (d) setMeta(d);
      setSavedAt(Date.now());
      qc.invalidateQueries({ queryKey: ["countries"] });
      qc.invalidateQueries({ queryKey: ["country-full", upperCode] });
    },
  });

  const deleteCountry = useMutation({
    mutationFn: async () => {
      await api.delete(`/api/countries/${upperCode}`);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["countries"] });
      navigate("/wiki");
    },
  });

  const dirty = useMemo(() => {
    if (!data || !meta) return false;
    const keys: (keyof CountryDetail)[] = [
      "name_en", "name_ko", "name_local", "region", "primary_language",
      "business_language", "steering", "is_high_risk", "is_russia_proxy_risk",
      "is_sanctioned", "is_blocked", "pre_registration_system",
      "consular_legalization", "notes",
    ];
    if (keys.some((k) => (data[k] ?? null) !== (meta[k] ?? null))) return true;
    const a = (data.main_ports_json ?? []).join(",");
    const b = (meta.main_ports_json ?? []).join(",");
    return a !== b;
  }, [data, meta]);

  if (isLoading || !meta) {
    return (
      <div className="space-y-4">
        <div className="h-8 w-1/3 animate-pulse rounded bg-muted" />
        <Card><CardContent className="h-64 animate-pulse" /></Card>
      </div>
    );
  }

  if (isError) {
    return (
      <Card>
        <CardContent className="py-8 text-sm">
          <p className="font-medium text-destructive">국가를 불러오지 못했습니다</p>
          <p className="mt-1 text-muted-foreground">{formatApiError(error)}</p>
          <Link to="/wiki" className="mt-3 inline-flex items-center gap-1 text-primary hover:underline">
            <ArrowLeft className="h-3 w-3" /> Wiki 로 돌아가기
          </Link>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <header className="flex items-start justify-between gap-3">
        <div>
          <Link to="/wiki" className="inline-flex items-center gap-1 text-xs text-primary hover:underline">
            <ArrowLeft className="h-3 w-3" /> Wiki
          </Link>
          <h2 className="mt-1 flex items-center gap-2 text-2xl font-semibold">
            <span className="rounded bg-muted px-2 py-0.5 font-mono text-base">{meta.code}</span>
            {meta.name_ko ?? meta.name_en}
            <span className="text-base font-normal text-muted-foreground">({meta.name_en})</span>
          </h2>
        </div>
        <div className="flex items-center gap-2">
          {savedAt && !dirty && (
            <span className="flex items-center gap-1 text-xs text-success">
              <CheckCircle2 className="h-3 w-3" /> 저장됨
            </span>
          )}
          <Button
            onClick={() => updateCountry.mutate()}
            disabled={!dirty || updateCountry.isPending}
            className="gap-2"
          >
            {updateCountry.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
            <Save className="h-4 w-4" /> 메타 저장
          </Button>
          <Button
            variant="ghost"
            className="text-destructive"
            onClick={() => {
              if (confirm(`${meta.code} 국가와 모든 룰을 삭제합니다. 진행하시겠습니까?`)) {
                deleteCountry.mutate();
              }
            }}
            disabled={deleteCountry.isPending}
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      </header>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">기본 정보</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <Field label="영문명 *" value={meta.name_en} onChange={(v) => setMeta({ ...meta, name_en: v })} />
          <Field label="한글명" value={meta.name_ko ?? ""} onChange={(v) => setMeta({ ...meta, name_ko: v || null })} />
          <Field label="현지명" value={meta.name_local ?? ""} onChange={(v) => setMeta({ ...meta, name_local: v || null })} />
          <Field label="지역" value={meta.region ?? ""} onChange={(v) => setMeta({ ...meta, region: v || null })} />
          <Field label="공식 언어" value={meta.primary_language ?? ""} onChange={(v) => setMeta({ ...meta, primary_language: v || null })} placeholder="es / ar / en" />
          <Field label="비즈니스 언어" value={meta.business_language ?? ""} onChange={(v) => setMeta({ ...meta, business_language: v || null })} />
          <SelectField
            label="핸들"
            value={meta.steering ?? ""}
            onChange={(v) => setMeta({ ...meta, steering: v || null })}
            options={["", "LHD", "RHD", "MIXED"]}
          />
          <Field
            label="사전등록 시스템"
            value={meta.pre_registration_system ?? ""}
            onChange={(v) => setMeta({ ...meta, pre_registration_system: v || null })}
            placeholder="DGA / ACI / ECTN"
          />
          <Field
            label="주요 항구 (콤마)"
            value={(meta.main_ports_json ?? []).join(", ")}
            onChange={(v) => setMeta({ ...meta, main_ports_json: v.split(",").map((s) => s.trim()).filter(Boolean) })}
            placeholder="Rio Haina, Caucedo"
          />
          <div className="sm:col-span-3 flex flex-wrap gap-4">
            <Toggle label="High Risk" checked={meta.is_high_risk} onChange={(v) => setMeta({ ...meta, is_high_risk: v })} />
            <Toggle label="Russia Proxy" checked={meta.is_russia_proxy_risk} onChange={(v) => setMeta({ ...meta, is_russia_proxy_risk: v })} />
            <Toggle label="Sanctioned" checked={meta.is_sanctioned} onChange={(v) => setMeta({ ...meta, is_sanctioned: v })} />
            <Toggle label="Blocked" checked={meta.is_blocked} onChange={(v) => setMeta({ ...meta, is_blocked: v })} />
            <Toggle label="영사인증 필요" checked={meta.consular_legalization} onChange={(v) => setMeta({ ...meta, consular_legalization: v })} />
          </div>
          <div className="sm:col-span-3">
            <label className="text-sm font-medium">메모</label>
            <textarea
              value={meta.notes ?? ""}
              onChange={(e) => setMeta({ ...meta, notes: e.target.value || null })}
              className="mt-1 min-h-[80px] w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm"
              placeholder="국가별 특이사항·FTA·조약·계절 변동 등"
            />
          </div>
        </CardContent>
      </Card>

      <RulesSection countryCode={upperCode} rules={meta.rules} />

      {(updateCountry.isError || deleteCountry.isError) && (
        <div className="rounded-md border border-destructive/30 bg-destructive/5 p-3 text-xs text-destructive">
          {formatApiError(updateCountry.error || deleteCountry.error)}
        </div>
      )}
    </div>
  );
}

// ── Rules section ────────────────────────────────────────────────

function RulesSection({ countryCode, rules }: { countryCode: string; rules: Rule[] }) {
  const qc = useQueryClient();
  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ["country-full", countryCode] });
    qc.invalidateQueries({ queryKey: ["countries"] });
  };

  const addRule = useMutation({
    mutationFn: async () => {
      const r = await api.post<Rule>(`/api/countries/${countryCode}/rules`, {
        body_type_filter: "passenger",
      });
      return r.data;
    },
    onSuccess: invalidate,
  });

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between">
        <CardTitle className="text-base">통관 룰 ({rules.length})</CardTitle>
        <Button size="sm" onClick={() => addRule.mutate()} disabled={addRule.isPending} className="gap-1">
          {addRule.isPending ? <Loader2 className="h-3 w-3 animate-spin" /> : <Plus className="h-3 w-3" />}
          룰 추가
        </Button>
      </CardHeader>
      <CardContent className="space-y-3">
        {rules.length === 0 ? (
          <p className="py-8 text-center text-sm text-muted-foreground">
            등록된 룰이 없습니다. "룰 추가" 클릭으로 시작하세요.
          </p>
        ) : (
          rules.map((rule) => (
            <RuleEditor key={rule.id} countryCode={countryCode} rule={rule} onChange={invalidate} />
          ))
        )}
      </CardContent>
    </Card>
  );
}

function RuleEditor({
  countryCode,
  rule,
  onChange,
}: {
  countryCode: string;
  rule: Rule;
  onChange: () => void;
}) {
  const [draft, setDraft] = useState(rule);
  const [savedAt, setSavedAt] = useState<number | null>(null);

  const update = useMutation({
    mutationFn: async () => {
      const r = await api.put<Rule>(`/api/countries/${countryCode}/rules/${rule.id}`, {
        body_type_filter: draft.body_type_filter,
        age_limit_years: draft.age_limit_years,
        age_basis: draft.age_basis,
        age_effective_from: draft.age_effective_from,
        registration_after_date: draft.registration_after_date,
        steering_required: draft.steering_required,
        max_engine_cc: draft.max_engine_cc,
        max_cylinders: draft.max_cylinders,
        fuel_blocked_json: draft.fuel_blocked_json ?? [],
        psi_required: draft.psi_required ?? [],
        doc_translation_lang: draft.doc_translation_lang,
        consular_required: draft.consular_required,
        pre_registration: draft.pre_registration,
        blocked_conditions_json: draft.blocked_conditions_json ?? [],
        required_documents_json: draft.required_documents_json ?? [],
        effective_from: draft.effective_from,
        effective_to: draft.effective_to,
        source_url: draft.source_url,
        last_verified_at: draft.last_verified_at,
        notes: draft.notes,
      });
      return r.data;
    },
    onSuccess: (d) => {
      setDraft(d);
      setSavedAt(Date.now());
      onChange();
    },
  });

  const remove = useMutation({
    mutationFn: async () => {
      await api.delete(`/api/countries/${countryCode}/rules/${rule.id}`);
    },
    onSuccess: onChange,
  });

  const dirty = JSON.stringify(draft) !== JSON.stringify(rule);

  return (
    <div className={cn(
      "rounded-lg border p-4",
      dirty ? "border-amber-400 bg-amber-50/30" : "border-border",
    )}>
      <div className="mb-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="text-[10px]">
            {draft.body_type_filter ?? "all"}
          </Badge>
          {draft.age_limit_years && (
            <Badge variant="outline" className="text-[10px]">
              {draft.age_limit_years}년 / {draft.age_basis ?? "manufacture_year"}
            </Badge>
          )}
          {draft.steering_required && (
            <Badge variant="outline" className="text-[10px]">
              {draft.steering_required}
            </Badge>
          )}
          {dirty && <Badge className="bg-amber-500 text-[10px]">● 미저장</Badge>}
          {savedAt && !dirty && <CheckCircle2 className="h-3 w-3 text-success" />}
        </div>
        <div className="flex items-center gap-1">
          <Button
            size="sm"
            variant="ghost"
            onClick={() => update.mutate()}
            disabled={!dirty || update.isPending}
            className="gap-1"
          >
            {update.isPending ? <Loader2 className="h-3 w-3 animate-spin" /> : <Save className="h-3 w-3" />}
            저장
          </Button>
          <Button
            size="sm"
            variant="ghost"
            className="text-destructive"
            onClick={() => {
              if (confirm("이 룰을 삭제합니다. 진행하시겠습니까?")) remove.mutate();
            }}
            disabled={remove.isPending}
          >
            <Trash2 className="h-3 w-3" />
          </Button>
        </div>
      </div>

      <div className="grid gap-3 text-xs sm:grid-cols-2 lg:grid-cols-3">
        <SelectField
          label="차종 필터"
          value={draft.body_type_filter ?? ""}
          onChange={(v) => setDraft({ ...draft, body_type_filter: v || null })}
          options={["", ...BODY_TYPES]}
        />
        <NumberField
          label="연식 제한 (년)"
          value={draft.age_limit_years}
          onChange={(v) => setDraft({ ...draft, age_limit_years: v })}
        />
        <SelectField
          label="연식 기준"
          value={draft.age_basis ?? ""}
          onChange={(v) => setDraft({ ...draft, age_basis: v || null })}
          options={["", ...AGE_BASIS_OPTIONS]}
        />
        <SelectField
          label="핸들 요구"
          value={draft.steering_required ?? ""}
          onChange={(v) => setDraft({ ...draft, steering_required: v || null })}
          options={["", ...STEERING_OPTIONS]}
        />
        <NumberField
          label="최대 배기량 (cc)"
          value={draft.max_engine_cc}
          onChange={(v) => setDraft({ ...draft, max_engine_cc: v })}
        />
        <NumberField
          label="최대 실린더"
          value={draft.max_cylinders}
          onChange={(v) => setDraft({ ...draft, max_cylinders: v })}
        />
        <ChipField
          label="차단 연료"
          values={draft.fuel_blocked_json ?? []}
          options={FUELS}
          onChange={(values) => setDraft({ ...draft, fuel_blocked_json: values })}
        />
        <ChipField
          label="PSI 필수"
          values={draft.psi_required ?? []}
          options={["JEVIC", "QISJ", "SONCAP", "Intertek", "GOEIC", "DVLA", "TBS"]}
          onChange={(values) => setDraft({ ...draft, psi_required: values })}
        />
        <Field
          label="문서 번역 언어"
          value={draft.doc_translation_lang ?? ""}
          onChange={(v) => setDraft({ ...draft, doc_translation_lang: v || null })}
          placeholder="ar / es / fr"
        />
        <Field
          label="사전등록"
          value={draft.pre_registration ?? ""}
          onChange={(v) => setDraft({ ...draft, pre_registration: v || null })}
          placeholder="DGA / ACI"
        />
        <Toggle
          label="영사인증 필수"
          checked={draft.consular_required}
          onChange={(v) => setDraft({ ...draft, consular_required: v })}
        />
        <Field
          label="시행 시작일"
          value={draft.age_effective_from ?? ""}
          onChange={(v) => setDraft({ ...draft, age_effective_from: v || null })}
          placeholder="2026-01-01"
        />
        <Field
          label="등록일 이후"
          value={draft.registration_after_date ?? ""}
          onChange={(v) => setDraft({ ...draft, registration_after_date: v || null })}
          placeholder="2019-01-01"
        />
        <Field
          label="마지막 검증일"
          value={draft.last_verified_at ?? ""}
          onChange={(v) => setDraft({ ...draft, last_verified_at: v || null })}
          placeholder="2026-05-12"
        />
        <div className="sm:col-span-2 lg:col-span-3">
          <ChipField
            label="필수 서류"
            values={draft.required_documents_json ?? []}
            options={COMMON_DOCS}
            onChange={(values) => setDraft({ ...draft, required_documents_json: values })}
            allowCustom
          />
        </div>
        <div className="sm:col-span-2 lg:col-span-3">
          <Field
            label="출처 URL"
            value={draft.source_url ?? ""}
            onChange={(v) => setDraft({ ...draft, source_url: v || null })}
            placeholder="https://..."
          />
        </div>
        <div className="sm:col-span-2 lg:col-span-3">
          <label className="text-xs font-medium">메모</label>
          <textarea
            value={draft.notes ?? ""}
            onChange={(e) => setDraft({ ...draft, notes: e.target.value || null })}
            className="mt-1 min-h-[60px] w-full rounded-md border border-input bg-transparent px-2 py-1.5 text-xs"
          />
        </div>
      </div>

      {(update.isError || remove.isError) && (
        <p className="mt-2 text-xs text-destructive">
          {formatApiError(update.error || remove.error)}
        </p>
      )}
    </div>
  );
}

// ── form helpers ─────────────────────────────────────────────────

function Field({
  label, value, onChange, placeholder,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
}) {
  return (
    <div className="space-y-1">
      <label className="text-xs font-medium">{label}</label>
      <Input value={value} onChange={(e) => onChange(e.target.value)} placeholder={placeholder} className="h-8 text-xs" />
    </div>
  );
}

function NumberField({
  label, value, onChange,
}: {
  label: string;
  value: number | null;
  onChange: (v: number | null) => void;
}) {
  return (
    <div className="space-y-1">
      <label className="text-xs font-medium">{label}</label>
      <Input
        type="number"
        value={value ?? ""}
        onChange={(e) => {
          const v = e.target.value;
          onChange(v === "" ? null : Number(v));
        }}
        className="h-8 text-xs"
      />
    </div>
  );
}

function SelectField({
  label, value, onChange, options,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: string[];
}) {
  return (
    <div className="space-y-1">
      <label className="text-xs font-medium">{label}</label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="flex h-8 w-full rounded-md border border-input bg-transparent px-2 text-xs"
      >
        {options.map((opt) => (
          <option key={opt} value={opt}>{opt || "—"}</option>
        ))}
      </select>
    </div>
  );
}

function Toggle({
  label, checked, onChange,
}: {
  label: string;
  checked: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <label className="flex items-center gap-2 text-xs">
      <input type="checkbox" checked={checked} onChange={(e) => onChange(e.target.checked)} />
      {label}
    </label>
  );
}

function ChipField({
  label, values, options, onChange, allowCustom,
}: {
  label: string;
  values: string[];
  options: string[];
  onChange: (v: string[]) => void;
  allowCustom?: boolean;
}) {
  const [custom, setCustom] = useState("");
  const has = (v: string) => values.includes(v);
  const toggle = (v: string) => {
    if (!v) return;
    onChange(has(v) ? values.filter((x) => x !== v) : [...values, v]);
  };
  const remove = (v: string) => onChange(values.filter((x) => x !== v));

  return (
    <div className="space-y-1">
      <label className="text-xs font-medium">{label}</label>
      <div className="flex flex-wrap gap-1">
        {values.map((v) => (
          <span key={v} className="inline-flex items-center gap-1 rounded-md bg-primary/10 px-2 py-0.5 text-[11px] text-primary">
            {v}
            <button type="button" onClick={() => remove(v)} className="hover:text-destructive">
              <X className="h-2.5 w-2.5" />
            </button>
          </span>
        ))}
      </div>
      <div className="flex flex-wrap gap-1 pt-1">
        {options.filter((o) => !has(o)).map((o) => (
          <button
            key={o}
            type="button"
            onClick={() => toggle(o)}
            className="rounded border border-dashed border-border px-1.5 py-0.5 text-[10px] text-muted-foreground hover:bg-accent hover:text-foreground"
          >
            + {o}
          </button>
        ))}
        {allowCustom && (
          <span className="inline-flex items-center gap-1">
            <input
              value={custom}
              onChange={(e) => setCustom(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && custom.trim()) {
                  e.preventDefault();
                  toggle(custom.trim());
                  setCustom("");
                }
              }}
              placeholder="+ 커스텀 (Enter)"
              className="rounded border border-input bg-transparent px-1.5 py-0.5 text-[10px]"
            />
          </span>
        )}
      </div>
    </div>
  );
}
