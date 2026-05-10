import { ArrowRight, FileText, Mail } from "lucide-react";
import { Link } from "react-router-dom";

import { Card, CardContent } from "@/components/ui/card";
import { useListings } from "@/hooks/useListings";
import { COUNTRY_FLAG } from "@/lib/constants";
import { shortId } from "@/lib/utils";

/**
 * /mail — 메일 작성기는 listing 컨텍스트 (vehicle + buyer + country) 가 있어야
 * 의미 있는 프롬프트가 됨. 이 페이지는 거래 선택 가이드 + 최근 5건 빠른 점프.
 */
export function MailPage() {
  const { data: listings, isLoading } = useListings();
  const recent = listings?.slice(0, 8) ?? [];

  return (
    <div className="space-y-6">
      <header>
        <h2 className="text-2xl font-semibold tracking-tight">다국어 메일 작성</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          AI 메일 작성기는 각 거래 상세 페이지에 통합돼 있어요. 거래를 선택하면
          그 차량·바이어·도착국 컨텍스트로 Gemini 가 격식체 메일을 만들어줍니다.
        </p>
      </header>

      <Card>
        <CardContent className="flex items-center gap-4 py-5">
          <Mail className="h-10 w-10 shrink-0 text-primary" />
          <div className="flex-1">
            <p className="font-medium">거래 선택 후 → 메일 작성</p>
            <p className="text-xs text-muted-foreground">
              5 시나리오 (inquiry / quote / negotiate / shipping / dispute) ×
              6 언어 (EN / ES / AR / RU / FR / KO) 자동 — 클립보드 복사·DB 저장 포함
            </p>
          </div>
          <Link
            to="/listings"
            className="inline-flex h-9 items-center gap-2 rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground hover:bg-primary/90"
          >
            거래 목록 보기 <ArrowRight className="h-4 w-4" />
          </Link>
        </CardContent>
      </Card>

      <div>
        <h3 className="mb-3 text-sm font-semibold">최근 거래에서 바로 작성</h3>
        {isLoading && (
          <p className="text-sm text-muted-foreground">불러오는 중…</p>
        )}
        {!isLoading && recent.length === 0 && (
          <p className="rounded-md border border-dashed bg-muted/30 px-4 py-6 text-center text-xs text-muted-foreground">
            거래가 없습니다. <Link to="/vehicles" className="underline">매물</Link> →
            <Link to="/buyers" className="ml-1 underline">바이어</Link> 등록 후 거래가 자동 생성됩니다.
          </p>
        )}
        {recent.length > 0 && (
          <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
            {recent.map((l) => (
              <Link
                key={l.id}
                to={`/listings/${l.id}`}
                className="flex items-center gap-3 rounded-md border bg-card p-3 text-sm transition hover:border-primary/40 hover:shadow-sm"
              >
                <FileText className="h-4 w-4 shrink-0 text-muted-foreground" />
                <div className="min-w-0 flex-1">
                  <p className="truncate font-medium">
                    {COUNTRY_FLAG[l.destination_country ?? ""]} {l.destination_country} · {l.status}
                  </p>
                  <p className="font-mono text-[10px] text-muted-foreground">{shortId(l.id)}</p>
                </div>
                <ArrowRight className="h-3 w-3 text-muted-foreground" />
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
