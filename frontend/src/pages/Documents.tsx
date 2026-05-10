import { ArrowRight, FileText, Package } from "lucide-react";
import { Link } from "react-router-dom";

import { Card, CardContent } from "@/components/ui/card";
import { useListings } from "@/hooks/useListings";
import { COUNTRY_FLAG } from "@/lib/constants";
import { shortId } from "@/lib/utils";

/**
 * /documents — PDF 4종 자동 생성도 listing 컨텍스트가 필요. 거래 선택 가이드.
 */
export function DocumentsPage() {
  const { data: listings, isLoading } = useListings();
  const recent = listings?.slice(0, 8) ?? [];

  return (
    <div className="space-y-6">
      <header>
        <h2 className="text-2xl font-semibold tracking-tight">수출 서류 자동 생성</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          서류 생성기는 각 거래 상세 페이지에 통합돼 있어요. Playwright 헤드리스 Chromium 으로
          Invoice / Packing List / Shipping Instruction / C/O Application — 4종 PDF 동시 생성.
        </p>
      </header>

      <Card>
        <CardContent className="flex items-center gap-4 py-5">
          <Package className="h-10 w-10 shrink-0 text-primary" />
          <div className="flex-1">
            <p className="font-medium">거래 선택 후 → 4종 PDF 동시 생성 (~10초)</p>
            <p className="text-xs text-muted-foreground">
              차량·바이어 데이터 자동 매핑 · 한글/아랍어 폰트 임베딩 · 다운로드 즉시 가능
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
        <h3 className="mb-3 text-sm font-semibold">최근 거래에서 바로 생성</h3>
        {isLoading && (
          <p className="text-sm text-muted-foreground">불러오는 중…</p>
        )}
        {!isLoading && recent.length === 0 && (
          <p className="rounded-md border border-dashed bg-muted/30 px-4 py-6 text-center text-xs text-muted-foreground">
            거래가 없습니다.
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
