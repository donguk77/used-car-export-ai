"""GET /api/dashboard/summary — UI 대시보드 한 번에 채울 데이터."""

from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id
from app.db import get_db
from app.models import Buyer, Listing, Vehicle

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


class DashboardCounts(BaseModel):
    vehicles_total: int
    vehicles_available: int
    buyers_total: int
    buyers_blocked: int
    buyers_warning: int
    listings_inquiry: int
    listings_in_progress: int  # quoted / negotiating / agreed / documenting
    listings_shipping: int  # shipping / in_transit / arrived / cleared
    listings_delivered: int


class RecentListing(BaseModel):
    id: uuid.UUID
    vehicle_label: str
    buyer_name: str | None
    destination_country: str | None
    status: str
    can_import: bool | None


class ComplianceAlert(BaseModel):
    buyer_id: uuid.UUID
    company_name: str | None
    country_code: str
    sanctions_status: str
    russia_proxy_risk_score: int | None


class DashboardSummary(BaseModel):
    counts: DashboardCounts
    recent_listings: list[RecentListing]
    compliance_alerts: list[ComplianceAlert]


@router.get("/summary", response_model=DashboardSummary)
def dashboard_summary(
    db: Annotated[Session, Depends(get_db)],
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
) -> DashboardSummary:
    counts = _counts(db, user_id)
    recent = _recent_listings(db, user_id)
    alerts = _compliance_alerts(db, user_id)
    return DashboardSummary(counts=counts, recent_listings=recent, compliance_alerts=alerts)


def _counts(db: Session, user_id: uuid.UUID) -> DashboardCounts:
    # Vehicles
    v_total = db.scalar(
        select(func.count()).select_from(Vehicle).where(Vehicle.user_id == user_id)
    )
    v_avail = db.scalar(
        select(func.count())
        .select_from(Vehicle)
        .where(Vehicle.user_id == user_id, Vehicle.status == "available")
    )

    # Buyers
    b_total = db.scalar(
        select(func.count()).select_from(Buyer).where(Buyer.user_id == user_id)
    )
    b_blocked = db.scalar(
        select(func.count())
        .select_from(Buyer)
        .where(Buyer.user_id == user_id, Buyer.sanctions_status == "blocked")
    )
    b_warning = db.scalar(
        select(func.count())
        .select_from(Buyer)
        .where(Buyer.user_id == user_id, Buyer.sanctions_status == "warning")
    )

    # Listings — group by status
    by_status: dict[str, int] = dict(
        db.execute(
            select(Listing.status, func.count())
            .where(Listing.user_id == user_id)
            .group_by(Listing.status)
        ).all()
    )

    in_progress = sum(by_status.get(s, 0) for s in ("quoted", "negotiating", "agreed", "documenting"))
    shipping = sum(by_status.get(s, 0) for s in ("shipping", "in_transit", "arrived", "cleared"))

    return DashboardCounts(
        vehicles_total=v_total or 0,
        vehicles_available=v_avail or 0,
        buyers_total=b_total or 0,
        buyers_blocked=b_blocked or 0,
        buyers_warning=b_warning or 0,
        listings_inquiry=by_status.get("inquiry", 0),
        listings_in_progress=in_progress,
        listings_shipping=shipping,
        listings_delivered=by_status.get("delivered", 0) + by_status.get("closed", 0),
    )


def _recent_listings(db: Session, user_id: uuid.UUID, limit: int = 5) -> list[RecentListing]:
    rows = db.execute(
        select(Listing, Vehicle, Buyer)
        .join(Vehicle, Listing.vehicle_id == Vehicle.id)
        .outerjoin(Buyer, Listing.buyer_id == Buyer.id)
        .where(Listing.user_id == user_id)
        .order_by(desc(Listing.created_at))
        .limit(limit)
    ).all()
    return [
        RecentListing(
            id=listing.id,
            vehicle_label=f"{v.make or '?'} {v.model or '?'} {v.year or ''}".strip(),
            buyer_name=b.company_name if b else None,
            destination_country=listing.destination_country,
            status=listing.status,
            can_import=listing.can_import,
        )
        for listing, v, b in rows
    ]


def _compliance_alerts(db: Session, user_id: uuid.UUID) -> list[ComplianceAlert]:
    rows = db.execute(
        select(Buyer)
        .where(
            Buyer.user_id == user_id,
            Buyer.sanctions_status.in_(("blocked", "warning")),
        )
        .order_by(desc(Buyer.created_at))
        .limit(10)
    ).scalars()
    return [
        ComplianceAlert(
            buyer_id=b.id,
            company_name=b.company_name,
            country_code=b.country_code,
            sanctions_status=b.sanctions_status,
            russia_proxy_risk_score=b.russia_proxy_risk_score,
        )
        for b in rows
    ]
