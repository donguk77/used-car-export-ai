"""NHTSA vPIC API VIN 디코딩 — VIN 17자리 → 차량 사양 자동 추론.

무료, 인증 불필요. https://vpic.nhtsa.dot.gov/api/
미국 판매 차량 위주이지만 한국 제조사(Hyundai/Kia/Genesis/KGM)도 대부분 커버.

사용:
    from app.services.nhtsa import decode_vin
    result = decode_vin("KMHE41LBXJA000001")
    # result.make = "Hyundai", result.model = "Sonata", result.year = 2018, ...
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from typing import Any

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class DecodedVin:
    """우리 Vehicle 모델과 동일한 필드명 사용 → 그대로 setattr 가능."""

    vin: str
    make: str | None = None
    model: str | None = None
    year: int | None = None
    body_type: str | None = None
    fuel_type: str | None = None
    engine_cc: int | None = None
    transmission: str | None = None
    drivetrain: str | None = None
    raw: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# NHTSA 응답의 Variable 이름 → 우리 필드 매핑
_FIELD_MAP = {
    "Make": "make_raw",
    "Model": "model_raw",
    "Model Year": "year_raw",
    "Body Class": "body_type_raw",
    "Fuel Type - Primary": "fuel_type_raw",
    "Displacement (CC)": "engine_cc_raw",
    "Transmission Style": "transmission_raw",
    "Drive Type": "drivetrain_raw",
}

# Body class → 우리 enum (passenger / truck / bus / van)
_BODY_NORMALIZE = [
    ("pickup", "truck"),
    ("truck", "truck"),
    ("bus", "bus"),
    ("van", "van"),  # passenger van vs cargo van — 기본 van
    ("minivan", "van"),
    ("sedan", "passenger"),
    ("coupe", "passenger"),
    ("hatchback", "passenger"),
    ("wagon", "passenger"),
    ("convertible", "passenger"),
    ("suv", "passenger"),
    ("crossover", "passenger"),
    ("sport utility", "passenger"),
]

_FUEL_NORMALIZE = [
    ("gasoline", "Gasoline"),
    ("diesel", "Diesel"),
    ("electric", "EV"),
    ("hybrid", "Hybrid"),
    ("lpg", "LPG"),
    ("compressed natural gas", "CNG"),
    ("hydrogen", "Hydrogen"),
]

# NHTSA 의 drivetrain 값은 "FWD/Front-Wheel Drive" 처럼 길게 옴 → 짧은 코드로
_DRIVETRAIN_NORMALIZE = [
    ("4wd", "4WD"),
    ("4x4", "4WD"),
    ("all-wheel", "AWD"),
    ("awd", "AWD"),
    ("front-wheel", "FWD"),
    ("fwd", "FWD"),
    ("rear-wheel", "RWD"),
    ("rwd", "RWD"),
]


def decode_vin(vin: str, *, timeout: float = 10.0) -> DecodedVin:
    """VIN 디코드. 실패·짧은VIN·NHTSA 다운 등의 경우 빈 DecodedVin (vin만 채움)."""
    vin = (vin or "").strip().upper()
    if len(vin) != 17:
        logger.info("decode_vin: invalid length %d, skip", len(vin))
        return DecodedVin(vin=vin)

    url = f"{get_settings().nhtsa_vpic_base}/vehicles/decodevin/{vin}?format=json"
    try:
        with httpx.Client(timeout=timeout, headers={"User-Agent": "used-car-export-ai/0.1"}) as c:
            resp = c.get(url)
            resp.raise_for_status()
            data = resp.json()
    except (httpx.HTTPError, ValueError) as e:
        logger.warning("NHTSA decode failed for %s: %s", vin, e)
        return DecodedVin(vin=vin)

    parsed: dict[str, Any] = {}
    for row in data.get("Results") or []:
        var_name = row.get("Variable")
        value = row.get("Value")
        if var_name in _FIELD_MAP and value and value != "Not Applicable":
            parsed[_FIELD_MAP[var_name]] = value

    return DecodedVin(
        vin=vin,
        make=_title(parsed.get("make_raw")),
        model=_title(parsed.get("model_raw")),
        year=_safe_int(parsed.get("year_raw")),
        body_type=_normalize(parsed.get("body_type_raw"), _BODY_NORMALIZE),
        fuel_type=_normalize(parsed.get("fuel_type_raw"), _FUEL_NORMALIZE),
        engine_cc=_safe_int(parsed.get("engine_cc_raw")),
        transmission=_normalize_transmission(parsed.get("transmission_raw")),
        drivetrain=_normalize(parsed.get("drivetrain_raw"), _DRIVETRAIN_NORMALIZE),
        raw=parsed,
    )


def _safe_int(v: Any) -> int | None:
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return None


def _title(v: Any) -> str | None:
    if not v:
        return None
    s = str(v).strip()
    # 대문자 원본 (예: "HYUNDAI") → 타이틀 케이스 (Hyundai)
    return s.title() if s.isupper() else s


def _normalize(raw: Any, table: list[tuple[str, str]]) -> str | None:
    if not raw:
        return None
    rl = str(raw).lower()
    for key, val in table:
        if key in rl:
            return val
    return str(raw)


def _normalize_transmission(raw: Any) -> str | None:
    if not raw:
        return None
    rl = str(raw).lower()
    if "automatic" in rl or "auto" in rl:
        return "A/T"
    if "manual" in rl:
        return "M/T"
    if "cvt" in rl or "continuously variable" in rl:
        return "CVT"
    return str(raw)
