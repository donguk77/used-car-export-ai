"""/api/vehicles CRUD + NHTSA VIN 자동 디코드.

POST /api/vehicles                — 매물 등록 (vin 있으면 NHTSA 로 자동 채움)
GET  /api/vehicles                — 목록 (status 필터, pagination)
GET  /api/vehicles/{id}           — 1건
PATCH /api/vehicles/{id}          — 부분 수정
DELETE /api/vehicles/{id}         — 삭제
GET  /api/vehicles/decode-vin/{vin} — NHTSA 미리보기 (저장 X, UI 자동완성용)
"""

from __future__ import annotations

import uuid
from datetime import date
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id
from app.db import get_db
from app.models import Vehicle
from app.services.nhtsa import DecodedVin, decode_vin

router = APIRouter(prefix="/vehicles", tags=["vehicles"])


# ── 스키마 ─────────────────────────────────────────────────────
class VehicleBase(BaseModel):
    vin: str | None = Field(default=None, max_length=17)
    registration_no: str | None = None
    registration_date: date | None = None
    manufacture_date: date | None = None

    make: str | None = None
    model: str | None = None
    year: int | None = None
    trim: str | None = None
    body_type: str | None = Field(default=None, description="passenger/truck/bus/van")
    fuel_type: str | None = Field(default=None, description="Gasoline/Diesel/HEV/PHEV/EV")
    engine_cc: int | None = None
    transmission: str | None = None
    drivetrain: str | None = None
    steering: str | None = Field(default=None, description="LHD/RHD")
    seats: int | None = Field(default=None, description="좌석수 (HS 8702 vs 8703 분기)")
    gross_vehicle_weight_kg: int | None = Field(default=None, description="GVW kg (HS 8704 트럭 세분)")
    color_exterior: str | None = None
    color_interior: str | None = None
    mileage_km: int | None = None

    purchase_price_krw: int | None = None
    list_price_usd: float | None = None
    port_of_loading: str | None = None
    hs_code: str | None = None
    image_url: str | None = None  # AI 생성 이미지 (vehicle-images/{id}.png)


class VehicleCreate(VehicleBase):
    auto_decode_vin: bool = Field(
        default=True,
        description="vin 이 17자리면 NHTSA vPIC API 로 make/model/year/engine 자동 채움",
    )


class VehicleUpdate(VehicleBase):
    status: str | None = None


class VehicleOut(VehicleBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: str


# ── 라우트 ─────────────────────────────────────────────────────
@router.post("", response_model=VehicleOut, status_code=status.HTTP_201_CREATED)
def create_vehicle(
    payload: VehicleCreate,
    db: Annotated[Session, Depends(get_db)],
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
) -> Vehicle:
    """매물 등록. vin 17자리이고 auto_decode_vin=True 면 NHTSA 로 자동 보강.

    사용자가 명시적으로 보낸 필드는 자동값을 덮어씀 (수동 우선).
    """
    data = payload.model_dump(exclude={"auto_decode_vin"}, exclude_none=False)

    decoded: dict[str, Any] = {}
    if payload.auto_decode_vin and payload.vin and len(payload.vin) == 17:
        d = decode_vin(payload.vin)
        decoded = {
            k: v for k, v in d.to_dict().items()
            if k not in ("vin", "raw") and v is not None
        }

    # decoded 가 base, 사용자 입력이 override (사용자가 명시한 값만)
    user_provided = payload.model_dump(
        exclude={"auto_decode_vin"}, exclude_unset=True
    )
    merged = {**decoded, **user_provided}

    vehicle = Vehicle(user_id=user_id, **merged)
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)
    return vehicle


@router.get("", response_model=list[VehicleOut])
def list_vehicles(
    db: Annotated[Session, Depends(get_db)],
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    status_filter: str | None = Query(None, alias="status"),
    skip: int = 0,
    limit: int = Query(50, le=200),
) -> list[Vehicle]:
    stmt = (
        select(Vehicle)
        .where(Vehicle.user_id == user_id)
        .order_by(Vehicle.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    if status_filter:
        stmt = stmt.where(Vehicle.status == status_filter)
    return list(db.execute(stmt).scalars())


@router.get("/decode-vin/{vin}", response_model=DecodedVin)
def preview_vin_decode(
    vin: str,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],  # 외부 NHTSA 프록시 악용 방지
) -> DecodedVin:
    """NHTSA VIN 디코드 미리보기 (저장하지 않음). UI 폼 자동완성용."""
    return decode_vin(vin)


@router.get("/{vehicle_id}", response_model=VehicleOut)
def get_vehicle(
    vehicle_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
) -> Vehicle:
    v = _get_owned(db, vehicle_id, user_id)
    return v


@router.patch("/{vehicle_id}", response_model=VehicleOut)
def update_vehicle(
    vehicle_id: uuid.UUID,
    payload: VehicleUpdate,
    db: Annotated[Session, Depends(get_db)],
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
) -> Vehicle:
    v = _get_owned(db, vehicle_id, user_id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(v, key, value)
    db.commit()
    db.refresh(v)
    return v


@router.delete("/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_vehicle(
    vehicle_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
) -> Response:
    v = _get_owned(db, vehicle_id, user_id)
    db.delete(v)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ── 시세 자동 분석 + 적정 수출가 산출 (제안서 결과물) ──────────────


@router.get("/{vehicle_id}/price-suggestion", response_model=dict[str, Any])
def get_price_suggestion(
    vehicle_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    destination_country: Annotated[
        str | None,
        Query(description="ISO 3166-1 alpha-2 — 도착국 시장 보정 적용", max_length=2),
    ] = None,
) -> dict[str, Any]:
    """동급 차량 통계 + baseline + 도착국 시장 보정 → FOB USD 산출.

    docs/used_car_export_top20_countries.md 의 도착국 시장 분석 기반 multiplier.
    """
    from app.services.pricing import suggest_price  # lazy — circular 방지

    v = _get_owned(db, vehicle_id, user_id)
    suggestion = suggest_price(db, v, destination_country=destination_country)
    return suggestion.to_dict()


# ── helpers ────────────────────────────────────────────────────
def _get_owned(db: Session, vehicle_id: uuid.UUID, user_id: uuid.UUID) -> Vehicle:
    v = db.get(Vehicle, vehicle_id)
    if v is None or v.user_id != user_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"vehicle {vehicle_id} not found")
    return v
