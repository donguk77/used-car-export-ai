import uuid
from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Buyer(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "buyers"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    # 기본
    buyer_type: Mapped[str | None] = mapped_column(String(16))  # Dealer/Importer/Individual/Re-exporter
    company_name: Mapped[str | None] = mapped_column(String(255))
    contact_person: Mapped[str | None] = mapped_column(String(128))
    country_code: Mapped[str] = mapped_column(String(2), index=True, nullable=False)
    city: Mapped[str | None] = mapped_column(String(128))
    address: Mapped[str | None] = mapped_column(Text)

    # 연락
    phone: Mapped[str | None] = mapped_column(String(32))
    whatsapp: Mapped[str | None] = mapped_column(String(32))
    email: Mapped[str | None] = mapped_column(String(255))
    wechat: Mapped[str | None] = mapped_column(String(64))

    # 신원
    business_license: Mapped[str | None] = mapped_column(String(64))
    tax_id: Mapped[str | None] = mapped_column(String(64))

    # 선호도
    preferred_language: Mapped[str | None] = mapped_column(String(8))
    preferred_currency: Mapped[str | None] = mapped_column(String(8))
    preferred_payment: Mapped[str | None] = mapped_column(String(32))
    preferred_port: Mapped[str | None] = mapped_column(String(64))
    preferred_incoterm: Mapped[str | None] = mapped_column(String(8))
    target_models_json: Mapped[list] = mapped_column(JSONB, default=list)
    target_year_min: Mapped[int | None] = mapped_column(Integer)
    target_price_max_usd: Mapped[float | None] = mapped_column(Numeric(10, 2))
    target_mileage_max_km: Mapped[int | None] = mapped_column(Integer)
    volume_per_month: Mapped[str | None] = mapped_column(String(32))

    # 거래 통계
    total_orders: Mapped[int] = mapped_column(Integer, default=0)
    total_value_usd: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    last_order_date: Mapped[date | None] = mapped_column(Date)
    payment_reliability_score: Mapped[int | None] = mapped_column(Integer)
    dispute_count: Mapped[int] = mapped_column(Integer, default=0)

    # 컴플라이언스 (요약)
    kyc_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    sanctions_status: Mapped[str] = mapped_column(String(16), default="unchecked", index=True)
    russia_proxy_risk_score: Mapped[int | None] = mapped_column(Integer)
    final_destination_declared: Mapped[str | None] = mapped_column(String(2))

    compliance_checks: Mapped[list["ComplianceCheck"]] = relationship(
        back_populates="buyer",
        cascade="all, delete-orphan",
    )


class ComplianceCheck(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "compliance_checks"

    buyer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("buyers.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    vehicle_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vehicles.id", ondelete="SET NULL"),
    )
    checked_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
    )

    check_type: Mapped[str] = mapped_column(String(32))  # yestrade/ofac/eu_sanctions/russia_proxy
    result: Mapped[str] = mapped_column(String(16))  # clean/flagged/blocked
    flags_json: Mapped[list] = mapped_column(JSONB, default=list)
    raw_response: Mapped[dict] = mapped_column(JSONB, default=dict)

    checked_at: Mapped[date] = mapped_column(Date, nullable=False)

    buyer: Mapped[Buyer] = relationship(back_populates="compliance_checks")
