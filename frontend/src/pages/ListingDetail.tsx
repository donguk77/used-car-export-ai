import { useState } from "react";
import {
  ArrowLeft,
  Car,
  CheckCircle2,
  Clipboard,
  ClipboardCheck,
  Download,
  FileText,
  History,
  Loader2,
  Mail,
  RefreshCw,
  Send,
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
  useListingMessages,
  useMailDraft,
  useMailRegenerateFromKorean,
  useSendMessage,
  useUpdateListingStatus,
  useVehicle,
  type MessageRecord,
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

          {/* 메일 history (draft + sent) */}
          <MailHistorySection listingId={listing.id} />

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
  const [includeTranslation, setIncludeTranslation] = useState(false);
  const [editedSubject, setEditedSubject] = useState("");
  const [editedBody, setEditedBody] = useState("");
  const [editedKorean, setEditedKorean] = useState("");
  const [originalKorean, setOriginalKorean] = useState("");
  const [strictRegen, setStrictRegen] = useState(false);
  const [copied, setCopied] = useState(false);

  const draftMutation = useMailDraft(listingId);
  const regenerateMutation = useMailRegenerateFromKorean(listingId);

  // 한국어 번역 옵션은 외국어일 때만 의미 — language=ko 면 자동 false
  const wantsTranslation = includeTranslation && language !== "ko";

  const onGenerate = async () => {
    setCopied(false);
    const r = await draftMutation.mutateAsync({
      scenario,
      language: language || undefined,
      extra_context: extra || undefined,
      include_translation: wantsTranslation,
    });
    setEditedSubject(r.subject);
    setEditedBody(r.body);
    setEditedKorean(r.translation_ko ?? "");
    setOriginalKorean(r.translation_ko ?? "");
  };

  const onRegenerateFromKorean = async () => {
    if (!editedKorean.trim()) return;
    setCopied(false);
    // language 자동 감지 결과를 사용 — language state 가 빈 문자열이면 result.language
    const target = language || draftMutation.data?.language;
    if (!target || target === "ko") return;
    const r = await regenerateMutation.mutateAsync({
      scenario,
      target_language: target,
      korean_body: editedKorean,
      strict: strictRegen,
    });
    setEditedSubject(r.subject);
    setEditedBody(r.body);
    setEditedKorean(r.translation_ko ?? "");
    setOriginalKorean(r.translation_ko ?? "");
  };

  // 한국어가 dirty (사용자가 수정함) 이고 외국어 메일이 있을 때만 재생성 버튼 활성
  const koreanDirty = editedKorean !== originalKorean;

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

        {/* 한국어 검증 옵션 — 외국어 메일 시 신뢰성 ↑ (LLM 호출 +1, 시간 약 2배) */}
        <label className={cn(
          "flex items-start gap-2 rounded-md border border-dashed p-2.5 text-xs",
          language === "ko"
            ? "cursor-not-allowed border-muted-foreground/20 opacity-50"
            : "cursor-pointer border-primary/30 bg-primary/5",
        )}>
          <input
            type="checkbox"
            checked={wantsTranslation}
            disabled={language === "ko"}
            onChange={(e) => setIncludeTranslation(e.target.checked)}
            className="mt-0.5 h-3.5 w-3.5 accent-primary"
          />
          <span className="flex-1">
            <span className="font-medium">한국어 번역도 함께 표시 (검증용)</span>
            {language === "ko" ? (
              <span className="ml-1 text-muted-foreground">— 한국어 메일에는 불필요</span>
            ) : (
              <span className="ml-1 text-muted-foreground">— 외국어 메일을 한국어로 한번 더 검토 (LLM 호출 2배, 약 30초)</span>
            )}
          </span>
        </label>

        <Button
          onClick={onGenerate}
          disabled={draftMutation.isPending}
          className="w-full gap-2"
        >
          {draftMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
          {draftMutation.isPending
            ? wantsTranslation
              ? "Gemini 생성 중... (외국어 + 한국어 번역, ~30초)"
              : "Gemini 생성 중... (~15초)"
            : wantsTranslation
              ? "AI로 메일 생성하기 (한국어 검증 포함)"
              : "AI로 메일 생성하기"}
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
            {result.translation_ko ? (
              // 2-column: 외국어 (발송용) ↔ 한국어 (편집 가능 → 외국어 재생성)
              <div className="space-y-3">
                <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
                  <div>
                    <label className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                      📤 {result.language.toUpperCase()} (발송용)
                      {result.language === "ar" && (
                        <span className="text-[9px] normal-case text-muted-foreground/70">— RTL 자연 정렬</span>
                      )}
                    </label>
                    <textarea
                      value={editedBody}
                      onChange={(e) => setEditedBody(e.target.value)}
                      rows={Math.min(28, Math.max(12, editedBody.split("\n").length))}
                      className="mt-1 flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm leading-relaxed"
                      dir={result.language === "ar" ? "rtl" : "ltr"}
                    />
                  </div>
                  <div>
                    <label className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                      🇰🇷 KO (검증·편집 가능)
                      {koreanDirty && (
                        <span className="text-[9px] normal-case font-bold text-warning">● 수정됨</span>
                      )}
                    </label>
                    <textarea
                      value={editedKorean}
                      onChange={(e) => setEditedKorean(e.target.value)}
                      rows={Math.min(28, Math.max(12, editedKorean.split("\n").length))}
                      className={cn(
                        "mt-1 flex w-full rounded-md border px-3 py-2 text-sm leading-relaxed",
                        koreanDirty ? "border-warning bg-warning/5" : "border-input bg-muted/40 text-muted-foreground",
                      )}
                      dir="ltr"
                      placeholder="이 한국어 본문을 수정한 뒤 아래 '한국어로 외국어 재생성' 버튼을 누르면 외국어 메일이 다시 만들어집니다."
                    />
                  </div>
                </div>
                {/* Level 2 재생성 컨트롤 — Strict 토글 + 버튼 */}
                <div className="space-y-2 rounded-md border border-dashed border-primary/30 bg-primary/5 p-3">
                  <div className="flex items-center justify-between gap-2">
                    <p className="flex-1 text-xs text-muted-foreground">
                      {koreanDirty
                        ? "한국어를 수정하셨습니다 — 외국어 메일을 새로 생성해 반영하세요."
                        : "한국어 패널을 직접 수정한 뒤, 그 의도로 외국어 메일을 다시 만들 수 있습니다."}
                    </p>
                    <Button
                      onClick={onRegenerateFromKorean}
                      disabled={!koreanDirty || regenerateMutation.isPending}
                      size="sm"
                      className="gap-2"
                    >
                      {regenerateMutation.isPending ? (
                        <Loader2 className="h-3.5 w-3.5 animate-spin" />
                      ) : (
                        <RefreshCw className="h-3.5 w-3.5" />
                      )}
                      {regenerateMutation.isPending
                        ? "재생성 중... (~30초)"
                        : "한국어로 외국어 재생성"}
                    </Button>
                  </div>
                  <label className="flex items-start gap-2 text-[11px] text-muted-foreground cursor-pointer">
                    <input
                      type="checkbox"
                      checked={strictRegen}
                      onChange={(e) => setStrictRegen(e.target.checked)}
                      className="mt-0.5 h-3 w-3 accent-primary"
                    />
                    <span>
                      <strong>Strict literal 모드</strong> — 한국어 톤·오타·구두점을 그대로 번역 (off: 비즈니스 격식체로 자동 polish + 오타 보정)
                    </span>
                  </label>
                </div>
                {regenerateMutation.isError && (
                  <p role="alert" className="text-xs text-destructive">
                    재생성 실패: {formatApiError(regenerateMutation.error)}
                  </p>
                )}
              </div>
            ) : (
              // 단일 column — 한국어 메일 또는 번역 옵션 off
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
            )}
            <div className="flex items-center gap-2">
              <Button onClick={onCopy} variant="outline" className="gap-2">
                {copied ? <ClipboardCheck className="h-4 w-4 text-success" /> : <Clipboard className="h-4 w-4" />}
                {copied ? "복사됨" : "클립보드 복사"}
              </Button>
              <span className="text-xs text-muted-foreground">
                ✓ AI 초안 DB 저장됨 · 편집본은 미저장 (id: {shortId(result.message_id)})
                {result.translation_ko && " · 한국어 번역은 DB 저장 X (참고용)"}
              </span>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// ── Mail history (draft + sent + 보내기 버튼) ──────────────
function MailHistorySection({ listingId }: { listingId: string }) {
  const messagesQ = useListingMessages(listingId);
  const sendMutation = useSendMessage(listingId);
  const [expanded, setExpanded] = useState<string | null>(null);

  const items = messagesQ.data ?? [];
  const draftCount = items.filter((m) => !m.sent_at).length;
  const sentCount = items.filter((m) => m.sent_at).length;

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="flex items-center gap-2 text-base">
          <History className="h-4 w-4" /> 메일 history
        </CardTitle>
        {!messagesQ.isLoading && items.length > 0 && (
          <span className="text-[10px] uppercase tracking-wider text-muted-foreground">
            draft {draftCount} · sent {sentCount}
          </span>
        )}
      </CardHeader>
      <CardContent>
        {messagesQ.isLoading ? (
          <p className="text-xs text-muted-foreground">로딩…</p>
        ) : items.length === 0 ? (
          <p className="rounded-md bg-muted/50 px-3 py-6 text-center text-xs text-muted-foreground">
            아직 작성된 메일이 없습니다 — 위 "AI로 메일 생성하기" 버튼 클릭
          </p>
        ) : (
          <ul className="space-y-2">
            {items.map((m) => (
              <MailHistoryRow
                key={m.id}
                message={m}
                expanded={expanded === m.id}
                onToggle={() => setExpanded(expanded === m.id ? null : m.id)}
                onSend={() => sendMutation.mutate(m.id)}
                sending={sendMutation.isPending && sendMutation.variables === m.id}
              />
            ))}
          </ul>
        )}
        {sendMutation.isError && (
          <p role="alert" className="mt-2 text-xs text-destructive">
            전송 실패: {formatApiError(sendMutation.error)}
          </p>
        )}
      </CardContent>
    </Card>
  );
}

function MailHistoryRow({
  message,
  expanded,
  onToggle,
  onSend,
  sending,
}: {
  message: MessageRecord;
  expanded: boolean;
  onToggle: () => void;
  onSend: () => void;
  sending: boolean;
}) {
  const sent = Boolean(message.sent_at);
  const subject = (message.content_text ?? "").split("\n", 1)[0].replace(/^Subject:\s*/, "");
  const body = (message.content_text ?? "").split("\n").slice(1).join("\n").trim();

  return (
    <li className={cn(
      "rounded-md border transition-colors",
      sent ? "border-success/30 bg-success/5" : "border-warning/30 bg-warning/5",
    )}>
      <button
        type="button"
        onClick={onToggle}
        className="flex w-full items-start gap-2.5 px-3 py-2.5 text-left"
      >
        <Mail className={cn("mt-0.5 h-4 w-4 shrink-0", sent ? "text-success" : "text-warning")} />
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-medium">{subject || "(제목 없음)"}</p>
          <p className="mt-0.5 text-[11px] text-muted-foreground">
            {message.scenario ?? "—"} · {message.language?.toUpperCase() ?? "—"}
            {message.ai_model && ` · ${message.ai_model}`}
            {sent
              ? ` · sent ${new Date(message.sent_at!).toLocaleString("ko-KR", { dateStyle: "short", timeStyle: "short" })}`
              : " · draft"}
          </p>
        </div>
        {sent ? (
          <span className="flex shrink-0 items-center gap-1 text-[10px] font-semibold text-success">
            <CheckCircle2 className="h-3 w-3" /> SENT
          </span>
        ) : (
          <Button
            type="button"
            size="sm"
            disabled={sending}
            onClick={(e) => { e.stopPropagation(); onSend(); }}
            className="shrink-0 gap-1"
          >
            {sending ? <Loader2 className="h-3 w-3 animate-spin" /> : <Send className="h-3 w-3" />}
            {sending ? "전송중" : "보내기"}
          </Button>
        )}
      </button>
      {expanded && body && (
        <div
          className="border-t bg-background px-3 py-3 text-xs leading-relaxed whitespace-pre-wrap"
          dir={message.language === "ar" ? "rtl" : "ltr"}
        >
          {body}
        </div>
      )}
    </li>
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
