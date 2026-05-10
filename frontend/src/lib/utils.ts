import { type ClassValue, clsx } from "clsx";
import { AxiosError } from "axios";
import { twMerge } from "tailwind-merge";

/** Tailwind 클래스 머지 (조건부 + 충돌 해결). shadcn/ui 표준 헬퍼. */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/** UUID 짧게 표시 (UI 카드용). */
export function shortId(id: string | null | undefined, len = 8): string {
  if (!id) return "—";
  return id.slice(0, len);
}

/** 통화 포맷 (USD 기본). */
export function formatPrice(value: number | null | undefined, currency = "USD"): string {
  if (value === null || value === undefined) return "—";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    maximumFractionDigits: 0,
  }).format(value);
}

/**
 * API 에러를 사람이 읽을 수 있는 메시지로 변환.
 * FastAPI 422 의 detail 은 배열 ([{loc, msg, type}, ...]) 이라 그대로 렌더하면
 * "[object Object]" 가 나옴 — 이 헬퍼가 모든 형태를 안전하게 처리.
 */
export function formatApiError(err: unknown): string {
  if (err instanceof AxiosError) {
    const detail = err.response?.data?.detail;
    if (Array.isArray(detail)) {
      return detail
        .map((d) => {
          if (typeof d === "string") return d;
          if (d?.msg) {
            const loc = Array.isArray(d.loc) ? d.loc.slice(-1)[0] : null;
            return loc ? `${loc}: ${d.msg}` : d.msg;
          }
          return JSON.stringify(d);
        })
        .join("; ");
    }
    if (typeof detail === "string") return detail;
    return err.message;
  }
  if (err instanceof Error) return err.message;
  return String(err);
}
