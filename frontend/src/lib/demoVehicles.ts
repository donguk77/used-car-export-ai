/**
 * Demo 매물 프리셋 — 시연 시나리오와 매핑된 5개 + 랜덤 생성기.
 *
 * 사용처: /vehicles/new 폼의 "데모 데이터 채우기" 드롭다운.
 * 각 프리셋은 룰엔진의 5개국 통관 결과를 의도적으로 다르게 만든다 —
 * 멘토·평가위원이 "왜 이 차는 케냐 안 됨?" 같은 질문에 즉시 답할 수 있게.
 */

export interface VehicleFormPreset {
  label: string;
  hint: string; // 한 줄 설명 (드롭다운에 표시)
  data: VehicleFormData;
}

export interface VehicleFormData {
  vin: string;
  make: string;
  model: string;
  year: number;
  body_type: string;
  fuel_type: string;
  engine_cc: number;
  transmission: string;
  steering: "LHD" | "RHD";
  mileage_km: number;
  color_exterior: string;
  list_price_usd: number;
  hs_code: string;
  manufacture_date: string; // YYYY-MM-DD
  registration_date: string;
}

export const DEMO_PRESETS: VehicleFormPreset[] = [
  {
    label: "Hyundai Sonata 2020 (LHD, 2.0L)",
    hint: "도미니카·리비아 OK / 케냐 X (RHD 아님)",
    data: {
      vin: "KMHE41LBXLA000901",
      make: "Hyundai",
      model: "Sonata",
      year: 2020,
      body_type: "passenger",
      fuel_type: "Gasoline",
      engine_cc: 2000,
      transmission: "A/T",
      steering: "LHD",
      mileage_km: 58000,
      color_exterior: "Pearl White",
      list_price_usd: 14000,
      hs_code: "8703.23",
      manufacture_date: "2020-04-01",
      registration_date: "2020-05-15",
    },
  },
  {
    label: "Genesis G80 2022 (LHD, 3.3L)",
    hint: "키르기스스탄 X (2000cc 초과 + $50k 초과 = 러시아 우회)",
    data: {
      vin: "KMHHU81KMNA000902",
      make: "Genesis",
      model: "G80",
      year: 2022,
      body_type: "passenger",
      fuel_type: "Gasoline",
      engine_cc: 3342,
      transmission: "A/T",
      steering: "LHD",
      mileage_km: 42000,
      color_exterior: "Midnight Blue",
      list_price_usd: 55000,
      hs_code: "8703.24",
      manufacture_date: "2022-01-15",
      registration_date: "2022-02-10",
    },
  },
  {
    label: "Hyundai Tucson 2017 (RHD, 2.0L Diesel)",
    hint: "케냐 룰엔진 검증 — 2026.1.1 발효 시점 차단 시연",
    data: {
      vin: "KMHJ381BFHU000903",
      make: "Hyundai",
      model: "Tucson",
      year: 2017,
      body_type: "passenger",
      fuel_type: "Diesel",
      engine_cc: 2000,
      transmission: "A/T",
      steering: "RHD",
      mileage_km: 98000,
      color_exterior: "Gray",
      list_price_usd: 11500,
      hs_code: "8703.32",
      manufacture_date: "2017-03-01",
      registration_date: "2017-05-01",
    },
  },
  {
    label: "Kia Bongo 2020 (1톤 트럭, Diesel)",
    hint: "시리아 OFAC 경고 + 신흥국 SUV·1톤 수요 시연",
    data: {
      vin: "KMFGA17EPJA000904",
      make: "Kia",
      model: "Bongo",
      year: 2020,
      body_type: "truck",
      fuel_type: "Diesel",
      engine_cc: 2497,
      transmission: "M/T",
      steering: "LHD",
      mileage_km: 95000,
      color_exterior: "White",
      list_price_usd: 18500,
      hs_code: "8704.21",
      manufacture_date: "2020-08-01",
      registration_date: "2020-09-12",
    },
  },
  {
    label: "Hyundai Avante 2019 (LHD, 1.6L)",
    hint: "표준 sedan — 모든 PoC 5개국 통관 OK",
    data: {
      vin: "KMHD84LF2KU000905",
      make: "Hyundai",
      model: "Avante",
      year: 2019,
      body_type: "passenger",
      fuel_type: "Gasoline",
      engine_cc: 1591,
      transmission: "A/T",
      steering: "LHD",
      mileage_km: 65000,
      color_exterior: "White",
      list_price_usd: 11000,
      hs_code: "8703.22",
      manufacture_date: "2019-05-01",
      registration_date: "2019-06-20",
    },
  },
];

// ── 랜덤 생성기 (Faker 같은 외부 라이브러리 없이 PoC 자체 구현) ──
const RANDOM_POOL = {
  make: ["Hyundai", "Kia", "Genesis", "KGM", "Renault Korea"],
  modelByMake: {
    Hyundai: ["Sonata", "Avante", "Tucson", "Santa Fe", "Palisade", "Kona", "Grand Starex"],
    Kia: ["K5", "K3", "K7", "Sorento", "Sportage", "Carnival", "Bongo", "Mohave"],
    Genesis: ["G70", "G80", "G90", "GV70", "GV80"],
    KGM: ["Tivoli", "Korando", "Rexton", "Torres"],
    "Renault Korea": ["SM6", "QM6", "XM3"],
  } as Record<string, string[]>,
  body_type: ["passenger", "truck", "van"] as const,
  fuel_type: ["Gasoline", "Diesel", "Hybrid", "EV", "LPG"] as const,
  transmission: ["A/T", "M/T", "CVT"] as const,
  steering: ["LHD", "RHD"] as const,
  color_exterior: ["White", "Black", "Silver", "Gray", "Pearl White", "Midnight Blue", "Red"],
};

const VIN_CHARS = "ABCDEFGHJKLMNPRSTUVWXYZ0123456789"; // VIN 표준 — I, O, Q 제외

function pick<T>(arr: readonly T[]): T {
  return arr[Math.floor(Math.random() * arr.length)]!;
}

function randomVin(): string {
  // 한국차 VIN 은 K 로 시작
  let s = "K";
  for (let i = 0; i < 16; i++) s += pick(VIN_CHARS.split(""));
  return s;
}

function randomDate(yearStart: number, yearEnd: number): string {
  const year = yearStart + Math.floor(Math.random() * (yearEnd - yearStart + 1));
  const month = String(1 + Math.floor(Math.random() * 12)).padStart(2, "0");
  const day = String(1 + Math.floor(Math.random() * 28)).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

export function generateRandomVehicle(): VehicleFormData {
  const make = pick(RANDOM_POOL.make);
  const model = pick(RANDOM_POOL.modelByMake[make] ?? ["Unknown"]);
  const year = 2014 + Math.floor(Math.random() * 11); // 2014~2024
  const body_type = pick(RANDOM_POOL.body_type);
  const fuel_type = pick(RANDOM_POOL.fuel_type);

  // 차종에 따라 합리적 cc 범위 — passenger 는 1500~3500 으로 넓혀서 HS 8703.24 도 가능
  const ccBase = body_type === "truck" ? 2500 : body_type === "van" ? 2200 : 2500;
  const ccSpread = body_type === "passenger" ? 2000 : 1000;
  const engine_cc = Math.max(1000, ccBase + Math.floor((Math.random() - 0.5) * ccSpread));

  const mileage_km = 20000 + Math.floor(Math.random() * 130000);
  const list_price_usd = 8000 + Math.floor(Math.random() * 40000);
  const manufacture_date = randomDate(year, year);
  const registration_date = randomDate(year, year);

  // HS code 차종별
  const hs_code = body_type === "truck" ? "8704.21"
    : body_type === "van" ? "8702.10"
    : engine_cc > 3000 ? "8703.24"
    : engine_cc > 1500 ? "8703.23"
    : "8703.22";

  return {
    vin: randomVin(),
    make,
    model,
    year,
    body_type,
    fuel_type,
    engine_cc,
    transmission: pick(RANDOM_POOL.transmission),
    steering: pick(RANDOM_POOL.steering),
    mileage_km,
    color_exterior: pick(RANDOM_POOL.color_exterior),
    list_price_usd,
    hs_code,
    manufacture_date,
    registration_date,
  };
}
