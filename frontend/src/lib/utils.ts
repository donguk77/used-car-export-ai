import { type ClassValue, clsx } from "clsx";
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
