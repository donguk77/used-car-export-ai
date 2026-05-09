import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDPrimaryKeyMixin


class Document(Base, UUIDPrimaryKeyMixin):
    """자동 생성된 수출 서류 (invoice / packing_list / si / co_application / customs_package)."""

    __tablename__ = "documents"

    listing_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("listings.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    doc_type: Mapped[str] = mapped_column(String(32), nullable=False)
    language: Mapped[str] = mapped_column(String(16), default="en")  # "en" 또는 "en+es"
    data_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    pdf_url: Mapped[str | None] = mapped_column(String(512))

    generated_by: Mapped[str] = mapped_column(String(16), default="ai")
    version: Mapped[int] = mapped_column(Integer, default=1)

    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    listing: Mapped["Listing"] = relationship(back_populates="documents")  # noqa: F821
