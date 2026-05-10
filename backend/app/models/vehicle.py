import uuid
from datetime import date

from sqlalchemy import BigInteger, Boolean, Date, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Vehicle(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "vehicles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    # 식별
    vin: Mapped[str | None] = mapped_column(String(17), unique=True, index=True)
    registration_no: Mapped[str | None] = mapped_column(String(32))
    registration_date: Mapped[date | None] = mapped_column(Date)
    manufacture_date: Mapped[date | None] = mapped_column(Date)

    # 사양 (NHTSA vPIC 자동 디코딩)
    make: Mapped[str | None] = mapped_column(String(64))
    model: Mapped[str | None] = mapped_column(String(64))
    year: Mapped[int | None] = mapped_column(Integer)
    trim: Mapped[str | None] = mapped_column(String(64))
    body_type: Mapped[str | None] = mapped_column(String(32))  # Sedan/SUV/Pickup/Van/Bus/Truck
    fuel_type: Mapped[str | None] = mapped_column(String(16))  # Gasoline/Diesel/LPG/Hybrid/EV
    engine_cc: Mapped[int | None] = mapped_column(Integer)
    transmission: Mapped[str | None] = mapped_column(String(8))  # A/T, M/T
    drivetrain: Mapped[str | None] = mapped_column(String(8))  # FWD/RWD/AWD/4WD
    steering: Mapped[str | None] = mapped_column(String(8))  # LHD/RHD
    seats: Mapped[int | None] = mapped_column(Integer)
    color_exterior: Mapped[str | None] = mapped_column(String(32))
    color_interior: Mapped[str | None] = mapped_column(String(32))
    mileage_km: Mapped[int | None] = mapped_column(Integer)

    # 상태
    options_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    panel_status_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    has_accident: Mapped[bool] = mapped_column(Boolean, default=False)
    accident_history: Mapped[str | None] = mapped_column(Text)
    inspection_grade: Mapped[str | None] = mapped_column(String(16))

    # AI 생성 이미지 URL (frontend/public/vehicle-images/{id}.png 같은 상대경로)
    image_url: Mapped[str | None] = mapped_column(String(512))

    # 가격·재고
    purchase_price_krw: Mapped[int | None] = mapped_column(BigInteger)
    list_price_usd: Mapped[float | None] = mapped_column(Numeric(10, 2))
    status: Mapped[str] = mapped_column(String(16), default="available", index=True)
    port_of_loading: Mapped[str | None] = mapped_column(String(64))

    # HS Code (자동 분류)
    hs_code: Mapped[str | None] = mapped_column(String(16))

    images: Mapped[list["VehicleImage"]] = relationship(
        back_populates="vehicle",
        cascade="all, delete-orphan",
    )
    history_records: Mapped[list["VehicleHistoryRecord"]] = relationship(
        back_populates="vehicle",
        cascade="all, delete-orphan",
    )


class VehicleImage(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "vehicle_images"

    vehicle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vehicles.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    url: Mapped[str] = mapped_column(String(512), nullable=False)
    type: Mapped[str | None] = mapped_column(String(32))  # exterior_front / interior / engine ...
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    uploaded_at: Mapped[date | None] = mapped_column(Date)

    vehicle: Mapped[Vehicle] = relationship(back_populates="images")


class VehicleHistoryRecord(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "vehicle_history_records"

    vehicle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vehicles.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    source: Mapped[str] = mapped_column(String(32))  # carhistory / car365 / manual
    record_type: Mapped[str] = mapped_column(String(32))  # accident / inspection / repair / recall
    record_date: Mapped[date | None] = mapped_column(Date)
    details_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    pdf_url: Mapped[str | None] = mapped_column(String(512))

    vehicle: Mapped[Vehicle] = relationship(back_populates="history_records")
