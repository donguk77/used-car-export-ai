import { useEffect } from "react";
import { ArrowRight, Info, X } from "lucide-react";
import { Link } from "react-router-dom";

/**
 * Single-user PoC 모드 알림 모달.
 * Sign In / My Order / Search 등 인증·계정 의존 버튼 클릭 시 표시.
 * Capstone 스코프상 풀 인증은 미구현 — 멘토에게 맥락 제공용.
 */
export function DemoModeModal({
  open,
  feature,
  onClose,
}: {
  open: boolean;
  feature: string; // e.g. "Sign In", "My Order"
  onClose: () => void;
}) {
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4 backdrop-blur-[2px]"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby="demo-modal-title"
    >
      <div
        className="w-full max-w-md rounded-lg border border-slate-200 bg-white shadow-[0_20px_60px_-15px_rgba(15,23,42,0.5)]"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between border-b px-6 py-4">
          <div className="flex items-center gap-2">
            <span className="rounded-md bg-amber-100 px-2 py-0.5 text-[10px] font-bold uppercase tracking-widest text-amber-800">
              Demo Mode
            </span>
            <h3 id="demo-modal-title" className="text-base font-semibold">
              {feature}
            </h3>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="닫기"
            className="rounded-md p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="space-y-3 px-6 py-5">
          <div className="flex items-start gap-3 rounded-md bg-slate-50 p-3 text-sm text-slate-700">
            <Info className="mt-0.5 h-4 w-4 shrink-0 text-slate-500" />
            <div>
              <p className="font-medium">단일 사용자 PoC 모드</p>
              <p className="mt-1 text-xs leading-relaxed text-slate-600">
                이 화면은 벤치마크 비교용 마켓플레이스 UI 입니다. Capstone 스코프상
                회원가입 / 로그인 / 주문 관리 같은 인증 기능은 구현되지 않았으며,
                모든 작업은 admin SaaS 에서 단일 사용자로 진행됩니다.
              </p>
            </div>
          </div>

          <div className="rounded-md border border-slate-200 p-3 text-xs text-slate-600">
            <p className="mb-2 font-semibold">대신 이렇게 시연합니다:</p>
            <ul className="ml-4 list-disc space-y-1">
              <li>차량 상세 → <strong>"Request Quote"</strong> 클릭 → 견적 요청 모달</li>
              <li>요청은 admin SaaS 에 inquiry 거래로 자동 등록</li>
              <li>관리자가 즉시 다국어 메일 / 4종 PDF 발송</li>
            </ul>
          </div>
        </div>

        <div className="flex items-center justify-between gap-2 border-t px-6 py-3">
          <button
            type="button"
            onClick={onClose}
            className="rounded-md px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100"
          >
            마켓플레이스 계속 보기
          </button>
          <Link
            to="/"
            className="inline-flex items-center gap-2 rounded-md bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800"
          >
            Admin SaaS 로 이동 <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </div>
    </div>
  );
}
