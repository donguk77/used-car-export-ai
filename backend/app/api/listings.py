"""POST /api/listings/import-check — 차량 + 바이어 + 도착국 → 통관·컴플라이언스 통합 판정.

룰엔진(rule_engine.evaluate) + 컴플라이언스(compliance.check) 두 모듈의 결과를 한 번에 리턴.
DB에는 아무것도 저장하지 않는 순수 평가 엔드포인트 — 매물 등록 후 실행하는 사전 체크 용도.
"""

from __future__ import annotations

from datetime import date
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core import compliance
from app.core.rule_engine import evaluate
from app.db import get_db
from app.models import Buyer, Country, Vehicle

router = APIRouter()


# ── 요청 스키마 ─────────────────────────────────────────────────
class VehicleInput(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "vin": "KMHE41LBXKA000001",
            "make": "Hyundai",
            "model": "Sonata",
            "year": 2018,
            "body_type": "passenger",
            "fuel_type": "Gasoline",
            "engine_cc": 2000,
            "steering": "LHD",
            "mileage_km": 65000,
            "list_price_usd": 12500,
            "manufacture_date": "2018-03-01",
            "registration_date": "2018-06-01",
        }
    })

    vin: str | None = None
    make: str | None = None
    model: str | None = None
    year: int | None = None
    body_type: str | None = Field(default=None, description="passenger/truck/bus/suv")
    fuel_type: str | None = Field(default=None, description="Gasoline/Diesel/HEV/PHEV/EV")
    engine_cc: int | None = None
    transmission: str | None = None
    steering: str | None = Field(default=None, description="LHD/RHD")
    mileage_km: int | None = None
    color_exterior: str | None = None
    list_price_usd: float | None = None
    manufacture_date: date | None = None
    registration_date: date | None = None


class BuyerInput(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "company_name": "Rodriguez Motors",
            "contact_person": "Sr. Carlos Rodríguez",
            "country_code": "DO",
            "tax_id": "DO-987654",
            "total_orders": 12,
        }
    })

    company_name: str | None = None
    contact_person: str | None = None
    country_code: str = Field(min_length=2, max_length=2, description="ISO 3166-1 (KE, DO, ...)")
    tax_id: str | None = None
    total_orders: int = 0
    sanctions_status: str = "unchecked"


class ImportCheckRequest(BaseModel):
    vehicle: VehicleInput
    destination_country: str = Field(
        min_length=2, max_length=2, description="ISO 3166-1 (KE, DO, LY, ...)"
    )
    buyer: BuyerInput | None = None
    granted_flags: list[str] = Field(
        default_factory=list,
        description='면제 플래그. 예: ["has_situational_license"] (전략물자 상황허가 보유)',
    )
    today: date | None = Field(
        default=None,
        description="발효일 기반 룰 테스트용 (예: 케냐 2026.1.1 cutoff). 미지정시 오늘",
    )


# ── 응답 스키마 ─────────────────────────────────────────────────
class ImportCheckResponse(BaseModel):
    can_import: bool
    rule_check: dict[str, Any]
    compliance: dict[str, Any] | None = None


# ── 라우트 ─────────────────────────────────────────────────────
@router.post(
    "/listings/import-check",
    response_model=ImportCheckResponse,
    summary="통관 + 컴플라이언스 사전 체크",
    description=(
        "차량 + (선택) 바이어 + 도착국 → 통관 가능 여부 + 컴플라이언스 리포트.\n\n"
        "DB의 import_rules 테이블 (시드: configs/rules/*.yaml) 을 사용.\n\n"
        "시연 시나리오 5개는 `scripts/demo_rule_engine.py` 의 케이스를 그대로 호출 가능."
    ),
)
def import_check(
    payload: ImportCheckRequest,
    db: Annotated[Session, Depends(get_db)],
) -> ImportCheckResponse:
    code = payload.destination_country.upper()

    country = db.execute(
        select(Country)
        .where(Country.code == code)
        .options(selectinload(Country.rules))
    ).scalar_one_or_none()

    if country is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"country {code!r} not in import_rules database. "
                f"Currently seeded: DO, KE, KG, LY, SY. "
                f"Run `python -m app.seed.import_rules` to refresh."
            ),
        )

    vehicle = _to_vehicle(payload.vehicle)
    buyer = _to_buyer(payload.buyer)

    rule_result = evaluate(
        vehicle,
        country,
        rules=country.rules,
        buyer=buyer,
        today=payload.today,
        granted_flags=set(payload.granted_flags),
    )

    compliance_dict: dict[str, Any] | None = None
    if buyer is not None:
        compliance_dict = compliance.check(buyer, vehicle).to_dict()

    return ImportCheckResponse(
        can_import=rule_result.can_import,
        rule_check=rule_result.to_dict(),
        compliance=compliance_dict,
    )


# ── helpers — Pydantic input → ORM (transient, DB 미저장) ──────
def _to_vehicle(v: VehicleInput) -> Vehicle:
    return Vehicle(
        vin=v.vin,
        make=v.make,
        model=v.model,
        year=v.year,
        body_type=v.body_type,
        fuel_type=v.fuel_type,
        engine_cc=v.engine_cc,
        transmission=v.transmission,
        steering=v.steering,
        mileage_km=v.mileage_km,
        color_exterior=v.color_exterior,
        list_price_usd=v.list_price_usd,
        manufacture_date=v.manufacture_date,
        registration_date=v.registration_date,
    )


def _to_buyer(b: BuyerInput | None) -> Buyer | None:
    if b is None:
        return None
    return Buyer(
        company_name=b.company_name,
        contact_person=b.contact_person,
        country_code=b.country_code.upper(),
        tax_id=b.tax_id,
        total_orders=b.total_orders,
        sanctions_status=b.sanctions_status,
    )
