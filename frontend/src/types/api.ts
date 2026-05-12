/**
 * 백엔드 API 응답 타입 — `backend/app/api/*.py` 의 Pydantic 스키마와 1:1 일치 유지.
 * 변경 시 양쪽 같이 수정. (Phase 2: openapi-typescript 로 자동 생성 검토)
 */

// ── Common ─────────────────────────────────────────────────
export type UUID = string;
export type ISODate = string; // "2026-05-09"
export type ISODateTime = string; // "2026-05-09T12:34:56Z"

// ── Dashboard (GET /api/dashboard/summary) ─────────────────
export interface DashboardCounts {
  vehicles_total: number;
  vehicles_available: number;
  buyers_total: number;
  buyers_blocked: number;
  buyers_warning: number;
  listings_inquiry: number;
  listings_in_progress: number;
  listings_shipping: number;
  listings_delivered: number;
}

export interface RecentListing {
  id: UUID;
  vehicle_label: string;
  buyer_name: string | null;
  destination_country: string | null;
  status: ListingStatus;
  can_import: boolean | null;
}

export interface ComplianceAlert {
  buyer_id: UUID;
  company_name: string | null;
  country_code: string;
  sanctions_status: SanctionsStatus;
  russia_proxy_risk_score: number | null;
}

export interface DashboardSummary {
  counts: DashboardCounts;
  recent_listings: RecentListing[];
  compliance_alerts: ComplianceAlert[];
}

// ── Country (GET /api/countries) ───────────────────────────
export interface Country {
  code: string;
  name_en: string;
  name_ko: string | null;
  region: string | null;
  primary_language: string | null;
  business_language: string | null;
  steering: "LHD" | "RHD" | "MIXED" | null;
  is_high_risk: boolean;
  is_russia_proxy_risk: boolean;
  is_sanctioned: boolean;
  pre_registration_system: string | null;
  consular_legalization: boolean;
}

// ── Vehicle (GET/POST /api/vehicles) ───────────────────────
export interface Vehicle {
  id: UUID;
  vin: string | null;
  make: string | null;
  model: string | null;
  year: number | null;
  body_type: string | null;
  fuel_type: string | null;
  engine_cc: number | null;
  transmission: string | null;
  drivetrain: string | null;
  steering: "LHD" | "RHD" | null;
  seats: number | null;  // 좌석수 (#033 — HS 8702 vs 8703 분기)
  gross_vehicle_weight_kg: number | null;  // GVW (#033 — HS 8704 세분)
  mileage_km: number | null;
  color_exterior: string | null;
  list_price_usd: number | null;
  hs_code: string | null;
  port_of_loading: string | null;
  status: string;
  registration_date: ISODate | null;
  manufacture_date: ISODate | null;
  image_url: string | null; // AI 생성 (Imagen) — /vehicle-images/{id}.png
}

export interface DecodedVin {
  vin: string;
  make: string | null;
  model: string | null;
  year: number | null;
  body_type: string | null;
  fuel_type: string | null;
  engine_cc: number | null;
  transmission: string | null;
  drivetrain: string | null;
  raw: Record<string, unknown> | null;
}

// ── Buyer (GET/POST /api/buyers) ───────────────────────────
export type SanctionsStatus = "clean" | "warning" | "blocked" | "unchecked";

export interface Buyer {
  id: UUID;
  buyer_type: string | null;
  company_name: string | null;
  contact_person: string | null;
  country_code: string;
  city: string | null;
  address: string | null;
  phone: string | null;
  whatsapp: string | null;
  email: string | null;
  business_license: string | null;
  tax_id: string | null;
  preferred_language: string | null;
  preferred_currency: string | null;
  preferred_payment: string | null;
  preferred_port: string | null;
  preferred_incoterm: string | null;
  sanctions_status: SanctionsStatus;
  russia_proxy_risk_score: number | null;
  total_orders: number;
}

export interface ComplianceFinding {
  severity: "clean" | "warning" | "blocked";
  code: string;
  message: string;
}

export interface ComplianceReport {
  overall: "clean" | "warning" | "blocked";
  score: number;
  findings: ComplianceFinding[];
}

export interface BuyerCreateResponse {
  buyer: Buyer;
  compliance: ComplianceReport;
}

// ── Listing (GET/POST /api/listings) ───────────────────────
export type ListingStatus =
  | "inquiry"
  | "quoted"
  | "negotiating"
  | "agreed"
  | "documenting"
  | "shipping"
  | "in_transit"
  | "arrived"
  | "cleared"
  | "delivered"
  | "disputed"
  | "closed";

export interface Listing {
  id: UUID;
  vehicle_id: UUID;
  buyer_id: UUID | null;
  destination_country: string | null;
  can_import: boolean | null;
  import_check_json: Record<string, unknown>;
  agreed_price_usd: number | null;
  incoterm: string | null;
  port_of_loading: string | null;
  port_of_discharge: string | null;
  payment_terms: string | null;
  shipping_method: string | null;
  status: ListingStatus;
  notes: string | null;
}

// ── Documents (POST/GET /api/listings/{id}/documents) ──────
export type ExportDocType = "invoice" | "packing_list" | "shipping_instruction" | "co_application";

export interface ExportDocument {
  id: UUID;
  doc_type: ExportDocType;
  pdf_url: string | null;
  version: number;
}

// ── Mail draft (POST /api/listings/{id}/mail-draft) ────────
export type MailScenario = "inquiry" | "quote" | "negotiate" | "shipping" | "dispute";
export type MailLanguage = "en" | "es" | "ar" | "ru" | "fr" | "ko";

export interface MailDraftResponse {
  subject: string;
  body: string;
  scenario: MailScenario;
  language: string;
  provider: string;
  model: string;
  message_id: UUID;
  translation_ko: string | null;
}

// ── Import-check (POST /api/listings/import-check) ─────────
export interface ImportCheckResult {
  can_import: boolean;
  reasons: string[];
  warnings: string[];
  required_documents: string[];
  matched_rule_id: UUID | null;
}

export interface ImportCheckResponse {
  can_import: boolean;
  rule_check: ImportCheckResult;
  compliance: ComplianceReport | null;
}
