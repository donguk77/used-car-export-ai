import uuid
from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Country(Base, TimestampMixin):
    """ISO 3166-1 country master data."""

    __tablename__ = "countries"

    code: Mapped[str] = mapped_column(String(2), primary_key=True)
    name_en: Mapped[str] = mapped_column(String(128), nullable=False)
    name_ko: Mapped[str | None] = mapped_column(String(128))
    name_local: Mapped[str | None] = mapped_column(String(128))
    region: Mapped[str | None] = mapped_column(String(32))

    # 비즈니스 메타
    primary_language: Mapped[str | None] = mapped_column(String(8))
    business_language: Mapped[str | None] = mapped_column(String(8))
    steering: Mapped[str | None] = mapped_column(String(8))  # LHD/RHD/MIXED

    # 통상 위험
    is_high_risk: Mapped[bool] = mapped_column(Boolean, default=False)
    is_russia_proxy_risk: Mapped[bool] = mapped_column(Boolean, default=False)
    is_sanctioned: Mapped[bool] = mapped_column(Boolean, default=False)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)

    # 항구·통관
    main_ports_json: Mapped[list] = mapped_column(JSONB, default=list)
    pre_registration_system: Mapped[str | None] = mapped_column(String(32))
    consular_legalization: Mapped[bool] = mapped_column(Boolean, default=False)

    notes: Mapped[str | None] = mapped_column(Text)

    rules: Mapped[list["ImportRule"]] = relationship(
        back_populates="country",
        cascade="all, delete-orphan",
    )


class ImportRule(Base, UUIDPrimaryKeyMixin):
    """국가별 수입 규제 룰 — 차종별 / 시기별 효력 분리.

    docs/competitor_analysis_and_features.md §5.3 의 YAML 이 시드 데이터.
    """

    __tablename__ = "import_rules"

    country_code: Mapped[str] = mapped_column(
        String(2),
        ForeignKey("countries.code", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    # 차종 필터 (NULL = 전체)
    body_type_filter: Mapped[str | None] = mapped_column(String(32))

    # 연식 룰
    age_limit_years: Mapped[int | None] = mapped_column(Integer)
    age_basis: Mapped[str | None] = mapped_column(String(32))  # manufacture_year/first_registration
    age_effective_from: Mapped[date | None] = mapped_column(Date)  # 케냐 2026.1.1
    registration_after_date: Mapped[date | None] = mapped_column(Date)  # 케냐: 2019.1.1+

    # 기본 룰
    steering_required: Mapped[str | None] = mapped_column(String(16))  # LHD_only/RHD_only/MIXED
    max_engine_cc: Mapped[int | None] = mapped_column(Integer)
    max_cylinders: Mapped[int | None] = mapped_column(Integer)
    fuel_blocked_json: Mapped[list] = mapped_column(JSONB, default=list)

    # 검사·서류
    psi_required: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    doc_translation_lang: Mapped[str | None] = mapped_column(String(8))
    consular_required: Mapped[bool] = mapped_column(Boolean, default=False)
    pre_registration: Mapped[str | None] = mapped_column(String(32))

    # 컴플라이언스
    blocked_conditions_json: Mapped[list] = mapped_column(JSONB, default=list)
    required_documents_json: Mapped[list] = mapped_column(JSONB, default=list)

    # 메타
    effective_from: Mapped[date | None] = mapped_column(Date)
    effective_to: Mapped[date | None] = mapped_column(Date)
    source_url: Mapped[str | None] = mapped_column(String(512))
    last_verified_at: Mapped[date | None] = mapped_column(Date)
    notes: Mapped[str | None] = mapped_column(Text)

    country: Mapped[Country] = relationship(back_populates="rules")
