import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Shipment(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """선적 추적 — listing 1:1."""

    __tablename__ = "shipments"

    listing_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("listings.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )

    bl_number: Mapped[str | None] = mapped_column(String(64))
    vessel_name: Mapped[str | None] = mapped_column(String(128))
    voyage_no: Mapped[str | None] = mapped_column(String(64))
    container_no: Mapped[str | None] = mapped_column(String(32))  # RoRo면 NULL
    seal_no: Mapped[str | None] = mapped_column(String(32))

    port_of_loading: Mapped[str | None] = mapped_column(String(64))
    port_of_discharge: Mapped[str | None] = mapped_column(String(64))
    etd: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    eta: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    ata: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # [{event: loaded, at: ts, location: ...}, ...]
    milestones_json: Mapped[list] = mapped_column(JSONB, default=list)

    last_notified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    next_notification_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    listing: Mapped["Listing"] = relationship(back_populates="shipment")  # noqa: F821
