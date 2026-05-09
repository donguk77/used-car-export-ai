"""/api/listings — 거래(매물×바이어×도착국) CRUD + 통관 판정.

POST /api/listings              — 거래 생성 (자동 import-check 실행)
GET  /api/listings              — 목록 (status 필터)
POST /api/listings/import-check — DB 저장 없이 평가만 (시연 1단계용)
GET  /api/listings/{id}
PATCH /api/listings/{id}        — 가격·상태 등 갱신 (status FSM)
DELETE /api/listings/{id}
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user_id
from app.core import compliance
from app.core.rule_engine import ImportCheckResult, evaluate
from app.db import get_db
from app.models import Buyer, Country, Document, Listing, Message, User, Vehicle
from app.services.document_writer import DocumentInput, generate_all
from app.services.mail_writer import MailRequest, MailWriter

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
GENERATED_PDFS_DIR = PROJECT_ROOT / "generated_pdfs"

router = APIRouter(prefix="/listings", tags=["listings"])


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
        result = evaluate(vehicle, country, rules=country.rules, buyer=buyer)
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

    rule_result = evaluate(
        vehicle, country, rules=country.rules,
        buyer=buyer, today=payload.today, granted_flags=set(payload.granted_flags),
    )
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

    # 상태 전환 시 타임스탬프 자동 기록
    if "status" in update_data:
        new_status = update_data["status"]
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

    # 언어 자동 감지: 명시 > 바이어 선호 > 국가 공식 > en
    language = (
        payload.language
        or (buyer.preferred_language if buyer else None)
        or country.primary_language
        or "en"
    )

    writer = MailWriter()  # uses LLM_PROVIDER env var
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

    멱등: 다시 호출하면 기존 PDF·Document 행을 새로 덮어씀.
    """
    listing = _get_owned(db, listing_id, user_id)
    if listing.buyer_id is None or listing.destination_country is None:
        raise HTTPException(400, "listing must have buyer_id and destination_country set")

    user = db.get(User, user_id)
    vehicle = db.get(Vehicle, listing.vehicle_id)
    buyer = db.get(Buyer, listing.buyer_id)

    doc_input = _build_document_input(user, vehicle, buyer, listing)

    # 1. 기존 Document 행·파일 삭제 (멱등성)
    out_dir = GENERATED_PDFS_DIR / str(listing.id)
    db.execute(delete(Document).where(Document.listing_id == listing.id))
    if out_dir.exists():
        for f in out_dir.glob("*.pdf"):
            f.unlink()

    # 2. PDF 생성 (Playwright로 4장 한 번에)
    pdfs = generate_all(doc_input)

    # 3. 파일 저장 + Document 행 insert
    out_dir.mkdir(parents=True, exist_ok=True)
    documents: list[Document] = []
    for doc_type, pdf_bytes in pdfs.items():
        path = out_dir / f"{doc_type}.pdf"
        path.write_bytes(pdf_bytes)
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
    path = GENERATED_PDFS_DIR / str(listing_id) / f"{doc_type}.pdf"
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
        hs_code=vehicle.hs_code or "8703.23",
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
