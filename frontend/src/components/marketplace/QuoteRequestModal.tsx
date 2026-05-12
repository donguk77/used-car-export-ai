import { useEffect, useMemo, useState } from "react";
import { ArrowRight, CheckCircle2, Loader2, ShieldAlert, X } from "lucide-react";
import { Link } from "react-router-dom";

import { CountrySelect } from "@/components/CountrySelect";
import { useBuyers } from "@/hooks/useBuyers";
import { useCreateListing } from "@/hooks/useListings";
import { COUNTRY_FLAG, SANCTIONS_LABEL } from "@/lib/constants";
import { cn, formatApiError } from "@/lib/utils";
import type { Vehicle } from "@/types/api";

/**
 * Marketplace 의 'Request Quote' 클릭 시 열리는 모달.
 * 바이어 + 도착국 + 비고 → POST /api/listings (status=inquiry).
 * 성공 시 admin SaaS 의 거래 상세 (메일·서류 작성 가능) 로 점프.
 *
 * 데모 narrative: "외부 마켓플레이스에서 견적 요청이 들어오면
 * 우리 admin SaaS 에 자동으로 inquiry 상태 거래로 등록됩니다."
 */
export function QuoteRequestModal({
  vehicle,
  open,
  onClose,
}: {
  vehicle: Vehicle;
  open: boolean;
  onClose: () => void;
}) {
  const buyersQ = useBuyers();
  const createMutation = useCreateListing();

  const [buyerId, setBuyerId] = useState<string>("");
  const [destination, setDestination] = useState<string>("");
  const [notes, setNotes] = useState("");

  // 차단 바이어는 dropdown 에서 제외 (admin CreateListingModal 정책과 일관성)
  const eligibleBuyers = useMemo(
    () => (buyersQ.data ?? []).filter((b) => b.sanctions_status !== "blocked"),
    [buyersQ.data],
  );

  const selectedBuyer = useMemo(
    () => buyersQ.data?.find((b) => b.id === buyerId),
    [buyersQ.data, buyerId],
  );

  // 바이어 변경 시 도착국 항상 새로 채움 (이전 국가 stuck 방지)
  useEffect(() => {
    if (selectedBuyer) {
      setDestination(selectedBuyer.country_code);
    }
  }, [selectedBuyer]);

  // 모달 닫힐 때 폼 리셋 — open 만 deps (createMutation churn 방지)
  useEffect(() => {
    if (open) return;
    setBuyerId("");
    setDestination("");
    setNotes("");
    createMutation.reset();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  // 제출 중 close 차단
  const safeClose = () => {
    if (createMutation.isPending) return;
    onClose();
  };

  // Esc 키로 닫기
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") safeClose(); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, createMutation.isPending]);

  if (!open) return null;

  const success = createMutation.isSuccess && createMutation.data;
  const canSubmit =
    Boolean(buyerId) &&
    destination.trim().length === 2 &&
    !createMutation.isPending;

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!canSubmit) return;
    createMutation.mutate({
      vehicle_id: vehicle.id,
      buyer_id: buyerId,
      destination_country: destination.toUpperCase(),
      notes: notes.trim() || undefined,
    });
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm"
      onClick={safeClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby="quote-modal-title"
    >
      <div
        className="w-full max-w-lg rounded-lg bg-white shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-start justify-between border-b px-6 py-4">
          <div>
            <h3 id="quote-modal-title" className="text-lg font-semibold">
              {success ? "✓ 견적 요청 접수됨" : "견적 요청 (Request Quote)"}
            </h3>
            <p className="mt-0.5 text-xs text-slate-500">
              {vehicle.make} {vehicle.model} {vehicle.year}
              {vehicle.list_price_usd ? ` · FOB $${vehicle.list_price_usd.toLocaleString()}` : ""}
            </p>
          </div>
          <button
            type="button"
            onClick={safeClose}
            disabled={createMutation.isPending}
            aria-label="닫기"
            className="rounded-md p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-600 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Body — Form 또는 Success */}
        {success ? (
          <SuccessPanel listingId={createMutation.data.id} onClose={onClose} />
        ) : (
          <form onSubmit={onSubmit} className="space-y-4 px-6 py-4">
            <div>
              <label htmlFor="qm-buyer" className="text-sm font-medium">
                바이어 선택 <span className="text-red-500">*</span>
              </label>
              {buyersQ.isLoading ? (
                <p className="mt-1 text-xs text-slate-500">바이어 목록 로딩 중…</p>
              ) : (
                <select
                  id="qm-buyer"
                  value={buyerId}
                  onChange={(e) => setBuyerId(e.target.value)}
                  className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-slate-900 focus:outline-none"
                  required
                >
                  <option value="">— 바이어를 선택하세요 —</option>
                  {eligibleBuyers.map((b) => (
                    <option key={b.id} value={b.id}>
                      {COUNTRY_FLAG[b.country_code] ?? "🌐"} {b.company_name ?? "(미상)"}
                      {" "}— {b.country_code}
                      {b.sanctions_status !== "clean" && ` [${SANCTIONS_LABEL[b.sanctions_status]}]`}
                    </option>
                  ))}
                </select>
              )}
              {selectedBuyer && selectedBuyer.sanctions_status !== "clean" && (
                <div className={cn(
                  "mt-2 flex items-start gap-2 rounded-md p-2 text-xs",
                  selectedBuyer.sanctions_status === "blocked"
                    ? "bg-red-50 text-red-800"
                    : "bg-amber-50 text-amber-800",
                )}>
                  <ShieldAlert className="mt-0.5 h-3.5 w-3.5 shrink-0" />
                  <span>
                    이 바이어는 <strong>{SANCTIONS_LABEL[selectedBuyer.sanctions_status]}</strong> 상태입니다.
                    거래는 등록되지만 통관 평가에서 차단·경고로 표시됩니다.
                  </span>
                </div>
              )}
            </div>

            <div>
              <label htmlFor="qm-dest" className="text-sm font-medium">
                도착국 <span className="text-red-500">*</span>
              </label>
              <CountrySelect
                id="qm-dest"
                value={destination}
                onChange={setDestination}
                required
              />
              <p className="mt-1 text-[10px] text-slate-500">
                바이어 선택 시 자동입력 — 자동차단 5국 (ZA·MM·TH·MY·SD) 은 비활성
              </p>
            </div>

            <div>
              <label htmlFor="qm-notes" className="text-sm font-medium">
                요청 사항 (선택)
              </label>
              <textarea
                id="qm-notes"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="예: CIF Santo Domingo 견적 + 2주 내 선적 가능 여부"
                rows={3}
                className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-slate-900 focus:outline-none"
              />
            </div>

            {createMutation.isError && (
              <div role="alert" aria-live="polite" className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-800">
                요청 실패: {formatApiError(createMutation.error)}
              </div>
            )}

            <div className="flex items-center justify-end gap-2 border-t pt-4">
              <button
                type="button"
                onClick={safeClose}
                disabled={createMutation.isPending}
                className="rounded-md px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-50"
              >
                취소
              </button>
              <button
                type="submit"
                disabled={!canSubmit}
                className="inline-flex items-center gap-2 rounded-md bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {createMutation.isPending ? (
                  <><Loader2 className="h-4 w-4 animate-spin" /> 등록 중...</>
                ) : (
                  <>견적 요청 보내기 <ArrowRight className="h-4 w-4" /></>
                )}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}

function SuccessPanel({ listingId, onClose }: { listingId: string; onClose: () => void }) {
  return (
    <div className="space-y-4 px-6 py-6">
      <div className="flex items-start gap-3 rounded-md bg-emerald-50 p-4 text-sm text-emerald-900">
        <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-emerald-600" />
        <div>
          <p className="font-semibold">견적 요청이 접수되었습니다.</p>
          <p className="mt-1 text-xs text-emerald-800">
            매니저가 24시간 내 다국어 견적 메일과 수출 서류를 발송합니다.
          </p>
        </div>
      </div>

      <div className="rounded-md border border-slate-200 bg-slate-50 p-3 text-xs text-slate-600">
        <p className="mb-1 font-semibold uppercase tracking-widest text-slate-500">
          데모 안내 — admin UI 연결
        </p>
        <p>
          이 견적은 우리 admin SaaS 에 <strong>inquiry</strong> 상태의 거래로 자동 등록됐습니다.
          관리자는 즉시 다국어 메일 작성 / 4종 PDF 생성을 진행할 수 있습니다.
        </p>
      </div>

      <div className="flex items-center justify-between gap-2 border-t pt-4">
        <button
          type="button"
          onClick={onClose}
          className="rounded-md px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100"
        >
          마켓플레이스 계속 둘러보기
        </button>
        <Link
          to={`/listings/${listingId}`}
          className="inline-flex items-center gap-2 rounded-md bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800"
        >
          Admin UI 에서 보기 <ArrowRight className="h-4 w-4" />
        </Link>
      </div>
    </div>
  );
}
