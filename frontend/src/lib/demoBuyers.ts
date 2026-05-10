/**
 * Demo 바이어 프리셋 — compliance 결과를 의도적으로 다르게 만든 5개 + 랜덤.
 * Vehicle 프리셋과 같은 패턴 (lib/demoVehicles.ts).
 *
 * 사용처: /buyers/new 의 "데모 데이터 채우기" 드롭다운.
 */

export interface BuyerFormPreset {
  label: string;
  hint: string; // 결과 미리 알려주는 힌트
  data: BuyerFormData;
}

export interface BuyerFormData {
  company_name: string;
  contact_person: string;
  country_code: string;
  city: string;
  address: string;
  phone: string;
  whatsapp: string;
  email: string;
  tax_id: string;
  preferred_language: string;
  preferred_currency: string;
  preferred_payment: string;
  preferred_port: string;
  preferred_incoterm: string;
}

export const EMPTY_BUYER_FORM: BuyerFormData = {
  company_name: "",
  contact_person: "",
  country_code: "",
  city: "",
  address: "",
  phone: "",
  whatsapp: "",
  email: "",
  tax_id: "",
  preferred_language: "",
  preferred_currency: "USD",
  preferred_payment: "T/T",
  preferred_port: "",
  preferred_incoterm: "CIF",
};

export const DEMO_BUYER_PRESETS: BuyerFormPreset[] = [
  {
    label: "Rodriguez Motors (DO, 정상)",
    hint: "도미니카공화국 · clean · 거래 가능",
    data: {
      ...EMPTY_BUYER_FORM,
      company_name: "Rodriguez Motors Demo S.R.L.",
      contact_person: "Sr. Carlos Rodríguez",
      country_code: "DO",
      city: "Santo Domingo",
      address: "Av. Winston Churchill 123, Santo Domingo, DN 10148",
      phone: "+1-809-555-0123",
      whatsapp: "+1-809-555-0123",
      email: "carlos@rodriguez-demo.do",
      tax_id: "DO-DEMO-001",
      preferred_language: "es",
      preferred_payment: "T/T",
      preferred_port: "Rio Haina",
    },
  },
  {
    label: "Sahara Auto Trading (LY, 정상)",
    hint: "리비아 · clean · ACI 사전등록 필요",
    data: {
      ...EMPTY_BUYER_FORM,
      company_name: "Sahara Auto Demo Ltd",
      contact_person: "Mr. Ahmed Al-Mansouri",
      country_code: "LY",
      city: "Misrata",
      address: "Tripoli Street, Misrata Free Zone",
      phone: "+218-91-555-0001",
      whatsapp: "+218-91-555-0001",
      email: "ahmed@sahara-demo.ly",
      tax_id: "LY-DEMO-002",
      preferred_language: "ar",
      preferred_payment: "T/T",
      preferred_port: "Misrata",
    },
  },
  {
    label: "ABC Auto LLC (KG, ⚠️ 경고)",
    hint: "키르기스스탄 · russia_proxy_country 경고 — 신규 바이어",
    data: {
      ...EMPTY_BUYER_FORM,
      company_name: "ABC Auto Demo LLC",
      contact_person: "Aibek Tashov",
      country_code: "KG",
      city: "Bishkek",
      address: "Chui Avenue 100, Bishkek 720040",
      phone: "+996-555-000-001",
      whatsapp: "+996-555-000-001",
      email: "aibek@abc-demo.kg",
      tax_id: "KG-DEMO-003",
      preferred_language: "ru",
      preferred_payment: "T/T",
      preferred_port: "Bandar Abbas (transit)",
    },
  },
  {
    label: "Damascus Trading (SY, ⚠️ 경고)",
    hint: "시리아 · 제재 적용국 + OFAC 사전 조회 필요",
    data: {
      ...EMPTY_BUYER_FORM,
      company_name: "Damascus Auto Demo",
      contact_person: "Mr. Karim Hadi",
      country_code: "SY",
      city: "Damascus",
      address: "Mezzeh Highway, Damascus",
      phone: "+963-11-555-0001",
      email: "karim@damascus-demo.sy",
      tax_id: "SY-DEMO-004",
      preferred_language: "ar",
      preferred_port: "Latakia",
    },
  },
  {
    label: "Vladivostok Trading (RU, 🚫 차단)",
    hint: "러시아 직수출 — direct_export_blocked 자동 차단",
    data: {
      ...EMPTY_BUYER_FORM,
      company_name: "Vladivostok Trading Demo",
      contact_person: "Ivan Petrov",
      country_code: "RU",
      city: "Vladivostok",
      address: "Svetlanskaya St., Vladivostok",
      phone: "+7-423-555-0001",
      email: "ivan@vlad-demo.ru",
      tax_id: "RU-DEMO-005",
      preferred_language: "ru",
      preferred_payment: "T/T",
    },
  },
];

// ── 랜덤 바이어 생성기 ─────────────────────────────────────
// import_rules 시드된 5개국으로 제한 — 미시드 국가는 거래 생성 시 404 유발.
// (Phase 2 에서 시드 확장하면 풀도 자연스럽게 늘어남)
const RANDOM_POOL = {
  countries: [
    { code: "DO", names: ["Garcia Auto", "Hernandez Motors", "Lopez Trading"] },
    { code: "KE", names: ["Nairobi Auto", "Mombasa Motors", "Kamau Trading"] },
    { code: "LY", names: ["Tripoli Auto", "Benghazi Trading", "Sahara Motors"] },
    { code: "KG", names: ["Bishkek Auto", "Osh Trading", "Tian Shan Motors"] },
    { code: "SY", names: ["Aleppo Trading", "Latakia Motors", "Homs Auto"] },
  ] as const,
  contactFirstNames: ["Carlos", "Ahmed", "James", "Mohammed", "Daniel", "Khalid", "Adebayo"],
  contactLastNames: ["Rodriguez", "Hassan", "Smith", "Al-Mansouri", "Kamau", "Okonkwo"],
};

function pick<T>(arr: readonly T[]): T {
  return arr[Math.floor(Math.random() * arr.length)]!;
}

export function generateRandomBuyer(): BuyerFormData {
  const country = pick(RANDOM_POOL.countries);
  const companyName = `${pick(country.names)} ${["LLC", "Ltd", "Co.", "S.R.L.", "FZE"][Math.floor(Math.random() * 5)]}`;
  const contact = `Mr. ${pick(RANDOM_POOL.contactFirstNames)} ${pick(RANDOM_POOL.contactLastNames)}`;
  const taxId = `${country.code}-${Math.floor(Math.random() * 900000) + 100000}`;
  const portMap: Record<string, string> = {
    DO: "Rio Haina",
    KE: "Mombasa",
    LY: "Misrata",
    AE: "Jebel Ali",
    JO: "Aqaba",
    NG: "Lagos (Apapa)",
  };
  const langMap: Record<string, string> = {
    DO: "es",
    KE: "en",
    LY: "ar",
    AE: "en",
    JO: "ar",
    NG: "en",
  };

  return {
    ...EMPTY_BUYER_FORM,
    company_name: companyName,
    contact_person: contact,
    country_code: country.code,
    city: portMap[country.code] ?? "",
    tax_id: taxId,
    preferred_language: langMap[country.code] ?? "en",
    preferred_payment: "T/T",
    preferred_port: portMap[country.code] ?? "",
    email: `${contact.toLowerCase().replace(/[^a-z]/g, "")}@${country.code.toLowerCase()}-demo.com`,
  };
}
