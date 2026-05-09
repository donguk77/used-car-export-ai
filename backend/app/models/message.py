import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDPrimaryKeyMixin


class Message(Base, UUIDPrimaryKeyMixin):
    """AI 가 생성하거나 수신한 메일·WhatsApp·SMS 로그."""

    __tablename__ = "messages"

    listing_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("listings.id", ondelete="SET NULL"),
        index=True,
    )
    buyer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("buyers.id", ondelete="SET NULL"),
        index=True,
    )

    channel: Mapped[str] = mapped_column(String(16))  # email/whatsapp/sms
    direction: Mapped[str] = mapped_column(String(16))  # outbound/inbound
    scenario: Mapped[str | None] = mapped_column(String(32))
    # inquiry/quote/negotiate/shipping/dispute
    language: Mapped[str | None] = mapped_column(String(8))
    content_text: Mapped[str | None] = mapped_column(Text)

    ai_generated: Mapped[bool] = mapped_column(Boolean, default=False)
    ai_model: Mapped[str | None] = mapped_column(String(64))
    ai_prompt_id: Mapped[str | None] = mapped_column(String(64))

    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    listing: Mapped["Listing | None"] = relationship(back_populates="messages")  # noqa: F821
