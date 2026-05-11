"""GET /api/countries — 시드된 국가 목록 (UI 드롭다운용)."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Country

router = APIRouter(prefix="/countries", tags=["countries"])


class CountryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    name_en: str
    name_ko: str | None
    region: str | None
    primary_language: str | None
    business_language: str | None
    steering: str | None
    is_high_risk: bool
    is_russia_proxy_risk: bool
    is_sanctioned: bool
    is_blocked: bool  # findings #055 — frontend CountryMatrix 에서 미리 제외
    pre_registration_system: str | None
    consular_legalization: bool


@router.get("", response_model=list[CountryOut])
def list_countries(db: Annotated[Session, Depends(get_db)]) -> list[Country]:
    return list(db.execute(select(Country).order_by(Country.code)).scalars())


@router.get("/{code}", response_model=CountryOut)
def get_country(code: str, db: Annotated[Session, Depends(get_db)]) -> Country:
    code = code.upper()
    country = db.get(Country, code)
    if country is None:
        from fastapi import HTTPException, status
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"country {code!r} not seeded")
    return country
