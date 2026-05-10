import { useState } from "react";
import { AxiosError } from "axios";
import {
  AlertTriangle,
  ArrowLeft,
  Building2,
  CheckCircle2,
  Loader2,
  Mail,
  MapPin,
  Phone,
  Plus,
  RefreshCw,
  ShieldAlert,
  ShieldCheck,
  ShieldX,
  Trash2,
  XCircle,
} from "lucide-react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { CreateListingModal } from "@/components/CreateListingModal";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useBuyer, useDeleteBuyer, useRecheckBuyer } from "@/hooks/useBuyers";
import {
  COUNTRY_FLAG,
  SANCTIONS_LABEL,
  SANCTIONS_VARIANT,
} from "@/lib/constants";
import { cn } from "@/lib/utils";
import type { SanctionsStatus } from "@/types/api";

export function BuyerDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [createListingOpen, setCreateListingOpen] = useState(false);

  const { data: buyer, isLoading, isError, error } = useBuyer(id);
  const recheckMutation = useRecheckBuyer();
  const deleteMutation = useDeleteBuyer();

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

  if (isError || !buyer) {
    return (
      <Card>
        <CardContent className="py-8 text-sm">
          <p className="font-medium text-destructive">바이어를 찾을 수 없습니다</p>
          <p className="mt-1 text-muted-foreground">
            {error instanceof AxiosError
              ? (error.response?.data?.detail ?? error.message)
              : (error as Error)?.message ?? "이미 삭제됐거나 ID가 잘못됐을 수 있습니다."}
          </p>
          <Link to="/buyers" className="mt-3 inline-flex items-center gap-1 text-xs underline">
            <ArrowLeft className="h-3 w-3" /> 바이어 목록으로
          </Link>
        </CardContent>
      </Card>
    );
  }

  const flag = COUNTRY_FLAG[buyer.country_code] ?? "🌐";
  const variant = SANCTIONS_VARIANT[buyer.sanctions_status as SanctionsStatus] ?? "outline";
  const SanctionsIcon = sanctionsIcon(buyer.sanctions_status);

  const onRecheck = () => recheckMutation.mutate(buyer.id);
  const onDelete = () => {
    if (!confirm(`바이어 "${buyer.company_name ?? buyer.id}" 를 삭제하시겠습니까?`)) return;
    deleteMutation.mutate(buyer.id, {
      onSuccess: () => navigate("/buyers"),
    });
  };

  const recheckResult = recheckMutation.data;

  return (
    <div className="space-y-6">
      <header>
        <Link
          to="/buyers"
          className="mb-1 inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="h-3 w-3" /> 바이어 목록
        </Link>
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div className="min-w-0 flex-1">
            <h2 className="flex items-center gap-2 text-2xl font-semibold tracking-tight">
              <span className="text-2xl">{flag}</span>
              {buyer.company_name ?? "—"}
            </h2>
            <p className="mt-1 flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
              <Badge variant={variant}>
                <SanctionsIcon className="mr-1 h-3 w-3" />
                {SANCTIONS_LABEL[buyer.sanctions_status as SanctionsStatus] ?? buyer.sanctions_status}
              </Badge>
              {buyer.contact_person && <span>· {buyer.contact_person}</span>}
              {buyer.country_code && <span>· {buyer.country_code}</span>}
              {buyer.tax_id && <span className="font-mono text-xs">· Tax {buyer.tax_id}</span>}
            </p>
          </div>
          <div className="flex gap-2">
            <Button
              onClick={() => setCreateListingOpen(true)}
              disabled={buyer.sanctions_status === "blocked"}
              title={buyer.sanctions_status === "blocked" ? "Blocked 바이어는 거래 생성 불가" : undefined}
              className="gap-2"
            >
              <Plus className="h-4 w-4" /> 이 바이어와 거래 만들기
            </Button>
            <Button variant="outline" onClick={onRecheck} disabled={recheckMutation.isPending} className="gap-2">
              {recheckMutation.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <RefreshCw className="h-4 w-4" />
              )}
              Compliance 재검사
            </Button>
            <Button variant="destructive" onClick={onDelete} disabled={deleteMutation.isPending} className="gap-2">
              {deleteMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Trash2 className="h-4 w-4" />}
              삭제
            </Button>
          </div>
        </div>
      </header>

      {recheckMutation.isError && (
        <div className="rounded-md border border-destructive/30 bg-destructive/5 p-3 text-sm text-destructive">
          재검사 실패:{" "}
          {recheckMutation.error instanceof AxiosError
            ? (recheckMutation.error.response?.data?.detail ?? recheckMutation.error.message)
            : (recheckMutation.error as Error)?.message}
        </div>
      )}

      {recheckResult && (
        <div className="rounded-md border border-success/30 bg-success/5 p-3 text-sm">
          <p className="font-medium text-success">✓ 재검사 완료</p>
          <p className="mt-1 text-xs text-muted-foreground">
            결과: {recheckResult.overall} · 점수 {recheckResult.score}/100 · 발견 {recheckResult.findings.length}건
          </p>
        </div>
      )}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1fr_360px]">
        {/* 좌 — 프로필 */}
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">기본 정보</CardTitle>
            </CardHeader>
            <CardContent className="grid grid-cols-2 gap-x-4 gap-y-3 sm:grid-cols-3">
              <Spec icon={Building2} label="회사명" value={buyer.company_name} />
              <Spec label="담당자" value={buyer.contact_person} />
              <Spec icon={MapPin} label="국가" value={`${flag} ${buyer.country_code}`} />
              <Spec label="도시" value={buyer.city} />
              <div className="col-span-full">
                <Spec label="주소" value={buyer.address} />
              </div>
              <Spec icon={Phone} label="전화" value={buyer.phone} />
              <Spec label="WhatsApp" value={buyer.whatsapp} />
              <Spec icon={Mail} label="이메일" value={buyer.email} />
              <Spec label="Tax ID" value={buyer.tax_id} mono />
              <Spec label="사업자번호" value={buyer.business_license} mono />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">선호도</CardTitle>
            </CardHeader>
            <CardContent className="grid grid-cols-2 gap-x-4 gap-y-3 sm:grid-cols-3">
              <Spec label="언어" value={buyer.preferred_language?.toUpperCase()} />
              <Spec label="통화" value={buyer.preferred_currency} />
              <Spec label="결제" value={buyer.preferred_payment} />
              <Spec label="Incoterm" value={buyer.preferred_incoterm} />
              <Spec label="항구" value={buyer.preferred_port} />
              <Spec label="구매 유형" value={buyer.buyer_type} />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">거래 통계</CardTitle>
            </CardHeader>
            <CardContent className="grid grid-cols-3 gap-4">
              <Stat label="총 거래" value={buyer.total_orders.toString()} />
              <Stat
                label="russia proxy 위험점수"
                value={buyer.russia_proxy_risk_score?.toString() ?? "—"}
                emphasis={buyer.russia_proxy_risk_score && buyer.russia_proxy_risk_score > 0 ? "warning" : undefined}
              />
              <Stat label="현재 sanctions 상태" value={SANCTIONS_LABEL[buyer.sanctions_status as SanctionsStatus] ?? buyer.sanctions_status} />
            </CardContent>
          </Card>
        </div>

        {/* 우 — Compliance 요약 */}
        <aside className="lg:sticky lg:top-6 lg:self-start space-y-4">
          <Card className={cn(
            buyer.sanctions_status === "blocked" ? "border-destructive/40 bg-destructive/5"
            : buyer.sanctions_status === "warning" ? "border-warning/40 bg-warning/5"
            : "border-success/40 bg-success/5",
          )}>
            <CardContent className="space-y-3 p-5">
              <div className="flex items-center gap-2">
                <SanctionsIcon className={cn(
                  "h-6 w-6",
                  buyer.sanctions_status === "blocked" ? "text-destructive"
                  : buyer.sanctions_status === "warning" ? "text-warning"
                  : "text-success",
                )} />
                <div>
                  <p className="text-sm font-bold">
                    {buyer.sanctions_status === "blocked" ? "거래 차단됨"
                    : buyer.sanctions_status === "warning" ? "주의 필요"
                    : buyer.sanctions_status === "unchecked" ? "미검사"
                    : "거래 가능"}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {SANCTIONS_LABEL[buyer.sanctions_status as SanctionsStatus] ?? buyer.sanctions_status}
                  </p>
                </div>
              </div>

              {recheckResult && recheckResult.findings.length > 0 && (
                <div className="space-y-2 border-t pt-3">
                  <p className="text-xs font-semibold text-muted-foreground">최근 검사 결과</p>
                  {recheckResult.findings.map((f, i) => (
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

              {!recheckResult && (
                <p className="border-t pt-3 text-xs text-muted-foreground">
                  상세 결과를 보려면 위의 <strong>Compliance 재검사</strong> 클릭.
                </p>
              )}
            </CardContent>
          </Card>
        </aside>
      </div>

      <CreateListingModal
        open={createListingOpen}
        onClose={() => setCreateListingOpen(false)}
        prefillBuyerId={buyer.id}
      />
    </div>
  );
}

function sanctionsIcon(status: string): typeof ShieldCheck {
  if (status === "blocked") return ShieldX;
  if (status === "warning") return ShieldAlert;
  return ShieldCheck;
}

function Spec({
  icon: Icon,
  label,
  value,
  mono = false,
}: {
  icon?: typeof Building2;
  label: string;
  value: string | number | null | undefined;
  mono?: boolean;
}) {
  return (
    <div>
      <p className="flex items-center gap-1 text-[10px] uppercase tracking-wider text-muted-foreground">
        {Icon && <Icon className="h-3 w-3" />}
        {label}
      </p>
      <p className={cn("text-sm font-medium", mono && "font-mono")}>{value ?? "—"}</p>
    </div>
  );
}

function Stat({
  label,
  value,
  emphasis,
}: {
  label: string;
  value: string;
  emphasis?: "warning" | "destructive";
}) {
  return (
    <div className="rounded-md border bg-background p-3 text-center">
      <p className={cn(
        "text-xl font-bold tabular-nums",
        emphasis === "warning" && "text-warning",
        emphasis === "destructive" && "text-destructive",
      )}>
        {value}
      </p>
      <p className="mt-1 text-[11px] text-muted-foreground">{label}</p>
    </div>
  );
}
