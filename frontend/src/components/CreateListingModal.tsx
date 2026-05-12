import { useEffect, useMemo, useRef, useState } from "react";
import { ArrowRight, FileText, Loader2, ShieldAlert, X } from "lucide-react";
import { useNavigate } from "react-router-dom";

import { CountrySelect } from "@/components/CountrySelect";
import { useBuyers } from "@/hooks/useBuyers";
import { useCreateListing } from "@/hooks/useListings";
import { useVehicles } from "@/hooks/useVehicles";
import { Button } from "@/components/ui/button";
import { COUNTRY_FLAG, SANCTIONS_LABEL } from "@/lib/constants";
import { cn, formatApiError } from "@/lib/utils";

/**
 * Admin-side 거래 생성 모달.
 *
 * 3가지 진입 모드 (prop 으로 prefill):
 *   - 매물 상세 → "이 매물로 거래 만들기" (prefillVehicleId)
 *   - 바이어 상세 → "이 바이어와 거래 만들기" (prefillBuyerId)
 *   - Listings 빈상태 → "+ 거래 만들기" (둘 다 선택)
 *
 * 마켓플레이스의 QuoteRequestModal 과 별도 — narrative 차이 유지.
 * 성공 시 새 거래 상세 페이지로 자동 이동 (admin 워크플로우의 "다음 단계").
 */
export function CreateListingModal({
  open,
  onClose,
  prefillVehicleId,
  prefillBuyerId,
}: {
  open: boolean;
  onClose: () => void;
  prefillVehicleId?: string;
  prefillBuyerId?: string;
}) {
  const navigate = useNavigate();
  const vehiclesQ = useVehicles();
  const buyersQ = useBuyers();
  const createMutation = useCreateListing();

  const [vehicleId, setVehicleId] = useState(prefillVehicleId ?? "");
  const [buyerId, setBuyerId] = useState(prefillBuyerId ?? "");
  const [destination, setDestination] = useState("");
  const [notes, setNotes] = useState("");
  const firstFieldRef = useRef<HTMLSelectElement | HTMLInputElement | null>(null);

  // 차단 바이어는 dropdown 에서 제외 (BuyerDetail 의 disable 정책과 일치).
  // prefill 인 경우는 그대로 노출 (warning 패널이 책임짐).
  const eligibleBuyers = useMemo(() => {
    if (!buyersQ.data) return [];
    if (prefillBuyerId) return buyersQ.data;
    return buyersQ.data.filter((b) => b.sanctions_status !== "blocked");
  }, [buyersQ.data, prefillBuyerId]);

  const selectedBuyer = useMemo(
    () => buyersQ.data?.find((b) => b.id === buyerId),
    [buyersQ.data, buyerId],
  );
  const selectedVehicle = useMemo(
    () => vehiclesQ.data?.find((v) => v.id === vehicleId),
    [vehiclesQ.data, vehicleId],
  );

  // 바이어 변경 시 도착국 항상 새로 채움 (이전 바이어 국가가 stuck 되지 않게).
  // 사용자가 의도적으로 변경한 값은 그 다음 바이어 선택 전까지 유지.
  useEffect(() => {
    if (selectedBuyer) {
      setDestination(selectedBuyer.country_code);
    }
  }, [selectedBuyer]);

  // 모달 닫힐 때 폼 리셋 — open 만 deps 로 (createMutation 객체 churn 방지)
  useEffect(() => {
    if (open) return;
    setVehicleId(prefillVehicleId ?? "");
    setBuyerId(prefillBuyerId ?? "");
    setDestination("");
    setNotes("");
    createMutation.reset();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  // 모달 진입 시 첫 필드에 포커스 (a11y — 키보드 사용자)
  useEffect(() => {
    if (!open) return;
    const t = setTimeout(() => firstFieldRef.current?.focus(), 50);
    return () => clearTimeout(t);
  }, [open]);

  // 제출 중에는 닫기 차단 — 제출 도중 외부 클릭/Esc 로 모달 사라지는 혼란 방지
  const safeClose = () => {
    if (createMutation.isPending) return;
    onClose();
  };

  // Esc 닫기
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") safeClose(); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, createMutation.isPending]);

  if (!open) return null;

  // prefill 된 바이어가 차단 상태면 제출 차단 (BuyerDetail 의 disable 정책과 일치)
  const blockedPrefill = Boolean(prefillBuyerId) && selectedBuyer?.sanctions_status === "blocked";

  const canSubmit =
    Boolean(vehicleId) &&
    Boolean(buyerId) &&
    destination.trim().length === 2 &&
    !blockedPrefill &&
    !createMutation.isPending;

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!canSubmit || createMutation.isPending) return;
    createMutation.mutate(
      {
        vehicle_id: vehicleId,
        buyer_id: buyerId,
        destination_country: destination.toUpperCase(),
        notes: notes.trim() || undefined,
      },
      {
        onSuccess: (listing) => {
          onClose();
          navigate(`/listings/${listing.id}`);
        },
      },
    );
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm"
      onClick={safeClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby="cl-modal-title"
    >
      <div
        className="w-full max-w-lg rounded-lg border bg-card shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-start justify-between border-b px-6 py-4">
          <div>
            <h3 id="cl-modal-title" className="flex items-center gap-2 text-lg font-semibold">
              <FileText className="h-5 w-5 text-primary" />
              새 거래 만들기
            </h3>
            <p className="mt-0.5 text-xs text-muted-foreground">
              매물 + 바이어 + 도착국 → inquiry 상태 거래 생성 + 통관 자동 평가
            </p>
          </div>
          <button
            type="button"
            onClick={safeClose}
            disabled={createMutation.isPending}
            aria-label="닫기"
            className="rounded-md p-1.5 text-muted-foreground hover:bg-muted disabled:cursor-not-allowed disabled:opacity-50"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <form onSubmit={onSubmit} className="space-y-4 px-6 py-4">
          {/* Vehicle */}
          <div>
            <label htmlFor="cl-vehicle" className="text-sm font-medium">
              매물 <span className="text-destructive">*</span>
              {prefillVehicleId && <span className="ml-2 text-[10px] text-muted-foreground">(자동 선택됨)</span>}
            </label>
            {vehiclesQ.isLoading ? (
              <p className="mt-1 text-xs text-muted-foreground">매물 목록 로딩 중…</p>
            ) : (
              <select
                id="cl-vehicle"
                ref={!prefillVehicleId ? (firstFieldRef as React.RefObject<HTMLSelectElement>) : undefined}
                value={vehicleId}
                onChange={(e) => setVehicleId(e.target.value)}
                disabled={Boolean(prefillVehicleId)}
                className="mt-1 flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm disabled:opacity-60"
                required
              >
                <option value="">— 매물을 선택하세요 —</option>
                {vehiclesQ.data?.map((v) => (
                  <option key={v.id} value={v.id}>
                    {v.make} {v.model} {v.year ?? ""}
                    {v.list_price_usd ? ` · $${v.list_price_usd.toLocaleString()}` : ""}
                    {v.vin ? ` · VIN ${v.vin.slice(-6)}` : ""}
                  </option>
                ))}
              </select>
            )}
            {selectedVehicle && (
              <p className="mt-1 text-[10px] text-muted-foreground">
                {selectedVehicle.engine_cc}cc · {selectedVehicle.fuel_type} · {selectedVehicle.steering}
              </p>
            )}
          </div>

          {/* Buyer */}
          <div>
            <label htmlFor="cl-buyer" className="text-sm font-medium">
              바이어 <span className="text-destructive">*</span>
              {prefillBuyerId && <span className="ml-2 text-[10px] text-muted-foreground">(자동 선택됨)</span>}
            </label>
            {buyersQ.isLoading ? (
              <p className="mt-1 text-xs text-muted-foreground">바이어 목록 로딩 중…</p>
            ) : (
              <>
                <select
                  id="cl-buyer"
                  ref={prefillVehicleId && !prefillBuyerId ? (firstFieldRef as React.RefObject<HTMLSelectElement>) : undefined}
                  value={buyerId}
                  onChange={(e) => setBuyerId(e.target.value)}
                  disabled={Boolean(prefillBuyerId)}
                  className="mt-1 flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm disabled:opacity-60"
                  required
                >
                  <option value="">— 바이어를 선택하세요 —</option>
                  {eligibleBuyers.map((b) => (
                    <option key={b.id} value={b.id}>
                      {COUNTRY_FLAG[b.country_code] ?? "🌐"} {b.company_name ?? "(미상)"} — {b.country_code}
                      {b.sanctions_status !== "clean" && ` [${SANCTIONS_LABEL[b.sanctions_status]}]`}
                    </option>
                  ))}
                </select>
                {!prefillBuyerId && buyersQ.data && eligibleBuyers.length < buyersQ.data.length && (
                  <p className="mt-1 text-[10px] text-muted-foreground">
                    Blocked 바이어 {buyersQ.data.length - eligibleBuyers.length}건은 선택 목록에서 제외됨
                  </p>
                )}
              </>
            )}
            {selectedBuyer && selectedBuyer.sanctions_status !== "clean" && (
              <div className={cn(
                "mt-2 flex items-start gap-2 rounded-md p-2 text-xs",
                selectedBuyer.sanctions_status === "blocked" ? "bg-destructive/10 text-destructive" : "bg-warning/10 text-warning",
              )}>
                <ShieldAlert className="mt-0.5 h-3.5 w-3.5 shrink-0" />
                <span>
                  이 바이어는 <strong>{SANCTIONS_LABEL[selectedBuyer.sanctions_status]}</strong> 상태입니다.
                  거래는 등록되지만 통관 평가가 차단·경고로 표시됩니다.
                </span>
              </div>
            )}
          </div>

          {/* Destination */}
          <div>
            <label htmlFor="cl-dest" className="text-sm font-medium">
              도착국 <span className="text-destructive">*</span>
            </label>
            <CountrySelect
              id="cl-dest"
              value={destination}
              onChange={setDestination}
              required
            />
            <p className="mt-1 text-[10px] text-muted-foreground">
              바이어 선택 시 자동입력 — 자동차단 5국 (ZA·MM·TH·MY·SD) 은 비활성
            </p>
          </div>

          {/* Notes */}
          <div>
            <label htmlFor="cl-notes" className="text-sm font-medium">메모 (선택)</label>
            <textarea
              id="cl-notes"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="예: 연락 채널은 WhatsApp, CIF 견적 우선"
              rows={3}
              className="mt-1 flex w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm"
            />
          </div>

          {createMutation.isError && (
            <div role="alert" aria-live="polite" className="rounded-md border border-destructive/30 bg-destructive/5 p-3 text-sm text-destructive">
              생성 실패: {formatApiError(createMutation.error)}
            </div>
          )}

          <div className="flex items-center justify-end gap-2 border-t pt-4">
            <Button
              type="button"
              variant="outline"
              onClick={safeClose}
              disabled={createMutation.isPending}
            >
              취소
            </Button>
            <Button type="submit" disabled={!canSubmit} className="gap-2">
              {createMutation.isPending ? (
                <><Loader2 className="h-4 w-4 animate-spin" /> 생성 중...</>
              ) : (
                <>거래 생성하고 상세로 이동 <ArrowRight className="h-4 w-4" /></>
              )}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
