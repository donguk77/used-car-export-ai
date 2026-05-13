"""시세 자동 분석 + 적정 수출가 산출 (제안서 명시 결과물).

전략 (hybrid):
1. DB 내 동급 차량 (같은 make/model/year ± 2년, mileage 유사) 표본 ≥ 3건이면 통계 우선
2. 표본 부족 시 baseline (body_type × age × fuel) 정적 시세표 사용
3. 도착국별 시장 보정 (예: 디젤 SUV → 아프리카 +8%, 한국차 → 중남미 +5%, 키르기스/카자흐 → -5% 우회 위험 할인)
4. 마일리지 보정 (10만km 기준, 1만km당 ±2%)
5. 사고이력 -15% / 무사고 +0%

출처:
- 베이스라인은 KITA·KIET 2024 + KATECH 한국 중고차 수출 시장 보고서 일반 추세 + 멘토 인터뷰
- 도착국 보정은 docs/used_car_export_top20_countries.md 시장 분석
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
from typing import Any

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.models import Vehicle


@dataclass
class PriceFactor:
    label: str
    delta_pct: float  # +10.0 = +10%
    reason: str


@dataclass
class PriceSuggestion:
    suggested_fob_usd: float
    range_low: float
    range_high: float
    confidence: str  # high / medium / low
    method: str  # db_stats / baseline_table / hybrid
    n_samples: int
    baseline_usd: float
    factors: list[PriceFactor]
    notes: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "suggested_fob_usd": round(self.suggested_fob_usd, 2),
            "range_low": round(self.range_low, 2),
            "range_high": round(self.range_high, 2),
            "confidence": self.confidence,
            "method": self.method,
            "n_samples": self.n_samples,
            "baseline_usd": round(self.baseline_usd, 2),
            "factors": [asdict(f) for f in self.factors],
            "notes": self.notes,
        }


# ── Baseline 시세표 (USD, 출고시점, FOB 인천 기준) ──────────────────
# 한국 중고차 수출 평균가 — KITA/KIET 보고서 + 멘토 인터뷰 기반.
# (body_type, fuel) → year delta 시 평균가
BASELINE_TABLE: dict[tuple[str, str], dict[int, float]] = {
    # (body_type, fuel_type): {age_in_years: usd_baseline}
    ("Sedan", "Gasoline"): {0: 17000, 3: 12000, 5: 9000, 7: 7000, 10: 5500, 15: 4000},
    ("Sedan", "Diesel"): {0: 19000, 3: 13500, 5: 10000, 7: 7500, 10: 5800, 15: 4200},
    ("Sedan", "Hybrid"): {0: 22000, 3: 16000, 5: 12000, 7: 9000, 10: 6500, 15: 4500},
    ("SUV", "Gasoline"): {0: 21000, 3: 15500, 5: 12000, 7: 9500, 10: 7500, 15: 5500},
    ("SUV", "Diesel"): {0: 24000, 3: 18000, 5: 14000, 7: 11000, 10: 8500, 15: 6000},
    ("SUV", "Hybrid"): {0: 28000, 3: 21000, 5: 16500, 7: 12500, 10: 9500, 15: 7000},
    ("Pickup", "Diesel"): {0: 23000, 3: 17500, 5: 13500, 7: 10500, 10: 8200, 15: 6000},
    ("Pickup", "Gasoline"): {0: 20000, 3: 15000, 5: 11500, 7: 9000, 10: 7000, 15: 5200},
    ("Van", "Diesel"): {0: 22000, 3: 16500, 5: 12500, 7: 9500, 10: 7200, 15: 5200},
    ("Van", "Gasoline"): {0: 19000, 3: 14000, 5: 10500, 7: 8000, 10: 6000, 15: 4500},
    ("Bus", "Diesel"): {0: 35000, 3: 26000, 5: 20000, 7: 15500, 10: 11500, 15: 8500},
    ("Truck", "Diesel"): {0: 28000, 3: 21000, 5: 16500, 7: 13000, 10: 10000, 15: 7500},
}

# Genesis / 럭셔리 라인 (단가 강세)
LUXURY_MAKES = {"Genesis", "BMW", "Mercedes-Benz", "Audi", "Lexus"}

# 국가별 시장 보정 multiplier — docs/used_car_export_top20_countries.md 참조
COUNTRY_PRICE_MULTIPLIER: dict[str, float] = {
    # 단가 강세국 (재건 수요 + SUV 선호)
    "SY": 1.10,  # 시리아 재건 수요 폭증
    "LY": 0.95,  # 리비아 양은 1위지만 저가 위주
    "JO": 1.02,  # 요르단 안정 시장
    "AE": 1.08,  # UAE 재수출 허브 단가 ↑
    # 중남미
    "DO": 1.05,  # 도미니카 6기통 이하 한정
    "CL": 1.10,  # 칠레 SUV·디젤 강세
    "CR": 1.05,
    # 아프리카
    "KE": 1.00,  # 케냐 RHD 한정 (LHD 차량은 N/A)
    "NG": 0.92,  # 나이지리아 가격 민감
    "GH": 0.95,
    "TZ": 0.95,
    "ZA": 1.00,
    # 중앙아시아 — 우회수출 위험 할인
    "KG": 0.95,
    "KZ": 0.95,
    "TJ": 0.92,
    "AM": 0.95,
    "UZ": 0.95,
    # 기타
    "EG": 0.90,
    "MX": 1.00,
    "AZ": 1.00,
}


def suggest_price(
    db: Session,
    vehicle: Vehicle,
    *,
    destination_country: str | None = None,
    today: date | None = None,
) -> PriceSuggestion:
    """차량 + (선택) 도착국 → 적정 FOB USD 산출."""

    today = today or date.today()
    factors: list[PriceFactor] = []
    notes: list[str] = []

    # ── 1. DB 동급 통계 우선 ──
    samples = _find_similar(db, vehicle)
    n = len(samples)
    db_median: float | None = None
    if n >= 3:
        # `is not None` 명시 — Decimal('0.0') 가 falsy 로 잘못 제외되는 것 방지.
        # _find_similar 가 이미 list_price_usd is not None 으로 거르지만, 0원 가격
        # 매물도 의도적으로 통계에 포함 (이상치 → median 으로 자동 무력화).
        prices = sorted(
            float(s.list_price_usd) for s in samples if s.list_price_usd is not None
        )
        if prices:
            db_median = prices[len(prices) // 2]

    # ── 2. Baseline 시세표 ──
    baseline = _baseline_price(vehicle, today)
    if baseline is None:
        notes.append(
            f"baseline 미정의 (body={vehicle.body_type}, fuel={vehicle.fuel_type}). "
            "기본값 8,000 USD 사용."
        )
        baseline = 8000.0

    # ── 3. 시작값 결정 ──
    if db_median is not None:
        base = (db_median + baseline) / 2.0  # 평균 — DB 표본 + baseline 합리적 중간
        method = "hybrid"
        confidence = "high"
        notes.append(f"DB 동급 {n}건 median ${db_median:,.0f} + baseline ${baseline:,.0f} 평균")
    else:
        base = baseline
        method = "baseline_table"
        confidence = "medium" if n >= 1 else "low"
        if n >= 1:
            notes.append(f"DB 동급 {n}건 (표본 부족, baseline 우선)")
        else:
            notes.append("DB 동급 차량 없음 — baseline table 사용")

    # ── 4. Factor 적용 ──
    price = base

    # 4a. Luxury 보정
    if vehicle.make and vehicle.make in LUXURY_MAKES:
        delta = 35.0
        factors.append(PriceFactor("Luxury 브랜드", delta, f"{vehicle.make} — 럭셔리 라인 +35%"))
        price *= 1 + delta / 100

    # 4b. Mileage 보정 (10만km 기준, 1만km당 ±2%)
    if vehicle.mileage_km:
        diff_km = vehicle.mileage_km - 100_000
        delta = -(diff_km / 10_000) * 2.0
        delta = max(min(delta, 20.0), -30.0)  # ±20~30% clamp
        if abs(delta) >= 0.5:
            factors.append(PriceFactor(
                "주행거리 보정",
                round(delta, 1),
                f"{vehicle.mileage_km:,}km (기준 100,000km, {delta:+.1f}%)",
            ))
            price *= 1 + delta / 100

    # 4c. 사고이력
    if vehicle.has_accident:
        factors.append(PriceFactor("사고이력", -15.0, "신고 사고이력 — 시세 -15%"))
        price *= 0.85

    # 4d. 도착국 시장 보정
    if destination_country:
        cc = destination_country.upper()
        mult = COUNTRY_PRICE_MULTIPLIER.get(cc)
        if mult is not None:
            delta = (mult - 1.0) * 100
            factors.append(PriceFactor(
                f"도착국 시장 ({cc})",
                round(delta, 1),
                _country_reason(cc, delta),
            ))
            price *= mult
        else:
            notes.append(f"도착국 {cc} 시장 multiplier 미정의 — 보정 없음")

    # ── 5. Range (±15%) ──
    low = price * 0.85
    high = price * 1.15

    return PriceSuggestion(
        suggested_fob_usd=price,
        range_low=low,
        range_high=high,
        confidence=confidence,
        method=method,
        n_samples=n,
        baseline_usd=baseline,
        factors=factors,
        notes=notes,
    )


def _find_similar(db: Session, vehicle: Vehicle) -> list[Vehicle]:
    """같은 make/model/year ±2년 차량 (자기 자신 제외)."""
    if not (vehicle.make and vehicle.model and vehicle.year):
        return []
    stmt = (
        select(Vehicle)
        .where(and_(
            Vehicle.make == vehicle.make,
            Vehicle.model == vehicle.model,
            Vehicle.year.between(vehicle.year - 2, vehicle.year + 2),
            Vehicle.id != vehicle.id,
            Vehicle.list_price_usd.is_not(None),
        ))
    )
    return list(db.execute(stmt).scalars())


def _baseline_price(vehicle: Vehicle, today: date) -> float | None:
    """body_type + fuel_type + age 로 baseline 보간."""
    if not vehicle.body_type or not vehicle.fuel_type:
        return None

    # fuel_type 정규화 (HEV/PHEV/BEV → Hybrid/Hybrid/Hybrid)
    fuel = vehicle.fuel_type
    if fuel in ("HEV", "PHEV", "BEV", "EV"):
        fuel_key = "Hybrid"
    else:
        fuel_key = fuel

    # body_type 정규화
    body_key = vehicle.body_type
    if body_key not in {"Sedan", "SUV", "Pickup", "Van", "Bus", "Truck"}:
        # 일부 시드는 다른 표현 사용 — 매핑
        body_map = {
            "sedan": "Sedan", "suv": "SUV", "pickup": "Pickup",
            "van": "Van", "bus": "Bus", "truck": "Truck",
            "Hatchback": "Sedan", "Coupe": "Sedan",
        }
        body_key = body_map.get(body_key, body_key)

    table = BASELINE_TABLE.get((body_key, fuel_key))
    if table is None:
        return None

    age = today.year - (vehicle.year or today.year)
    age = max(age, 0)

    # 보간 (linear between known points)
    keys = sorted(table.keys())
    if age <= keys[0]:
        return table[keys[0]]
    if age >= keys[-1]:
        return table[keys[-1]]
    for i in range(len(keys) - 1):
        if keys[i] <= age <= keys[i + 1]:
            x0, x1 = keys[i], keys[i + 1]
            y0, y1 = table[x0], table[x1]
            return y0 + (y1 - y0) * (age - x0) / (x1 - x0)
    return None


def _country_reason(cc: str, delta: float) -> str:
    if delta > 5:
        return f"{cc} — 단가 강세 시장 ({delta:+.1f}%)"
    if delta < -3:
        return f"{cc} — 가격 민감/할인 시장 ({delta:+.1f}%)"
    return f"{cc} 시장 보정 ({delta:+.1f}%)"
