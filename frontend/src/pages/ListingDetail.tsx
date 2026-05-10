import { useState } from "react";
import {
  ArrowLeft,
  Car,
  CheckCircle2,
  Clipboard,
  ClipboardCheck,
  Download,
  FileText,
  Loader2,
  Mail,
  RefreshCw,
  ShieldAlert,
  ShieldCheck,
  ShieldX,
  Sparkles,
  XCircle,
} from "lucide-react";
import { Link, useParams } from "react-router-dom";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  useBuyerById,
  useGenerateDocuments,
  useListing,
  useListingDocuments,
  useMailDraft,
  useUpdateListingStatus,
  useVehicle,
} from "@/hooks/useListings";
import {
  COUNTRY_FLAG,
  LISTING_STATUS_LABEL,
  SANCTIONS_LABEL,
  SANCTIONS_VARIANT,
} from "@/lib/constants";
import { cn, formatApiError, formatPrice, shortId } from "@/lib/utils";
import type {
  ExportDocType,
  ListingStatus,
  MailDraftResponse,
  MailLanguage,
  MailScenario,
  SanctionsStatus,
} from "@/types/api";

const SCENARIO_OPTIONS: { value: MailScenario; label: string }[] = [
  { value: "inquiry", label: "신규 문의 응대" },
  { value: "quote", label: "견적 발송" },
  { value: "negotiate", label: "가격 협상 응대" },
  { value: "shipping", label: "선적 안내" },
  { value: "dispute", label: "분쟁·클레임 응대" },
];

const LANGUAGE_OPTIONS: { value: MailLanguage | ""; label: string }[] = [
  { value: "", label: "자동 (바이어 선호 → 국가 공식)" },
  { value: "en", label: "English" },
  { value: "es", label: "Español" },
  { value: "ar", label: "العربية" },
  { value: "ru", label: "Русский" },
  { value: "fr", label: "Français" },
  { value: "ko", label: "한국어" },
];

const DOC_TYPE_LABEL: Record<ExportDocType, string> = {
  invoice: "Commercial Invoice",
  packing_list: "Packing List",
  shipping_instruction: "Shipping Instruction",
  co_application: "C/O Application",
};

// 다음 가능한 status 전환 (백엔드 _FSM_TRANSITIONS 와 동기화)
const NEXT_STATUS: Record<ListingStatus, ListingStatus[]> = {
  inquiry: ["quoted", "negotiating"],
  quoted: ["negotiating", "agreed"],
  negotiating: ["quoted", "agreed"],
  agreed: ["documenting"],
  documenting: ["shipping"],
  shipping: ["in_transit", "arrived"],
  in_transit: ["arrived"],
  arrived: ["cleared"],
  cleared: ["delivered"],
  delivered: ["closed"],
  disputed: ["agreed", "closed"],
  closed: [],
};

export function ListingDetailPage() {
  const { id } = useParams<{ id: string }>();
  const listingQ = useListing(id);
  const vehicleQ = useVehicle(listingQ.data?.vehicle_id);
  const buyerQ = useBuyerById(listingQ.data?.buyer_id ?? undefined);
  const updateStatusMutation = useUpdateListingStatus();

  if (listingQ.isLoading) {
    return (
      <div className="space-y-4">
        <div className="h-8 w-1/3 animate-pulse rounded bg-muted" />
        <Card><CardContent className="h-64 animate-pulse" /></Card>
      </div>
    );
  }

  if (listingQ.isError || !listingQ.data) {
    return (
      <Card>
        <CardContent className="py-8 text-sm">
          <p className="font-medium text-destructive">거래를 찾을 수 없습니다</p>
          <p className="mt-1 text-muted-foreground">
            {formatApiError(listingQ.error) || "ID 가 잘못됐을 수 있습니다."}
          </p>
          <Link to="/listings" className="mt-3 inline-flex items-center gap-1 text-xs underline">
            <ArrowLeft className="h-3 w-3" /> 거래 목록으로
          </Link>
        </CardContent>
      </Card>
    );
  }

  const listing = listingQ.data;
  const vehicle = vehicleQ.data;
  const buyer = buyerQ.data;
  const flag = COUNTRY_FLAG[listing.destination_country ?? ""] ?? "🌐";
  const nextStatuses = NEXT_STATUS[listing.status] ?? [];
  // null guard — 신규 거래는 import-check 미실행 상태일 수 있음
  const ruleCheck = (listing.import_check_json ?? {}) as {
    can_import?: boolean;
    reasons?: string[];
    warnings?: string[];
    required_documents?: string[];
  };

  return (
    <div className="space-y-6">
      <header>
        <Link to="/listings" className="mb-1 inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground">
          <ArrowLeft className="h-3 w-3" /> 거래 목록
        </Link>
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <h2 className="flex items-center gap-2 text-2xl font-semibold tracking-tight">
              {vehicle ? `${vehicle.make ?? "?"} ${vehicle.model ?? "?"} ${vehicle.year ?? ""}` : "차량 로딩…"}
              <span className="text-base text-muted-foreground">→</span>
              <span className="text-base">{flag}</span>
              <span className="text-base">{listing.destination_country}</span>
            </h2>
            <p className="mt-1 flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
              <Badge variant="outline">{LISTING_STATUS_LABEL[listing.status] ?? listing.status}</Badge>
              <span className="font-mono text-xs">ID {shortId(listing.id)}</span>
              {listing.can_import === true && (
                <span className="flex items-center gap-1 text-success">
                  <CheckCircle2 className="h-3 w-3" /> 통관 OK
                </span>
              )}
              {listing.can_import === false && (
                <span className="flex items-center gap-1 text-destructive">
                  <XCircle className="h-3 w-3" /> 통관 차단
                </span>
              )}
            </p>
          </div>

          {/* Status FSM 전환 */}
          {nextStatuses.length > 0 && (
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs text-muted-foreground">상태 전환:</span>
              {nextStatuses.map((next) => (
                <Button
                  key={next}
                  variant="outline"
                  size="sm"
                  disabled={updateStatusMutation.isPending}
                  onClick={() => updateStatusMutation.mutate({ id: listing.id, status: next })}
                  className="gap-1"
                >
                  → {LISTING_STATUS_LABEL[next]}
                </Button>
              ))}
            </div>
          )}
        </div>
        {updateStatusMutation.isError && (
          <p role="alert" aria-live="polite" className="mt-2 text-xs text-destructive">
            상태 전환 실패: {formatApiError(updateStatusMutation.error)}
          </p>
        )}
      </header>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1fr_360px]">
        {/* 좌 — 본문 (요약 + 메일 + 서류) */}
        <div className="space-y-6">
          {/* Summary: vehicle + buyer + import-check */}
          <SummarySection
            vehicle={vehicle}
            buyer={buyer}
            ruleCheck={ruleCheck}
          />

          {/* 메일 작성 (Gemini) */}
          <MailComposerSection listingId={listing.id} buyer={buyer} />

          {/* 서류 4종 자동 생성 */}
          <DocumentsSection listingId={listing.id} canGenerate={Boolean(listing.buyer_id && listing.destination_country)} />
        </div>

        {/* 우 — 거래 메타 (sticky) */}
        <aside className="lg:sticky lg:top-6 lg:self-start space-y-4">
          <DealMetaCard listing={listing} />
          {buyer && (
            <ComplianceMiniCard
              status={buyer.sanctions_status}
              countryCode={buyer.country_code}
              riskScore={buyer.russia_proxy_risk_score}
            />
          )}
        </aside>
      </div>
    </div>
  );
}

// ── Summary section ───────────────────────────────────────
function SummarySection({
  vehicle,
  buyer,
  ruleCheck,
}: {
  vehicle: ReturnType<typeof useVehicle>["data"];
  buyer: ReturnType<typeof useBuyerById>["data"];
  ruleCheck: { reasons?: string[]; warnings?: string[]; required_documents?: string[] };
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">거래 요약</CardTitle>
      </CardHeader>
      <CardContent className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {/* Vehicle */}
        <div className="rounded-md border bg-muted/30 p-3">
          <div className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            <Car className="h-3.5 w-3.5" /> 매물
          </div>
          {vehicle ? (
            <div className="flex gap-3">
              <div className="h-16 w-24 shrink-0 overflow-hidden rounded bg-muted">
                {vehicle.image_url ? (
                  <img src={vehicle.image_url} alt="" className="h-full w-full object-cover" />
                ) : (
                  <div className="flex h-full w-full items-center justify-center">
                    <Car className="h-6 w-6 text-muted-foreground" />
                  </div>
                )}
              </div>
              <div className="min-w-0">
                <p className="truncate text-sm font-medium">
                  {vehicle.make} {vehicle.model} {vehicle.year}
                </p>
                <p className="text-xs text-muted-foreground">
                  {vehicle.engine_cc}cc · {vehicle.fuel_type} · {vehicle.steering}
                </p>
                <p className="text-xs text-muted-foreground">
                  {formatPrice(vehicle.list_price_usd)}
                </p>
              </div>
            </div>
          ) : (
            <p className="text-xs text-muted-foreground">로딩…</p>
          )}
        </div>

        {/* Buyer */}
        <div className="rounded-md border bg-muted/30 p-3">
          <div className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            <ShieldCheck className="h-3.5 w-3.5" /> 바이어
          </div>
          {buyer ? (
            <div>
              <p className="truncate text-sm font-medium">{buyer.company_name ?? "—"}</p>
              <p className="text-xs text-muted-foreground">{buyer.contact_person ?? ""}</p>
              <p className="text-xs text-muted-foreground">
                {COUNTRY_FLAG[buyer.country_code] ?? "🌐"} {buyer.country_code} ·{" "}
                <span className={cn(
                  buyer.sanctions_status === "blocked" && "text-destructive",
                  buyer.sanctions_status === "warning" && "text-warning",
                  buyer.sanctions_status === "clean" && "text-success",
                )}>
                  {SANCTIONS_LABEL[buyer.sanctions_status as SanctionsStatus]}
                </span>
              </p>
            </div>
          ) : (
            <p className="text-xs text-muted-foreground">로딩…</p>
          )}
        </div>

        {/* Import check 결과 */}
        <div className="rounded-md border bg-muted/30 p-3 sm:col-span-2">
          <div className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            <FileText className="h-3.5 w-3.5" /> 통관 평가 결과
          </div>
          {ruleCheck.reasons && ruleCheck.reasons.length > 0 && (
            <div className="mb-2">
              {ruleCheck.reasons.map((r, i) => (
                <p key={i} className="flex items-start gap-1.5 text-xs text-destructive">
                  <XCircle className="mt-0.5 h-3 w-3 shrink-0" /><span>{r}</span>
                </p>
              ))}
            </div>
          )}
          {ruleCheck.warnings && ruleCheck.warnings.length > 0 && (
            <div className="mb-2">
              {ruleCheck.warnings.map((w, i) => (
                <p key={i} className="flex items-start gap-1.5 text-xs text-warning">
                  <ShieldAlert className="mt-0.5 h-3 w-3 shrink-0" /><span>{w}</span>
                </p>
              ))}
            </div>
          )}
          {ruleCheck.required_documents && ruleCheck.required_documents.length > 0 && (
            <p className="text-xs text-muted-foreground">
              필요 서류: {ruleCheck.required_documents.join(", ")}
            </p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

// ── Mail composer (시연 시나리오 3) ──────────────────────
function MailComposerSection({
  listingId,
  buyer,
}: {
  listingId: string;
  buyer: ReturnType<typeof useBuyerById>["data"];
}) {
  const [scenario, setScenario] = useState<MailScenario>("quote");
  const [language, setLanguage] = useState<string>("");
  const [extra, setExtra] = useState("");
  const [editedSubject, setEditedSubject] = useState("");
  const [editedBody, setEditedBody] = useState("");
  const [copied, setCopied] = useState(false);

  const draftMutation = useMailDraft(listingId);

  const onGenerate = async () => {
    setCopied(false);
    const r = await draftMutation.mutateAsync({
      scenario,
      language: language || undefined,
      extra_context: extra || undefined,
    });
    setEditedSubject(r.subject);
    setEditedBody(r.body);
  };

  const onCopy = async () => {
    const text = `Subject: ${editedSubject}\n\n${editedBody}`;
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const result: MailDraftResponse | undefined = draftMutation.data;

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="flex items-center gap-2 text-base">
          <Mail className="h-4 w-4" /> 다국어 메일 작성 (Gemini)
        </CardTitle>
        {result && (
          <span className="text-[10px] uppercase tracking-wider text-muted-foreground">
            {result.provider} · {result.model}
          </span>
        )}
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <div>
            <label className="text-sm font-medium">시나리오</label>
            <select
              value={scenario}
              onChange={(e) => setScenario(e.target.value as MailScenario)}
              className="mt-1 flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm"
            >
              {SCENARIO_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-sm font-medium">언어</label>
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              className="mt-1 flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm"
            >
              {LANGUAGE_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
            {!language && buyer?.preferred_language && (
              <p className="mt-1 text-[10px] text-muted-foreground">
                자동 감지: 바이어 선호 {buyer.preferred_language.toUpperCase()}
              </p>
            )}
          </div>
        </div>

        <div>
          <label className="text-sm font-medium">추가 컨텍스트 (선택)</label>
          <textarea
            value={extra}
            onChange={(e) => setExtra(e.target.value)}
            placeholder="예: Buyer asked for total CIF Santo Domingo with 28-35 day shipping window."
            rows={2}
            className="mt-1 flex w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm"
          />
        </div>

        <Button
          onClick={onGenerate}
          disabled={draftMutation.isPending}
          className="w-full gap-2"
        >
          {draftMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
          {draftMutation.isPending ? "Gemini 생성 중... (~5초)" : "AI로 메일 생성하기"}
        </Button>

        {draftMutation.isError && (
          <div role="alert" aria-live="polite" className="rounded-md border border-destructive/30 bg-destructive/5 p-3 text-sm">
            <p className="font-medium text-destructive">생성 실패</p>
            <p className="mt-1 text-xs text-muted-foreground">
              {formatApiError(draftMutation.error)}
            </p>
          </div>
        )}

        {result && (
          <div className="space-y-3 rounded-md border bg-muted/30 p-4">
            <div>
              <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Subject</label>
              <Input
                value={editedSubject}
                onChange={(e) => setEditedSubject(e.target.value)}
                className="mt-1 font-medium"
              />
            </div>
            <div>
              <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Body</label>
              <textarea
                value={editedBody}
                onChange={(e) => setEditedBody(e.target.value)}
                rows={Math.min(20, Math.max(8, editedBody.split("\n").length))}
                className="mt-1 flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm leading-relaxed"
                dir={result.language === "ar" ? "rtl" : "ltr"}
              />
            </div>
            <div className="flex items-center gap-2">
              <Button onClick={onCopy} variant="outline" className="gap-2">
                {copied ? <ClipboardCheck className="h-4 w-4 text-success" /> : <Clipboard className="h-4 w-4" />}
                {copied ? "복사됨" : "클립보드 복사"}
              </Button>
              <span className="text-xs text-muted-foreground">
                ✓ AI 초안 DB 저장됨 · 편집본은 미저장 (id: {shortId(result.message_id)})
              </span>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// ── Documents section (시연 시나리오 4) ──────────────────
function DocumentsSection({
  listingId,
  canGenerate,
}: {
  listingId: string;
  canGenerate: boolean;
}) {
  const docsQ = useListingDocuments(listingId);
  const generateMutation = useGenerateDocuments(listingId);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <FileText className="h-4 w-4" /> 수출 서류 4종 자동 생성
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center gap-3">
          <Button
            onClick={() => generateMutation.mutate()}
            disabled={!canGenerate || generateMutation.isPending}
            className="gap-2"
          >
            {generateMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
            {generateMutation.isPending
              ? "Playwright 생성 중... (~10초)"
              : (docsQ.data && docsQ.data.length > 0)
                ? "4종 PDF 다시 생성"
                : "4종 PDF 생성하기"}
          </Button>
          {!canGenerate && (
            <p className="text-xs text-muted-foreground">
              바이어·도착국 설정 필요
            </p>
          )}
        </div>

        {generateMutation.isError && (
          <div role="alert" aria-live="polite" className="rounded-md border border-destructive/30 bg-destructive/5 p-3 text-sm text-destructive">
            생성 실패: {formatApiError(generateMutation.error)}
          </div>
        )}

        {docsQ.data && docsQ.data.length > 0 && (
          <div className={cn(
            "grid grid-cols-2 gap-3 transition-opacity sm:grid-cols-4",
            generateMutation.isPending && "pointer-events-none opacity-50",
          )}>
            {docsQ.data.map((d) => (
              <a
                key={d.id}
                href={d.pdf_url ?? undefined}
                aria-disabled={!d.pdf_url}
                onClick={(e) => { if (!d.pdf_url) e.preventDefault(); }}
                target="_blank"
                rel="noopener noreferrer"
                className="group flex flex-col items-center gap-2 rounded-md border bg-card p-3 text-center transition hover:border-primary/40 hover:shadow-md aria-disabled:cursor-not-allowed aria-disabled:opacity-50"
              >
                <FileText className="h-8 w-8 text-primary" />
                <p className="text-xs font-medium">{DOC_TYPE_LABEL[d.doc_type]}</p>
                <span className="inline-flex items-center gap-1 text-[10px] text-muted-foreground group-hover:text-primary">
                  <Download className="h-3 w-3" /> 다운로드
                </span>
              </a>
            ))}
          </div>
        )}
        {generateMutation.isPending && docsQ.data && docsQ.data.length > 0 && (
          <p className="text-xs text-warning">⚠ 재생성 중 — 기존 다운로드 링크가 곧 새 파일로 교체됩니다.</p>
        )}

        {docsQ.data && docsQ.data.length === 0 && !generateMutation.isPending && (
          <p className="rounded-md bg-muted/50 px-3 py-6 text-center text-xs text-muted-foreground">
            아직 생성된 서류가 없습니다. 위 버튼을 클릭하면 4종 PDF (Invoice / PL / SI / C/O) 가
            한 번에 생성됩니다.
          </p>
        )}
      </CardContent>
    </Card>
  );
}

// ── Right sidebar cards ───────────────────────────────────
function DealMetaCard({ listing }: { listing: ReturnType<typeof useListing>["data"] }) {
  if (!listing) return null;
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm">거래 메타</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2 text-xs">
        <Row label="합의 가격" value={formatPrice(listing.agreed_price_usd)} />
        <Row label="Incoterm" value={listing.incoterm ?? "—"} />
        <Row label="결제 조건" value={listing.payment_terms ?? "—"} />
        <Row label="선적 방식" value={listing.shipping_method ?? "—"} />
        <Row label="선적항" value={listing.port_of_loading ?? "Incheon"} />
        <Row label="도착항" value={listing.port_of_discharge ?? "—"} />
        {listing.notes && (
          <div className="border-t pt-2">
            <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">메모</p>
            <p className="mt-1">{listing.notes}</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function ComplianceMiniCard({
  status,
  countryCode,
  riskScore,
}: {
  status: SanctionsStatus | string;
  countryCode: string;
  riskScore: number | null;
}) {
  const variant = SANCTIONS_VARIANT[status as SanctionsStatus] ?? "outline";
  const Icon = status === "blocked" ? ShieldX : status === "warning" ? ShieldAlert : ShieldCheck;
  return (
    <Card className={cn(
      status === "blocked" && "border-destructive/40 bg-destructive/5",
      status === "warning" && "border-warning/40 bg-warning/5",
      status === "clean" && "border-success/40 bg-success/5",
    )}>
      <CardContent className="flex items-center gap-3 p-4">
        <Icon className={cn(
          "h-5 w-5",
          status === "blocked" && "text-destructive",
          status === "warning" && "text-warning",
          status === "clean" && "text-success",
        )} />
        <div className="flex-1">
          <p className="text-xs font-semibold">바이어 Compliance</p>
          <p className="mt-0.5 text-[10px] text-muted-foreground">
            {COUNTRY_FLAG[countryCode] ?? "🌐"} {countryCode} ·{" "}
            {riskScore !== null && riskScore > 0 ? `risk ${riskScore}` : "risk 0"}
          </p>
        </div>
        <Badge variant={variant}>{SANCTIONS_LABEL[status as SanctionsStatus] ?? status}</Badge>
      </CardContent>
    </Card>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between gap-2">
      <span className="text-muted-foreground">{label}</span>
      <span className="font-medium tabular-nums">{value}</span>
    </div>
  );
}
