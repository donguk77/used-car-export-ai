"""MCP Tool dispatcher — tool name + input → ToolResult.

채팅 에이전트 + 외부 MCP client 모두에서 호출되는 단일 진입점.
권한 체크 (user_id) + DB session 관리 일원화.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, selectinload

from app.core.compliance import check as compliance_check
from app.core.rule_engine import evaluate as evaluate_import_rules
from app.mcp.tools import ToolResult, get_tool, validate_arguments
from app.models import Buyer, Country, Listing, Vehicle

logger = logging.getLogger(__name__)


class MCPDispatcher:
    """MCP tool 실행기. 호출당 새로 생성 (db session + user 컨텍스트 보유)."""

    def __init__(self, db: Session, user_id: uuid.UUID):
        self.db = db
        self.user_id = user_id

    def call(self, name: str, arguments: dict[str, Any] | None) -> ToolResult:
        """tool name + arguments → ToolResult. 알 수 없는 tool 은 ok=False."""
        tool = get_tool(name)
        if tool is None:
            return ToolResult(ok=False, data=None, error=f"unknown tool: {name!r}")

        args = arguments or {}

        # Fix #6 — input_schema 검증 (외부 MCP client 가 잘못된 payload 보낼 때 catch).
        validation_error = validate_arguments(tool, args)
        if validation_error:
            return ToolResult(
                ok=False, data=None,
                error=f"input validation failed: {validation_error}",
            )

        handler = getattr(self, f"_h_{tool.handler_key}", None)
        if handler is None:
            return ToolResult(ok=False, data=None, error=f"no handler for {tool.handler_key!r}")

        try:
            return handler(args)
        except SQLAlchemyError as e:
            # Fix #5 — DB 오류 시 세션 명시적 롤백 (다음 호출 시 세션 오염 방지).
            self.db.rollback()
            logger.exception("MCP tool %s — DB error, session rolled back", name)
            return ToolResult(ok=False, data=None, error=f"{type(e).__name__}: {e}")
        except Exception as e:  # noqa: BLE001
            logger.exception("MCP tool %s failed", name)
            return ToolResult(ok=False, data=None, error=f"{type(e).__name__}: {e}")

    # ── handlers ────────────────────────────────────────────

    def _h_decode_vin(self, args: dict[str, Any]) -> ToolResult:
        from app.services.nhtsa import decode_vin
        vin = (args.get("vin") or "").strip()
        if len(vin) != 17:
            return ToolResult(ok=False, data=None, error="VIN must be exactly 17 chars")
        result = decode_vin(vin)
        return ToolResult(ok=True, data=result.to_dict())

    def _h_lookup_country_rules(self, args: dict[str, Any]) -> ToolResult:
        code = (args.get("country_code") or "").upper()
        if len(code) != 2:
            return ToolResult(ok=False, data=None, error="country_code must be ISO 3166-1 alpha-2")
        country = self.db.execute(
            select(Country)
            .where(Country.code == code)
            .options(selectinload(Country.rules))
        ).scalar_one_or_none()
        if country is None:
            return ToolResult(ok=False, data=None, error=f"country {code!r} not seeded")

        return ToolResult(ok=True, data={
            "code": country.code,
            "name_ko": country.name_ko,
            "name_en": country.name_en,
            "primary_language": country.primary_language,
            "business_language": country.business_language,
            "steering": country.steering,
            "is_blocked": country.is_blocked,
            "is_sanctioned": country.is_sanctioned,
            "is_russia_proxy_risk": country.is_russia_proxy_risk,
            "consular_legalization": country.consular_legalization,
            "pre_registration_system": country.pre_registration_system,
            "main_ports": country.main_ports_json or [],
            "notes": country.notes,
            "rules": [
                {
                    "body_type_filter": r.body_type_filter,
                    "age_limit_years": r.age_limit_years,
                    "age_basis": r.age_basis,
                    "steering_required": r.steering_required,
                    "max_engine_cc": r.max_engine_cc,
                    "max_cylinders": r.max_cylinders,
                    "fuel_blocked": r.fuel_blocked_json or [],
                    "psi_required": r.psi_required or [],
                    "consular_required": r.consular_required,
                    "required_documents": r.required_documents_json or [],
                }
                for r in country.rules
            ],
        })

    def _h_check_compliance(self, args: dict[str, Any]) -> ToolResult:
        # 가상 buyer/vehicle 생성해서 compliance 모듈 재사용
        buyer = Buyer(
            user_id=self.user_id,
            country_code=(args.get("buyer_country") or "").upper(),
            company_name=args.get("buyer_company_name"),
            tax_id=args.get("buyer_tax_id"),
        )
        vehicle = None
        if args.get("vehicle_engine_cc") or args.get("vehicle_fuel_type") or args.get("vehicle_list_price_usd"):
            vehicle = Vehicle(
                user_id=self.user_id,
                engine_cc=args.get("vehicle_engine_cc"),
                fuel_type=args.get("vehicle_fuel_type"),
                list_price_usd=args.get("vehicle_list_price_usd"),
            )
        report = compliance_check(buyer, vehicle)
        return ToolResult(ok=True, data=report.to_dict())

    def _h_suggest_price(self, args: dict[str, Any]) -> ToolResult:
        from app.services.pricing import suggest_price
        try:
            vid = uuid.UUID(args.get("vehicle_id") or "")
        except ValueError:
            return ToolResult(ok=False, data=None, error="invalid vehicle_id (must be UUID)")
        v = self.db.get(Vehicle, vid)
        if v is None or v.user_id != self.user_id:
            return ToolResult(ok=False, data=None, error="vehicle not found")
        suggestion = suggest_price(
            self.db, v, destination_country=args.get("destination_country")
        )
        return ToolResult(ok=True, data=suggestion.to_dict())

    def _h_check_ofac_sdn(self, args: dict[str, Any]) -> ToolResult:
        from app.services.ofac_loader import get_loader
        name = (args.get("name") or "").strip()
        if not name:
            return ToolResult(ok=False, data=None, error="name required")
        threshold = int(args.get("fuzzy_threshold") or 85)
        loader = get_loader()
        exact = loader.is_match(name)
        if exact:
            return ToolResult(ok=True, data={
                "match_type": "exact",
                "matched_name": exact.name,
                "uid": exact.uid,
                "type": exact.type,
                "programs": list(exact.programs),
                "score": 100.0,
            })
        fuzzy = loader.fuzzy_match(name, threshold=threshold)
        if fuzzy:
            entry, score = fuzzy
            return ToolResult(ok=True, data={
                "match_type": "fuzzy",
                "matched_name": entry.name,
                "uid": entry.uid,
                "type": entry.type,
                "programs": list(entry.programs),
                "score": score,
            })
        return ToolResult(ok=True, data={"match_type": "none"})

    def _h_evaluate_import(self, args: dict[str, Any]) -> ToolResult:
        try:
            vid = uuid.UUID(args.get("vehicle_id") or "")
        except ValueError:
            return ToolResult(ok=False, data=None, error="invalid vehicle_id")
        v = self.db.get(Vehicle, vid)
        if v is None or v.user_id != self.user_id:
            return ToolResult(ok=False, data=None, error="vehicle not found")
        cc = (args.get("destination_country") or "").upper()
        country = self.db.execute(
            select(Country)
            .where(Country.code == cc)
            .options(selectinload(Country.rules))
        ).scalar_one_or_none()
        if country is None:
            return ToolResult(ok=False, data=None, error=f"country {cc!r} not seeded")
        result = evaluate_import_rules(v, country)
        return ToolResult(ok=True, data=result.to_dict())

    def _h_list_vehicles(self, args: dict[str, Any]) -> ToolResult:
        stmt = select(Vehicle).where(Vehicle.user_id == self.user_id)
        if args.get("status"):
            stmt = stmt.where(Vehicle.status == args["status"])
        if args.get("search"):
            q = f"%{args['search']}%"
            stmt = stmt.where(
                or_(
                    Vehicle.make.ilike(q),
                    Vehicle.model.ilike(q),
                    Vehicle.vin.ilike(q),
                )
            )
        limit = min(int(args.get("limit") or 10), 50)
        stmt = stmt.order_by(Vehicle.created_at.desc()).limit(limit)
        rows = list(self.db.execute(stmt).scalars())
        return ToolResult(ok=True, data=[
            {
                "id": str(v.id),
                "make": v.make,
                "model": v.model,
                "year": v.year,
                "vin": v.vin,
                "status": v.status,
                "fuel_type": v.fuel_type,
                "engine_cc": v.engine_cc,
                "list_price_usd": float(v.list_price_usd) if v.list_price_usd else None,
            }
            for v in rows
        ])

    def _h_generate_mail_draft(self, args: dict[str, Any]) -> ToolResult:
        try:
            lid = uuid.UUID(args.get("listing_id") or "")
        except ValueError:
            return ToolResult(ok=False, data=None, error="invalid listing_id")
        listing = self.db.get(Listing, lid)
        if listing is None or listing.user_id != self.user_id:
            return ToolResult(ok=False, data=None, error="listing not found")
        if listing.buyer_id is None or listing.destination_country is None:
            return ToolResult(
                ok=False, data=None,
                error="listing must have buyer_id and destination_country set",
            )
        # 채팅에서는 LLM 호출 비용 절약을 위해 안내만 제공.
        # 실제 생성은 mail-draft endpoint 호출 권장.
        return ToolResult(ok=True, data={
            "listing_id": str(lid),
            "scenario": args.get("scenario") or "quote",
            "language": args.get("language") or "en",
            "action_required": (
                f"POST /api/listings/{lid}/mail-draft "
                f'with body {{"scenario":"{args.get("scenario") or "quote"}",'
                f'"language":"{args.get("language") or "en"}"}}'
            ),
            "estimated_seconds": 15,
            "note": (
                "다국어 메일 작성은 LLM 1건당 ~15초 소요. 채팅 UI 의 '메일 작성' "
                "버튼으로 진행하면 한국어 검증 패널 옵션도 사용 가능."
            ),
        })

    def _h_generate_export_documents(self, args: dict[str, Any]) -> ToolResult:
        # 직접 endpoint 호출 대신 안내 — Playwright 호출은 chat 응답 속도 저해 가능.
        # 안내 + UI 버튼 redirect 권장.
        try:
            lid = uuid.UUID(args.get("listing_id") or "")
        except ValueError:
            return ToolResult(ok=False, data=None, error="invalid listing_id")
        listing = self.db.get(Listing, lid)
        if listing is None or listing.user_id != self.user_id:
            return ToolResult(ok=False, data=None, error="listing not found")
        return ToolResult(ok=True, data={
            "listing_id": str(lid),
            "action_required": "POST /api/listings/{id}/documents",
            "estimated_seconds": 7,
            "note": "PDF 4종 동시 생성. 채팅 UI 에서 '서류 보기' 버튼으로 진행하세요.",
        })

    def _h_dashboard_summary(self, args: dict[str, Any]) -> ToolResult:
        from sqlalchemy import func
        v_count = self.db.execute(
            select(func.count()).select_from(Vehicle).where(Vehicle.user_id == self.user_id)
        ).scalar_one()
        b_count = self.db.execute(
            select(func.count()).select_from(Buyer).where(Buyer.user_id == self.user_id)
        ).scalar_one()
        l_count = self.db.execute(
            select(func.count()).select_from(Listing).where(Listing.user_id == self.user_id)
        ).scalar_one()
        return ToolResult(ok=True, data={
            "vehicles_total": v_count,
            "buyers_total": b_count,
            "listings_total": l_count,
        })


def get_dispatcher(db: Session, user_id: uuid.UUID) -> MCPDispatcher:
    return MCPDispatcher(db, user_id)
