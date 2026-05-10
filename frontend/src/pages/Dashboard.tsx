import { useQuery } from "@tanstack/react-query";
import { AlertTriangle, Car, FileText, ShieldCheck, Users } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";
import { formatApiError } from "@/lib/utils";
import type { DashboardSummary } from "@/types/api";

export function DashboardPage() {
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["dashboard-summary"],
    queryFn: async (): Promise<DashboardSummary> => {
      const r = await api.get<DashboardSummary>("/api/dashboard/summary");
      return r.data;
    },
    staleTime: 60_000,
  });

  return (
    <div className="space-y-6">
      <header>
        <h2 className="text-2xl font-semibold tracking-tight">대시보드</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          오늘의 매물·거래·컴플라이언스 한눈에 보기
        </p>
      </header>

      {isLoading && <p className="text-sm text-muted-foreground">불러오는 중…</p>}
      {isError && (
        <Card>
          <CardContent className="py-8 text-sm">
            <p className="font-medium text-destructive">백엔드 연결 실패</p>
            <p className="mt-1 text-muted-foreground">
              백엔드 서버가 켜져 있는지 확인하세요:
              <code className="mx-1 rounded bg-muted px-1.5 py-0.5 text-xs">
                cd backend && uvicorn app.main:app --reload
              </code>
            </p>
            <p className="mt-2 text-xs text-muted-foreground">상세: {formatApiError(error)}</p>
          </CardContent>
        </Card>
      )}

      {data && (
        <>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <KpiCard
              icon={Car}
              label="매물"
              primary={data.counts.vehicles_available}
              suffix={`/ ${data.counts.vehicles_total}`}
              hint="판매 가능 / 전체"
            />
            <KpiCard
              icon={Users}
              label="바이어"
              primary={data.counts.buyers_total}
              hint={`경고 ${data.counts.buyers_warning} · 차단 ${data.counts.buyers_blocked}`}
            />
            <KpiCard
              icon={FileText}
              label="진행 중 거래"
              primary={data.counts.listings_in_progress}
              hint={`문의 ${data.counts.listings_inquiry} · 선적 ${data.counts.listings_shipping}`}
            />
            <KpiCard
              icon={ShieldCheck}
              label="완료"
              primary={data.counts.listings_delivered}
              hint="delivered + closed"
            />
          </div>

          <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
            <Card className="lg:col-span-2">
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle className="text-base">최근 거래</CardTitle>
                <span className="text-xs text-muted-foreground">
                  {data.recent_listings.length}건
                </span>
              </CardHeader>
              <CardContent className="px-0">
                <table className="w-full text-sm">
                  <thead className="border-y bg-muted/30 text-xs uppercase text-muted-foreground">
                    <tr>
                      <th className="px-6 py-2 text-left">매물</th>
                      <th className="px-3 py-2 text-left">바이어</th>
                      <th className="px-3 py-2 text-left">목적국</th>
                      <th className="px-3 py-2 text-left">상태</th>
                      <th className="px-3 py-2 text-left">통관</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.recent_listings.length === 0 && (
                      <tr>
                        <td colSpan={5} className="px-6 py-6 text-center text-muted-foreground">
                          거래가 없습니다.
                        </td>
                      </tr>
                    )}
                    {data.recent_listings.map((l) => (
                      <tr key={l.id} className="border-b last:border-0">
                        <td className="px-6 py-3 font-medium">{l.vehicle_label}</td>
                        <td className="px-3 py-3 text-muted-foreground">{l.buyer_name ?? "—"}</td>
                        <td className="px-3 py-3">{l.destination_country ?? "—"}</td>
                        <td className="px-3 py-3">
                          <Badge variant="secondary">{l.status}</Badge>
                        </td>
                        <td className="px-3 py-3">
                          {l.can_import === true && <Badge variant="success">통과</Badge>}
                          {l.can_import === false && <Badge variant="destructive">차단</Badge>}
                          {l.can_import === null && <Badge variant="outline">미평가</Badge>}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle className="text-base">컴플라이언스 경고</CardTitle>
                <AlertTriangle className="h-4 w-4 text-warning" />
              </CardHeader>
              <CardContent className="space-y-3">
                {data.compliance_alerts.length === 0 ? (
                  <p className="text-sm text-muted-foreground">경고 없음 ✓</p>
                ) : (
                  data.compliance_alerts.map((a) => (
                    <div
                      key={a.buyer_id}
                      className="flex items-start gap-3 rounded-md border bg-warning/5 p-3"
                    >
                      <AlertTriangle className="h-4 w-4 shrink-0 text-warning" />
                      <div className="min-w-0 flex-1 text-sm">
                        <p className="truncate font-medium">{a.company_name}</p>
                        <p className="mt-0.5 text-xs text-muted-foreground">
                          {a.country_code} · {a.sanctions_status}
                          {a.russia_proxy_risk_score !== null
                            ? ` · risk ${a.russia_proxy_risk_score}`
                            : ""}
                        </p>
                      </div>
                    </div>
                  ))
                )}
              </CardContent>
            </Card>
          </div>
        </>
      )}
    </div>
  );
}

function KpiCard({
  icon: Icon,
  label,
  primary,
  suffix,
  hint,
}: {
  icon: typeof Car;
  label: string;
  primary: number;
  suffix?: string;
  hint?: string;
}) {
  return (
    <Card>
      <CardContent className="py-5">
        <div className="flex items-center justify-between">
          <p className="text-sm font-medium text-muted-foreground">{label}</p>
          <Icon className="h-4 w-4 text-muted-foreground" />
        </div>
        <p className="mt-2 text-2xl font-semibold tabular-nums">
          {primary}
          {suffix && <span className="ml-1 text-base font-normal text-muted-foreground">{suffix}</span>}
        </p>
        {hint && <p className="mt-1 text-xs text-muted-foreground">{hint}</p>}
      </CardContent>
    </Card>
  );
}
