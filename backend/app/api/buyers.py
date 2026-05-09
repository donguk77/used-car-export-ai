"""/api/buyers CRUD + 등록·수정 시 compliance 자동 트리거.

POST /api/buyers              — 등록 + 자동 compliance.check (시연 시나리오 2)
GET  /api/buyers              — 목록 (sanctions_status 필터)
GET  /api/buyers/{id}
PATCH /api/buyers/{id}        — 수정 (compliance 재실행)
DELETE /api/buyers/{id}
POST /api/buyers/{id}/recheck — compliance 강제 재검사
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
from app.core import compliance
from app.db import get_db
from app.models import Buyer, ComplianceCheck

router = APIRouter(prefix="/buyers", tags=["buyers"])


# ── 스키마 ─────────────────────────────────────────────────────
class BuyerBase(BaseModel):
    buyer_type: str | None = Field(default=None, description="Dealer/Importer/Individual")
    company_name: str | None = None
    contact_person: str | None = None
    country_code: str | None = Field(default=None, min_length=2, max_length=2)
    city: str | None = None
    address: str | None = None
    phone: str | None = None
    whatsapp: str | None = None
    email: str | None = None
    business_license: str | None = None
    tax_id: str | None = None

    preferred_language: str | None = None
    preferred_currency: str | None = None
    preferred_payment: str | None = None
    preferred_port: str | None = None
    preferred_incoterm: str | None = None


class BuyerCreate(BuyerBase):
    country_code: str = Field(min_length=2, max_length=2)


class BuyerUpdate(BuyerBase):
    pass


class BuyerOut(BuyerBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    sanctions_status: str
    russia_proxy_risk_score: int | None
    total_orders: int


class ComplianceFindingOut(BaseModel):
    severity: str
    code: str
    message: str


class ComplianceReportOut(BaseModel):
    overall: str
    score: int
    findings: list[ComplianceFindingOut]


class BuyerCreateResponse(BaseModel):
    buyer: BuyerOut
    compliance: ComplianceReportOut


# ── 라우트 ─────────────────────────────────────────────────────
@router.post("", response_model=BuyerCreateResponse, status_code=status.HTTP_201_CREATED)
def create_buyer(
    payload: BuyerCreate,
    db: Annotated[Session, Depends(get_db)],
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
) -> dict[str, Any]:
    buyer = Buyer(
        user_id=user_id,
        country_code=payload.country_code.upper(),
        **payload.model_dump(exclude={"country_code"}, exclude_none=True),
    )
    db.add(buyer)
    db.flush()
    report = _run_compliance(db, buyer)
    db.commit()
    db.refresh(buyer)
    return {"buyer": buyer, "compliance": report}


@router.get("", response_model=list[BuyerOut])
def list_buyers(
    db: Annotated[Session, Depends(get_db)],
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    sanctions_status: str | None = Query(None, description="clean/warning/blocked/unchecked"),
    skip: int = 0,
    limit: int = Query(50, le=200),
) -> list[Buyer]:
    stmt = (
        select(Buyer)
        .where(Buyer.user_id == user_id)
        .order_by(Buyer.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    if sanctions_status:
        stmt = stmt.where(Buyer.sanctions_status == sanctions_status)
    return list(db.execute(stmt).scalars())


@router.get("/{buyer_id}", response_model=BuyerOut)
def get_buyer(
    buyer_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
) -> Buyer:
    return _get_owned(db, buyer_id, user_id)


@router.patch("/{buyer_id}", response_model=BuyerOut)
def update_buyer(
    buyer_id: uuid.UUID,
    payload: BuyerUpdate,
    db: Annotated[Session, Depends(get_db)],
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
) -> Buyer:
    buyer = _get_owned(db, buyer_id, user_id)
    update_data = payload.model_dump(exclude_unset=True)
    if "country_code" in update_data and update_data["country_code"]:
        update_data["country_code"] = update_data["country_code"].upper()

    needs_recheck = any(
        k in update_data for k in ("country_code", "company_name", "tax_id")
    )
    for key, value in update_data.items():
        setattr(buyer, key, value)
    db.flush()

    if needs_recheck:
        _run_compliance(db, buyer)

    db.commit()
    db.refresh(buyer)
    return buyer


@router.delete("/{buyer_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_buyer(
    buyer_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
) -> Response:
    buyer = _get_owned(db, buyer_id, user_id)
    db.delete(buyer)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{buyer_id}/recheck", response_model=ComplianceReportOut)
def recheck_compliance(
    buyer_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
) -> dict[str, Any]:
    buyer = _get_owned(db, buyer_id, user_id)
    report = _run_compliance(db, buyer)
    db.commit()
    return report


# ── helpers ────────────────────────────────────────────────────
def _get_owned(db: Session, buyer_id: uuid.UUID, user_id: uuid.UUID) -> Buyer:
    b = db.get(Buyer, buyer_id)
    if b is None or b.user_id != user_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"buyer {buyer_id} not found")
    return b


def _run_compliance(db: Session, buyer: Buyer) -> dict[str, Any]:
    """compliance.check() 실행 → ComplianceCheck 행 저장 + Buyer 요약 갱신."""
    report = compliance.check(buyer, vehicle=None)

    check = ComplianceCheck(
        buyer_id=buyer.id,
        check_type="auto_summary",
        result=report.overall,
        flags_json=[f.to_dict() for f in report.findings],
        raw_response={"overall": report.overall, "score": report.score},
        checked_at=date.today(),
    )
    db.add(check)

    buyer.sanctions_status = report.overall
    buyer.russia_proxy_risk_score = max(0, 100 - report.score) if report.overall != "clean" else 0
    db.flush()

    return report.to_dict()
