"""차량 spec → HS Code 자동 분류 (HS 2022 기준).

WCO HS 2022 의 87류 (Vehicles other than railway):
  8702: ≥10인승 운송 차량 (버스)
  8703: ≤9인승 승용차 (포함 station wagon, 레이싱카)
  8704: 화물 운송 차량 (트럭)
  8705: 특수 목적 차량
  8711: 모터사이클

8703 세분 (2024 개정):
  8703.10  Snow vehicles (제외)
  8703.21  Other vehicles, spark-ignition (gasoline) — cylinder ≤ 1,000cc
  8703.22  Other vehicles, gasoline — 1,000cc < cylinder ≤ 1,500cc
  8703.23  Other vehicles, gasoline — 1,500cc < cylinder ≤ 3,000cc  (가장 흔함)
  8703.24  Other vehicles, gasoline — cylinder > 3,000cc
  8703.31  Other vehicles, compression-ignition (diesel) — cylinder ≤ 1,500cc
  8703.32  Other vehicles, diesel — 1,500cc < cylinder ≤ 2,500cc
  8703.33  Other vehicles, diesel — cylinder > 2,500cc
  8703.40  Hybrid (gasoline + electric), 전기 충전 불가  (HEV)
  8703.50  Hybrid (diesel + electric), 전기 충전 불가
  8703.60  Plug-in hybrid (gasoline + electric)            (PHEV)
  8703.70  Plug-in hybrid (diesel + electric)
  8703.80  Solely electric                                 (BEV)
  8703.90  Other (water vapor, hydrogen 등)

8702 세분:
  8702.10  Diesel/semi-diesel, ≥10 seats incl driver
  8702.20  Hybrid diesel + electric, ≥10 seats
  8702.30  Hybrid gasoline + electric, ≥10 seats
  8702.40  Solely electric, ≥10 seats
  8702.90  Other (gasoline, water vapor 등)

8704 세분:
  8704.21  Diesel, GVW ≤ 5t
  8704.22  Diesel, 5 < GVW ≤ 20t
  8704.23  Diesel, GVW > 20t
  8704.31  Gasoline, GVW ≤ 5t
  8704.32  Gasoline, GVW > 5t

PoC 한계: GVW (총 중량) 와 좌석수는 우리 Vehicle 모델에 없음 — 향후 보강 후보.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HSClassification:
    """HS code + 분류 근거 (감사 가능)."""

    hs_code: str
    rationale: str
    confidence: float  # 0.0~1.0


_HEV_KEYWORDS = {"HEV", "Hybrid", "Mild Hybrid"}
_PHEV_KEYWORDS = {"PHEV", "Plug-in Hybrid", "Plugin Hybrid"}
_BEV_KEYWORDS = {"EV", "BEV", "Electric"}
_DIESEL_KEYWORDS = {"Diesel", "diesel"}
_GASOLINE_KEYWORDS = {"Gasoline", "gasoline", "Petrol", "petrol"}


def _matches_any(fuel: str, keywords: set[str]) -> bool:
    """단어 단위 정확 매치 — 'HEV' 가 'EV' substring 매치하는 버그 방지."""
    tokens = {t.strip() for t in fuel.replace("-", " ").replace("/", " ").split()}
    return bool(tokens & keywords) or fuel in keywords


def classify(
    *,
    body_type: str | None,
    fuel_type: str | None,
    engine_cc: int | None,
) -> HSClassification:
    """Vehicle spec → 6자리 HS code 추정.

    Args:
        body_type: passenger / bus / truck / van (None 시 passenger 가정)
        fuel_type: Gasoline / Diesel / HEV / PHEV / EV / Hybrid 등
        engine_cc: 배기량 (None 시 1500cc 가정 — 가장 흔한 8703.23 fallback)

    Returns:
        HSClassification — confidence 가 0.7 이하면 사람 검토 권장.
    """
    body = (body_type or "passenger").lower()
    fuel = (fuel_type or "Gasoline").strip()
    cc = engine_cc or 1500

    # 화물 차량 (8704)
    if body == "truck":
        # GVW 정보 없어 ≤5t 가정 (한국 1톤 트럭 봉고 등 대부분)
        if fuel in _DIESEL_KEYWORDS:
            return HSClassification("8704.21", f"truck + diesel + GVW≤5t 가정", 0.7)
        return HSClassification("8704.31", f"truck + gasoline + GVW≤5t 가정", 0.7)

    # 버스 / 승합차 (8702)
    if body in ("bus", "van"):
        # van 은 좌석수 모호 — ≥10인승 가정 (Grand Starex 등)
        if fuel in _DIESEL_KEYWORDS:
            return HSClassification("8702.10", f"{body} + diesel + ≥10 seats 가정", 0.6)
        if _matches_any(fuel, _BEV_KEYWORDS):
            return HSClassification("8702.40", f"{body} + EV", 0.8)
        if _matches_any(fuel, _HEV_KEYWORDS) or _matches_any(fuel, _PHEV_KEYWORDS):
            ext = "diesel-hybrid" if "Diesel" in fuel else "gasoline-hybrid"
            return HSClassification("8702.20" if "Diesel" in fuel else "8702.30",
                                    f"{body} + {ext}", 0.7)
        return HSClassification("8702.90", f"{body} + gasoline 추정", 0.6)

    # 승용차 (8703) — 가장 일반적인 케이스
    # PHEV
    if _matches_any(fuel, _PHEV_KEYWORDS):
        return HSClassification(
            "8703.70" if "Diesel" in fuel else "8703.60",
            f"PHEV ({fuel})", 0.85,
        )
    # BEV
    if _matches_any(fuel, _BEV_KEYWORDS):
        return HSClassification("8703.80", f"BEV ({fuel})", 0.95)
    # HEV
    if _matches_any(fuel, _HEV_KEYWORDS):
        return HSClassification(
            "8703.50" if "Diesel" in fuel else "8703.40",
            f"HEV ({fuel})", 0.85,
        )

    # ICE 가솔린 / 디젤
    if fuel in _DIESEL_KEYWORDS:
        if cc < 1500:
            return HSClassification("8703.31", f"diesel + cc<1,500", 0.95)
        if cc <= 2500:
            return HSClassification("8703.32", f"diesel + 1,500<cc≤2,500", 0.95)
        return HSClassification("8703.33", f"diesel + cc>2,500", 0.95)

    # default: gasoline
    if cc < 1000:
        return HSClassification("8703.21", f"gasoline + cc<1,000", 0.95)
    if cc <= 1500:
        return HSClassification("8703.22", f"gasoline + cc≤1,500", 0.95)
    if cc <= 3000:
        return HSClassification("8703.23", f"gasoline + 1,500<cc≤3,000", 0.95)
    return HSClassification("8703.24", f"gasoline + cc>3,000", 0.95)
