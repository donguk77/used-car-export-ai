/** UI 표시용 한국어 라벨 매핑. 백엔드 enum 값 → 한국어. */

import type { ListingStatus, SanctionsStatus } from "@/types/api";

export const VEHICLE_STATUS_LABEL: Record<string, string> = {
  available: "판매 가능",
  reserved: "예약됨",
  sold: "판매 완료",
  shipping: "선적 중",
  in_transit: "운송 중",
  delivered: "배송 완료",
};

export const VEHICLE_STATUS_VARIANT: Record<string, "secondary" | "success" | "warning" | "outline"> = {
  available: "success",
  reserved: "warning",
  sold: "secondary",
  shipping: "secondary",
  in_transit: "secondary",
  delivered: "outline",
};

export const LISTING_STATUS_LABEL: Record<ListingStatus, string> = {
  inquiry: "문의",
  quoted: "견적",
  negotiating: "협상",
  agreed: "합의",
  documenting: "서류작성",
  shipping: "선적",
  in_transit: "운송",
  arrived: "도착",
  cleared: "통관",
  delivered: "인도완료",
  disputed: "분쟁",
  closed: "종료",
};

export const SANCTIONS_LABEL: Record<SanctionsStatus, string> = {
  clean: "정상",
  warning: "주의",
  blocked: "차단",
  unchecked: "미검사",
};

export const SANCTIONS_VARIANT: Record<SanctionsStatus, "success" | "warning" | "destructive" | "outline"> = {
  clean: "success",
  warning: "warning",
  blocked: "destructive",
  unchecked: "outline",
};

export const FUEL_LABEL: Record<string, string> = {
  Gasoline: "가솔린",
  Diesel: "디젤",
  EV: "전기",
  Hybrid: "하이브리드",
  HEV: "하이브리드",
  PHEV: "플러그인 하이브리드",
  LPG: "LPG",
  CNG: "CNG",
};

/**
 * 백엔드 backend/app/core/compliance.py 와 동기화 유지.
 * - DIRECT_BLOCKED_COUNTRIES: 직접 수출 차단 (대외무역법/제재)
 * - RUSSIA_PROXY_COUNTRIES: EAEU/CIS — 우회수출 위험 카테고리
 */
export const DIRECT_BLOCKED_COUNTRIES: ReadonlySet<string> = new Set([
  "RU", "BY", "KP", "IR",
]);

export const RUSSIA_PROXY_COUNTRIES: ReadonlySet<string> = new Set([
  "KG", "KZ", "TJ", "AM", "UZ",
]);

export const COUNTRY_FLAG: Record<string, string> = {
  DO: "🇩🇴",
  KE: "🇰🇪",
  KG: "🇰🇬",
  LY: "🇱🇾",
  SY: "🇸🇾",
  RU: "🇷🇺",
  KR: "🇰🇷",
  US: "🇺🇸",
  JP: "🇯🇵",
};
