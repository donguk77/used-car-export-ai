"""GET/POST/PUT/DELETE /api/countries — 국가 + 통관 룰 CRUD (LLM Wiki 편집).

기존 GET 목록 + 단건 endpoint 에 더해, 28국 yaml rule을 웹 UI에서 편집할 수 있도록
country/rule CRUD endpoints 추가. 제안서 "사용자가 직접 LLM Wiki를 편집·확장할 수
있는 관리 페이지" 충족.
"""

from __future__ import annotations

import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from app.db import get_db
from app.models import Country, ImportRule

router = APIRouter(prefix="/countries", tags=["countries"])


# ── Schemas ───────────────────────────────────────────────────────


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
    is_blocked: bool
    pre_registration_system: str | None
    consular_legalization: bool


class RuleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    country_code: str
    body_type_filter: str | None
    age_limit_years: int | None
    age_basis: str | None
    age_effective_from: date | None
    registration_after_date: date | None
    steering_required: str | None
    max_engine_cc: int | None
    max_cylinders: int | None
    fuel_blocked_json: list = Field(default_factory=list)
    psi_required: list[str] = Field(default_factory=list)
    doc_translation_lang: str | None
    consular_required: bool
    pre_registration: str | None
    blocked_conditions_json: list = Field(default_factory=list)
    required_documents_json: list = Field(default_factory=list)
    effective_from: date | None
    effective_to: date | None
    source_url: str | None
    last_verified_at: date | None
    notes: str | None


class CountryDetailOut(CountryOut):
    """편집 페이지용 — country meta + 모든 rules 포함."""

    name_local: str | None
    main_ports_json: list = Field(default_factory=list)
    notes: str | None
    rules: list[RuleOut] = Field(default_factory=list)


class CountryUpsert(BaseModel):
    """POST/PUT body — country meta 입력. PUT 시 code는 path 사용."""

    code: str | None = None
    name_en: str
    name_ko: str | None = None
    name_local: str | None = None
    region: str | None = None
    primary_language: str | None = None
    business_language: str | None = None
    steering: str | None = None
    is_high_risk: bool = False
    is_russia_proxy_risk: bool = False
    is_sanctioned: bool = False
    is_blocked: bool = False
    main_ports_json: list = Field(default_factory=list)
    pre_registration_system: str | None = None
    consular_legalization: bool = False
    notes: str | None = None


class RuleUpsert(BaseModel):
    """POST/PUT rule body."""

    body_type_filter: str | None = None
    age_limit_years: int | None = None
    age_basis: str | None = None
    age_effective_from: date | None = None
    registration_after_date: date | None = None
    steering_required: str | None = None
    max_engine_cc: int | None = None
    max_cylinders: int | None = None
    fuel_blocked_json: list = Field(default_factory=list)
    psi_required: list[str] = Field(default_factory=list)
    doc_translation_lang: str | None = None
    consular_required: bool = False
    pre_registration: str | None = None
    blocked_conditions_json: list = Field(default_factory=list)
    required_documents_json: list = Field(default_factory=list)
    effective_from: date | None = None
    effective_to: date | None = None
    source_url: str | None = None
    last_verified_at: date | None = None
    notes: str | None = None


# ── Country endpoints ──────────────────────────────────────────────


@router.get("", response_model=list[CountryOut])
def list_countries(db: Annotated[Session, Depends(get_db)]) -> list[Country]:
    return list(db.execute(select(Country).order_by(Country.code)).scalars())


@router.post("", response_model=CountryDetailOut, status_code=status.HTTP_201_CREATED)
def create_country(
    payload: CountryUpsert,
    db: Annotated[Session, Depends(get_db)],
) -> Country:
    """신규 국가 추가 (28국 외 확장 시연용)."""
    if not payload.code:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "code is required for new country")
    code = payload.code.upper()
    if len(code) != 2:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "ISO 3166-1 alpha-2 (2 letters)")
    if db.get(Country, code) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, f"country {code!r} already exists")
    country = Country(code=code)
    _apply_country(country, payload)
    db.add(country)
    db.commit()
    db.refresh(country)
    return country


@router.get("/{code}", response_model=CountryOut)
def get_country(code: str, db: Annotated[Session, Depends(get_db)]) -> Country:
    country = db.get(Country, code.upper())
    if country is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"country {code!r} not seeded")
    return country


@router.get("/{code}/full", response_model=CountryDetailOut)
def get_country_full(code: str, db: Annotated[Session, Depends(get_db)]) -> Country:
    """편집 페이지용 — country + 모든 rules 한 번에."""
    country = db.execute(
        select(Country)
        .where(Country.code == code.upper())
        .options(selectinload(Country.rules))
    ).scalar_one_or_none()
    if country is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"country {code!r} not found")
    return country


@router.put("/{code}", response_model=CountryDetailOut)
def update_country(
    code: str,
    payload: CountryUpsert,
    db: Annotated[Session, Depends(get_db)],
) -> Country:
    country = db.execute(
        select(Country)
        .where(Country.code == code.upper())
        .options(selectinload(Country.rules))
    ).scalar_one_or_none()
    if country is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"country {code!r} not found")
    _apply_country(country, payload)
    db.commit()
    db.refresh(country)
    return country


@router.delete("/{code}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_country(code: str, db: Annotated[Session, Depends(get_db)]) -> Response:
    country = db.get(Country, code.upper())
    if country is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"country {code!r} not found")
    db.delete(country)  # cascade rules
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ── Rule endpoints ─────────────────────────────────────────────────


@router.post(
    "/{code}/rules",
    response_model=RuleOut,
    status_code=status.HTTP_201_CREATED,
)
def create_rule(
    code: str,
    payload: RuleUpsert,
    db: Annotated[Session, Depends(get_db)],
) -> ImportRule:
    code = code.upper()
    if db.get(Country, code) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"country {code!r} not found")
    rule = ImportRule(country_code=code)
    _apply_rule(rule, payload)
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@router.put("/{code}/rules/{rule_id}", response_model=RuleOut)
def update_rule(
    code: str,
    rule_id: uuid.UUID,
    payload: RuleUpsert,
    db: Annotated[Session, Depends(get_db)],
) -> ImportRule:
    rule = db.get(ImportRule, rule_id)
    if rule is None or rule.country_code != code.upper():
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            f"rule {rule_id} not found in {code!r}",
        )
    _apply_rule(rule, payload)
    db.commit()
    db.refresh(rule)
    return rule


@router.delete(
    "/{code}/rules/{rule_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def delete_rule(
    code: str,
    rule_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    rule = db.get(ImportRule, rule_id)
    if rule is None or rule.country_code != code.upper():
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            f"rule {rule_id} not found in {code!r}",
        )
    db.delete(rule)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ── helpers ────────────────────────────────────────────────────────


def _apply_country(country: Country, payload: CountryUpsert) -> None:
    country.name_en = payload.name_en
    country.name_ko = payload.name_ko
    country.name_local = payload.name_local
    country.region = payload.region
    country.primary_language = payload.primary_language
    country.business_language = payload.business_language
    country.steering = payload.steering
    country.is_high_risk = payload.is_high_risk
    country.is_russia_proxy_risk = payload.is_russia_proxy_risk
    country.is_sanctioned = payload.is_sanctioned
    country.is_blocked = payload.is_blocked
    country.main_ports_json = list(payload.main_ports_json or [])
    country.pre_registration_system = payload.pre_registration_system
    country.consular_legalization = payload.consular_legalization
    country.notes = payload.notes


def _apply_rule(rule: ImportRule, payload: RuleUpsert) -> None:
    rule.body_type_filter = payload.body_type_filter
    rule.age_limit_years = payload.age_limit_years
    rule.age_basis = payload.age_basis
    rule.age_effective_from = payload.age_effective_from
    rule.registration_after_date = payload.registration_after_date
    rule.steering_required = payload.steering_required
    rule.max_engine_cc = payload.max_engine_cc
    rule.max_cylinders = payload.max_cylinders
    rule.fuel_blocked_json = list(payload.fuel_blocked_json or [])
    rule.psi_required = list(payload.psi_required or [])
    rule.doc_translation_lang = payload.doc_translation_lang
    rule.consular_required = payload.consular_required
    rule.pre_registration = payload.pre_registration
    rule.blocked_conditions_json = list(payload.blocked_conditions_json or [])
    rule.required_documents_json = list(payload.required_documents_json or [])
    rule.effective_from = payload.effective_from
    rule.effective_to = payload.effective_to
    rule.source_url = payload.source_url
    rule.last_verified_at = payload.last_verified_at
    rule.notes = payload.notes
