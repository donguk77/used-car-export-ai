import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Listing(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """매물-바이어 매칭 단위. 거래 1건 = listing 1건."""

    __tablename__ = "listings"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    vehicle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vehicles.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    buyer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("buyers.id", ondelete="SET NULL"),
    )
    destination_country: Mapped[str | None] = mapped_column(
        String(2),
        ForeignKey("countries.code", ondelete="SET NULL"),
        index=True,
    )

    # 룰 엔진 결과
    can_import: Mapped[bool | None] = mapped_column(Boolean)
    import_check_json: Mapped[dict] = mapped_column(JSONB, default=dict)

    # 가격·조건
    agreed_price_usd: Mapped[float | None] = mapped_column(Numeric(10, 2))
    incoterm: Mapped[str | None] = mapped_column(String(8))  # CIF/FOB/CFR/EXW
    port_of_loading: Mapped[str | None] = mapped_column(String(64))
    port_of_discharge: Mapped[str | None] = mapped_column(String(64))
    payment_terms: Mapped[str | None] = mapped_column(String(64))
    shipping_method: Mapped[str | None] = mapped_column(String(16))  # container/roro/bulk

    # 상태 머신
    status: Mapped[str] = mapped_column(String(16), default="inquiry", index=True)
    # inquiry/quoted/negotiating/agreed/documenting/shipping/in_transit/
    # arrived/cleared/delivered/disputed/closed

    # 타임라인
    inquiry_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    quoted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    agreed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    shipped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    notes: Mapped[str | None] = mapped_column(Text)

    documents: Mapped[list["Document"]] = relationship(  # noqa: F821
        back_populates="listing",
        cascade="all, delete-orphan",
    )
    messages: Mapped[list["Message"]] = relationship(  # noqa: F821
        back_populates="listing",
        cascade="all, delete-orphan",
    )
    shipment: Mapped["Shipment | None"] = relationship(  # noqa: F821
        back_populates="listing",
        uselist=False,
        cascade="all, delete-orphan",
    )
