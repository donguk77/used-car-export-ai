"""/api/listings — 거래(매물×바이어×도착국) CRUD + 통관 판정.

POST /api/listings              — 거래 생성 (자동 import-check 실행)
GET  /api/listings              — 목록 (status 필터)
POST /api/listings/import-check — DB 저장 없이 평가만 (시연 1단계용)
GET  /api/listings/{id}
PATCH /api/listings/{id}        — 가격·상태 등 갱신 (status FSM)
DELETE /api/listings/{id}
"""

from __future__ import annotations

import logging
import uuid
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Annotated, Any

logger = logging.getLogger(__name__)

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user_id
from app.core import compliance, hs_classifier
from app.core.rule_engine import ImportCheckResult, RuleEngineError, evaluate
from app.db import get_db
from app.models import Buyer, Country, Document, Listing, Message, User, Vehicle
from app.services.document_writer import DocumentInput, generate_all
from app.services.mail_writer import MailDraftParseError, MailRequest, MailWriter

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
GENERATED_PDFS_DIR = PROJECT_ROOT / "generated_pdfs"

router = APIRouter(prefix="/listings", tags=["listings"])


# Listing 상태 머신 — 합법 전환만 허용. 같은 상태로 재설정도 OK.
# disputed 는 어디서든 진입 가능, closed 는 종착.
_FSM_TRANSITIONS: dict[str, set[str]] = {
    "inquiry": {"quoted", "negotiating", "disputed", "closed"},
    "quoted": {"negotiating", "agreed", "disputed", "closed"},
    "negotiating": {"quoted", "agreed", "disputed", "closed"},
    "agreed": {"documenting", "disputed", "closed"},
    "documenting": {"shipping", "disputed", "closed"},
    "shipping": {"in_transit", "arrived", "disputed"},
    "in_transit": {"arrived", "disputed"},
    "arrived": {"cleared", "disputed"},
    "cleared": {"delivered", "disputed"},
    "delivered": {"closed", "disputed"},
    "disputed": {"closed", "agreed"},  # 분쟁 해결 후 재합의 가능
    "closed": set(),  # terminal
}


def _validate_status_transition(current: str, new: str) -> None:
    if new == current:
        return
    valid = _FSM_TRANSITIONS.get(current, set())
    if new not in valid:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"invalid status transition: {current!r} → {new!r}. "
            f"Allowed from {current!r}: {sorted(valid) or 'terminal'}",
        )


# ── /import-check 전용 (DB 저장 없는 평가) 스키마 ─────────────
class _VehicleInputForCheck(BaseModel):
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
    body_type: str | None = None
    fuel_type: str | None = None
    engine_cc: int | None = None
    transmission: str | None = None
    steering: str | None = None
    mileage_km: int | None = None
    color_exterior: str | None = None
    list_price_usd: float | None = None
    manufacture_date: date | None = None
    registration_date: date | None = None


class _BuyerInputForCheck(BaseModel):
    company_name: str | None = None
    contact_person: str | None = None
    country_code: str = Field(min_length=2, max_length=2)
    tax_id: str | None = None
    total_orders: int = 0
    sanctions_status: str = "unchecked"


class ImportCheckRequest(BaseModel):
    vehicle: _VehicleInputForCheck
    destination_country: str = Field(min_length=2, max_length=2)
    buyer: _BuyerInputForCheck | None = None
    granted_flags: list[str] = Field(default_factory=list)
    today: date | None = None


class ImportCheckResponse(BaseModel):
    can_import: bool
    rule_check: dict[str, Any]
    compliance: dict[str, Any] | None = None


# ── Listing CRUD 스키마 ────────────────────────────────────────
class ListingCreate(BaseModel):
    vehicle_id: uuid.UUID
    buyer_id: uuid.UUID
    destination_country: str = Field(min_length=2, max_length=2)

    agreed_price_usd: float | None = None
    incoterm: str | None = Field(default=None, description="CIF/FOB/CFR/EXW")
    port_of_loading: str | None = None
    port_of_discharge: str | None = None
    payment_terms: str | None = None
    shipping_method: str | None = Field(default=None, description="container/roro/bulk")
    notes: str | None = None
    auto_import_check: bool = True


class ListingUpdate(BaseModel):
    buyer_id: uuid.UUID | None = None
    destination_country: str | None = Field(default=None, min_length=2, max_length=2)
    agreed_price_usd: float | None = None
    incoterm: str | None = None
    port_of_loading: str | None = None
    port_of_discharge: str | None = None
    payment_terms: str | None = None
    shipping_method: str | None = None
    status: str | None = Field(
        default=None,
        description=(
            "inquiry/quoted/negotiating/agreed/documenting/shipping/"
            "in_transit/arrived/cleared/delivered/disputed/closed"
        ),
    )
    notes: str | None = None


class ListingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    vehicle_id: uuid.UUID
    buyer_id: uuid.UUID | None
    destination_country: str | None

    can_import: bool | None
    import_check_json: dict[str, Any]

    agreed_price_usd: float | None
    incoterm: str | None
    port_of_loading: str | None
    port_of_discharge: str | None
    payment_terms: str | None
    shipping_method: str | None

    status: str
    notes: str | None


# ── 라우트: CRUD ───────────────────────────────────────────────
@router.post("", response_model=ListingOut, status_code=status.HTTP_201_CREATED)
def create_listing(
    payload: ListingCreate,
    db: Annotated[Session, Depends(get_db)],
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
) -> Listing:
    vehicle = db.get(Vehicle, payload.vehicle_id)
    if vehicle is None or vehicle.user_id != user_id:
        raise HTTPException(404, f"vehicle {payload.vehicle_id} not found")

    buyer = db.get(Buyer, payload.buyer_id)
    if buyer is None or buyer.user_id != user_id:
        raise HTTPException(404, f"buyer {payload.buyer_id} not found")

    code = payload.destination_country.upper()
    country = _load_country(db, code)

    listing = Listing(
        user_id=user_id,
        vehicle_id=vehicle.id,
        buyer_id=buyer.id,
        destination_country=code,
        agreed_price_usd=payload.agreed_price_usd,
        incoterm=payload.incoterm,
        port_of_loading=payload.port_of_loading,
        port_of_discharge=payload.port_of_discharge,
        payment_terms=payload.payment_terms,
        shipping_method=payload.shipping_method,
        notes=payload.notes,
        status="inquiry",
        inquiry_at=datetime.now(timezone.utc),
    )

    if payload.auto_import_check:
        try:
            result = evaluate(vehicle, country, rules=country.rules, buyer=buyer)
        except RuleEngineError as e:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(e)) from e
        listing.can_import = result.can_import
        listing.import_check_json = result.to_dict()

    db.add(listing)
    db.commit()
    db.refresh(listing)
    return listing


@router.get("", response_model=list[ListingOut])
def list_listings(
    db: Annotated[Session, Depends(get_db)],
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    status_filter: str | None = Query(None, alias="status"),
    skip: int = 0,
    limit: int = Query(50, le=200),
) -> list[Listing]:
    stmt = (
        select(Listing)
        .where(Listing.user_id == user_id)
        .order_by(Listing.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    if status_filter:
        stmt = stmt.where(Listing.status == status_filter)
    return list(db.execute(stmt).scalars())


# ── /import-check (literal path before /{id} wildcards) ────────
@router.post(
    "/import-check",
    response_model=ImportCheckResponse,
    summary="통관 + 컴플라이언스 사전 체크 (DB 저장 X)",
    description=(
        "등록 전 빠른 평가용. 차량 + (선택) 바이어 + 도착국 → 통관·컴플라이언스 통합 판정.\n"
        "실제 거래 등록은 POST /api/listings 사용 (vehicle_id × buyer_id 가 DB 에 있어야 함)."
    ),
)
def import_check(
    payload: ImportCheckRequest,
    db: Annotated[Session, Depends(get_db)],
) -> ImportCheckResponse:
    code = payload.destination_country.upper()
    country = _load_country(db, code)

    vehicle = _payload_to_vehicle(payload.vehicle)
    buyer = _payload_to_buyer(payload.buyer)

    try:
        rule_result = evaluate(
            vehicle, country, rules=country.rules,
            buyer=buyer, today=payload.today, granted_flags=set(payload.granted_flags),
        )
    except RuleEngineError as e:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(e)) from e
    compliance_dict = None
    if buyer is not None:
        compliance_dict = compliance.check(buyer, vehicle).to_dict()

    return ImportCheckResponse(
        can_import=rule_result.can_import,
        rule_check=rule_result.to_dict(),
        compliance=compliance_dict,
    )


@router.get("/{listing_id}", response_model=ListingOut)
def get_listing(
    listing_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
) -> Listing:
    return _get_owned(db, listing_id, user_id)


@router.patch("/{listing_id}", response_model=ListingOut)
def update_listing(
    listing_id: uuid.UUID,
    payload: ListingUpdate,
    db: Annotated[Session, Depends(get_db)],
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
) -> Listing:
    listing = _get_owned(db, listing_id, user_id)
    update_data = payload.model_dump(exclude_unset=True)

    if "destination_country" in update_data and update_data["destination_country"]:
        update_data["destination_country"] = update_data["destination_country"].upper()

    # 상태 전환 검증 + 타임스탬프 자동 기록
    if "status" in update_data:
        new_status = update_data["status"]
        _validate_status_transition(listing.status, new_status)
        now = datetime.now(timezone.utc)
        if new_status == "quoted" and listing.quoted_at is None:
            listing.quoted_at = now
        elif new_status == "agreed" and listing.agreed_at is None:
            listing.agreed_at = now
        elif new_status in ("shipping", "in_transit") and listing.shipped_at is None:
            listing.shipped_at = now
        elif new_status == "delivered" and listing.delivered_at is None:
            listing.delivered_at = now

    for key, value in update_data.items():
        setattr(listing, key, value)
    db.commit()
    db.refresh(listing)
    return listing


# ── /listings/{id}/mail-draft ──────────────────────────────────
class MailDraftRequest(BaseModel):
    scenario: str = Field(
        description="inquiry / quote / negotiate / shipping / dispute",
        examples=["quote"],
    )
    language: str | None = Field(
        default=None,
        description="en / es / ar / ru / fr — None 이면 buyer.preferred_language 또는 country.primary_language 사용",
    )
    extra_context: str = Field(default="", description="LLM 에 추가로 전달할 맥락 (선택)")


class MailDraftResponse(BaseModel):
    subject: str
    body: str
    scenario: str
    language: str
    provider: str
    model: str
    message_id: uuid.UUID


@router.post(
    "/{listing_id}/mail-draft",
    response_model=MailDraftResponse,
    summary="LLM 다국어 격식 메일 자동 생성 (시연 시나리오 3)",
)
def draft_mail(
    listing_id: uuid.UUID,
    payload: MailDraftRequest,
    db: Annotated[Session, Depends(get_db)],
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
) -> MailDraftResponse:
    listing = _get_owned(db, listing_id, user_id)

    if listing.buyer_id is None or listing.destination_country is None:
        raise HTTPException(400, "listing must have buyer_id and destination_country set")

    vehicle = db.get(Vehicle, listing.vehicle_id)
    buyer = db.get(Buyer, listing.buyer_id)
    country = _load_country(db, listing.destination_country)

    # 언어 자동 감지: 명시 > 바이어 선호 > 국가 공식 > 국가 비즈니스 > en
    # findings #026 — 28국 중 12국 (KZ kk, AZ az, KH km, BD bn, KG ky, MY ms,
    # MM my, PH tl, LK si, TZ sw, TH th, VN vi) 의 primary_language 가 LLM
    # 미지원. business_language 거치는 fallback 추가로 'kk' 같은 raw 코드가
    # Gemini 에 직행하는 것 방지.
    _SUPPORTED_LLM_LANGS = {"en", "es", "ar", "ru", "fr", "ko"}

    def _supported(lang: str | None) -> str | None:
        return lang if lang in _SUPPORTED_LLM_LANGS else None

    language = (
        _supported(payload.language)
        or _supported(buyer.preferred_language if buyer else None)
        or _supported(country.primary_language)
        or _supported(country.business_language)
        or "en"
    )

    writer = MailWriter()  # uses LLM_PROVIDER env var
    try:
        draft = writer.draft(
            MailRequest(
                scenario=payload.scenario,
                language=language,
                vehicle=vehicle,
                buyer=buyer,
                country=country,
                rules=country.rules,
                extra_context=payload.extra_context,
            )
        )
    except MailDraftParseError as e:
        # LLM 이 JSON 형식 어김 — 쓰레기 메일 저장 X, 502 반환
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            f"LLM provider returned malformed response. Try again or switch provider. ({e})",
        ) from e
    except HTTPException:
        raise
    except Exception as e:
        # Gemini 일시 장애 (429 quota / 503 / network timeout) — 503 + 명확한 메시지
        logger.exception("LLM provider error during mail-draft")
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            (
                f"LLM provider unavailable ({type(e).__name__}). "
                "Try again in a moment or switch LLM_PROVIDER in backend/.env."
            ),
        ) from e

    message = Message(
        listing_id=listing.id,
        buyer_id=listing.buyer_id,
        channel="email",
        direction="outbound",
        scenario=payload.scenario,
        language=language,
        content_text=f"Subject: {draft.subject}\n\n{draft.body}",
        ai_generated=True,
        ai_model=draft.model,
        ai_prompt_id=f"{payload.scenario}_{language}",
    )
    db.add(message)
    db.commit()
    db.refresh(message)

    return MailDraftResponse(
        subject=draft.subject,
        body=draft.body,
        scenario=payload.scenario,
        language=language,
        provider=draft.provider,
        model=draft.model,
        message_id=message.id,
    )


# ── /listings/{id}/documents (시연 시나리오 4) ──────────────────
class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    doc_type: str
    pdf_url: str | None
    version: int


class DocumentsGenerateResponse(BaseModel):
    listing_id: uuid.UUID
    documents: list[DocumentOut]


@router.post(
    "/{listing_id}/documents",
    response_model=DocumentsGenerateResponse,
    summary="4종 수출 서류 PDF 자동 생성 (시연 시나리오 4)",
)
def generate_documents(
    listing_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
) -> DocumentsGenerateResponse:
    """4종 PDF (Invoice/PL/SI/CO) 를 동시 생성 → DB Document 행 + 파일 시스템 저장.

    원자성·동시성 보장:
      1. SELECT FOR UPDATE 로 해당 listing 행 락 → 동시 호출 직렬화
      2. .tmp 파일로 먼저 작성 (Playwright 동안 기존 PDF 보존)
      3. 모든 .tmp 가 정상 작성된 후 단일 디렉터리 내 atomic rename
      4. DB 트랜잭션은 마지막에 한 번 commit
    Playwright 실패 → 기존 파일·DB 행 모두 그대로.
    """
    # 1. Row lock — 동시 /documents 호출 직렬화
    listing = db.execute(
        select(Listing)
        .where(Listing.id == listing_id, Listing.user_id == user_id)
        .with_for_update()
    ).scalar_one_or_none()
    if listing is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"listing {listing_id} not found")
    if listing.buyer_id is None or listing.destination_country is None:
        raise HTTPException(400, "listing must have buyer_id and destination_country set")

    user = db.get(User, user_id)
    vehicle = db.get(Vehicle, listing.vehicle_id)
    buyer = db.get(Buyer, listing.buyer_id)
    doc_input = _build_document_input(user, vehicle, buyer, listing)

    # Path traversal 방어 (defense-in-depth — listing_id 가 UUID 라 이론상 안전하지만)
    base = GENERATED_PDFS_DIR.resolve()
    out_dir = (base / str(listing.id)).resolve()
    if not out_dir.is_relative_to(base):
        raise HTTPException(500, "computed path escapes generated_pdfs root")

    # 2. PDF 생성 — 실패해도 기존 파일·DB 행은 그대로 유지됨
    pdfs = generate_all(doc_input)

    # 3. .tmp 파일로 모두 작성
    out_dir.mkdir(parents=True, exist_ok=True)
    tmp_pairs: list[tuple[str, Path, Path]] = []  # (doc_type, tmp_path, final_path)
    for doc_type, pdf_bytes in pdfs.items():
        tmp_path = out_dir / f"{doc_type}.pdf.tmp"
        final_path = out_dir / f"{doc_type}.pdf"
        tmp_path.write_bytes(pdf_bytes)
        tmp_pairs.append((doc_type, tmp_path, final_path))

    # 4. Atomic swap (row lock 보유 중이라 unlink/rename 사이 race 없음)
    for _, tmp_path, final_path in tmp_pairs:
        if final_path.exists():
            final_path.unlink()
        tmp_path.rename(final_path)

    # 5. DB 트랜잭션 — 기존 Document 행 삭제 + 새 행 insert (한 transaction)
    db.execute(delete(Document).where(Document.listing_id == listing.id))
    documents: list[Document] = []
    for doc_type, _, _ in tmp_pairs:
        rel_url = f"/api/listings/{listing.id}/documents/{doc_type}.pdf"
        doc = Document(
            listing_id=listing.id,
            doc_type=doc_type,
            language="en",
            pdf_url=rel_url,
            data_json={"invoice_no": doc_input.invoice_no},
            generated_by="ai",
            version=1,
        )
        db.add(doc)
        documents.append(doc)

    db.commit()
    for d in documents:
        db.refresh(d)
    return DocumentsGenerateResponse(listing_id=listing.id, documents=documents)


@router.get(
    "/{listing_id}/documents/{doc_type}.pdf",
    response_class=FileResponse,
    summary="생성된 PDF 다운로드",
)
def serve_document(
    listing_id: uuid.UUID,
    doc_type: str,
    db: Annotated[Session, Depends(get_db)],
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
) -> FileResponse:
    _get_owned(db, listing_id, user_id)
    if doc_type not in {"invoice", "packing_list", "shipping_instruction", "co_application"}:
        raise HTTPException(400, f"unknown doc_type: {doc_type}")

    base = GENERATED_PDFS_DIR.resolve()
    path = (base / str(listing_id) / f"{doc_type}.pdf").resolve()
    # defense-in-depth: 결과 경로가 generated_pdfs 안에 있는지 확인
    if not path.is_relative_to(base):
        raise HTTPException(403, "path outside allowed directory")
    if not path.exists():
        raise HTTPException(404, "PDF not generated yet — POST /documents first")
    return FileResponse(
        path,
        media_type="application/pdf",
        filename=f"{doc_type}_{str(listing_id)[:8]}.pdf",
    )


@router.get("/{listing_id}/documents", response_model=list[DocumentOut])
def list_documents(
    listing_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
) -> list[Document]:
    _get_owned(db, listing_id, user_id)
    return list(db.execute(
        select(Document).where(Document.listing_id == listing_id).order_by(Document.doc_type)
    ).scalars())


@router.delete("/{listing_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_listing(
    listing_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
) -> Response:
    listing = _get_owned(db, listing_id, user_id)
    db.delete(listing)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ── helpers ────────────────────────────────────────────────────
def _get_owned(db: Session, listing_id: uuid.UUID, user_id: uuid.UUID) -> Listing:
    listing = db.get(Listing, listing_id)
    if listing is None or listing.user_id != user_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"listing {listing_id} not found")
    return listing


def _load_country(db: Session, code: str) -> Country:
    country = db.execute(
        select(Country)
        .where(Country.code == code)
        .options(selectinload(Country.rules))
    ).scalar_one_or_none()
    if country is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            f"country {code!r} not in import_rules. Currently seeded: DO/KE/KG/LY/SY.",
        )
    return country


def _payload_to_vehicle(v: _VehicleInputForCheck) -> Vehicle:
    return Vehicle(
        vin=v.vin, make=v.make, model=v.model, year=v.year,
        body_type=v.body_type, fuel_type=v.fuel_type, engine_cc=v.engine_cc,
        transmission=v.transmission, steering=v.steering,
        mileage_km=v.mileage_km, color_exterior=v.color_exterior,
        list_price_usd=v.list_price_usd,
        manufacture_date=v.manufacture_date, registration_date=v.registration_date,
    )


def _build_document_input(
    user: User, vehicle: Vehicle, buyer: Buyer, listing: Listing
) -> DocumentInput:
    """ORM 4개 → DocumentInput dataclass."""
    invoice_no = f"INV-{listing.created_at.strftime('%Y%m%d')}-{str(listing.id)[:8].upper()}"
    return DocumentInput(
        invoice_no=invoice_no,
        invoice_date=date.today(),
        shipper_name=user.company_name or "Korean Used-Car Exporter",
        shipper_address=user.address or "Songdo, Incheon, Republic of Korea",
        shipper_phone=user.phone or "+82-32-000-0000",
        shipper_business_no=user.business_no or "000-00-00000",
        consignee_name=buyer.company_name or "(buyer name TBA)",
        consignee_contact=buyer.contact_person or "",
        consignee_address=buyer.address or "",
        consignee_country=buyer.country_code,
        consignee_tax_id=buyer.tax_id or "",
        make=vehicle.make or "?",
        model=vehicle.model or "?",
        year=vehicle.year or 0,
        vin=vehicle.vin or "?",
        body_type=vehicle.body_type or "passenger",
        fuel_type=vehicle.fuel_type or "Gasoline",
        engine_cc=vehicle.engine_cc or 0,
        color=vehicle.color_exterior or "?",
        mileage_km=vehicle.mileage_km or 0,
        # findings #034 — vehicle.hs_code 비어있으면 자동 분류 (8703.23 hard-default 대신)
        hs_code=vehicle.hs_code or hs_classifier.classify(
            body_type=vehicle.body_type,
            fuel_type=vehicle.fuel_type,
            engine_cc=vehicle.engine_cc,
        ).hs_code,
        net_weight_kg=1480,  # PoC: 차량 평균. 실제는 Vehicle 에 컬럼 추가
        gross_weight_kg=1620,
        unit_price_usd=float(listing.agreed_price_usd or vehicle.list_price_usd or 0),
        currency="USD",
        incoterm=listing.incoterm or "CIF",
        payment_terms=listing.payment_terms or "T/T 100% advance",
        port_of_loading=listing.port_of_loading or user.port_of_loading or "Incheon, Korea",
        port_of_discharge=listing.port_of_discharge or "",
        final_destination=buyer.country_code,
        shipping_method=listing.shipping_method or "Container",
        bank_name="KEB Hana Bank, Songdo Branch",
        bank_swift="KOEXKRSE",
        bank_account="123-456789-01-001",
    )


def _payload_to_buyer(b: _BuyerInputForCheck | None) -> Buyer | None:
    if b is None:
        return None
    return Buyer(
        company_name=b.company_name, contact_person=b.contact_person,
        country_code=b.country_code.upper(),
        tax_id=b.tax_id, total_orders=b.total_orders,
        sanctions_status=b.sanctions_status,
    )
