"""configs/rules/*.yaml → countries + import_rules upsert.

사용법:
    cd backend
    python -m app.seed.import_rules
    # 또는 특정 파일만
    python -m app.seed.import_rules --file ../configs/rules/dominican_republic.yaml
"""

from __future__ import annotations

import argparse
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any

import yaml
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.api.deps import ensure_demo_user
from app.config import get_settings
from app.db import SessionLocal, create_all
from app.models import Country, ImportRule


def _resolve_rules_dir() -> Path:
    """RULES_DIR 가 상대경로면 backend/ 기준으로 한 단계 위(=프로젝트 루트)에서 찾는다."""
    settings = get_settings()
    p = Path(settings.rules_dir)
    if p.is_absolute():
        return p
    here = Path(__file__).resolve().parent.parent.parent  # backend/
    candidate = (here.parent / p).resolve()
    if candidate.exists():
        return candidate
    return (here / p).resolve()


def _parse_date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        return datetime.strptime(value, "%Y-%m-%d").date()
    raise TypeError(f"Cannot parse date from {value!r}")


def _upsert_country(session: Session, payload: dict[str, Any]) -> Country:
    code = payload["code"]
    country = session.get(Country, code)
    if country is None:
        country = Country(code=code, name_en=payload["name_en"])
        session.add(country)

    country.name_en = payload["name_en"]
    country.name_ko = payload.get("name_ko")
    country.name_local = payload.get("name_local")
    country.region = payload.get("region")
    country.primary_language = payload.get("primary_language")
    country.business_language = payload.get("business_language")
    country.steering = payload.get("steering")
    country.is_high_risk = bool(payload.get("is_high_risk", False))
    country.is_russia_proxy_risk = bool(payload.get("is_russia_proxy_risk", False))
    country.is_sanctioned = bool(payload.get("is_sanctioned", False))
    country.is_blocked = bool(payload.get("is_blocked", False))
    country.main_ports_json = payload.get("main_ports") or []
    country.pre_registration_system = payload.get("pre_registration_system")
    country.consular_legalization = bool(payload.get("consular_legalization", False))
    country.notes = payload.get("notes")
    return country


def _replace_rules(session: Session, country_code: str, rules: list[dict[str, Any]]) -> int:
    """Drop-and-insert. 룰은 작은 집합이라 단순함이 안전함."""
    session.execute(delete(ImportRule).where(ImportRule.country_code == country_code))

    for raw in rules:
        rule = ImportRule(
            country_code=country_code,
            body_type_filter=raw.get("body_type_filter"),
            age_limit_years=raw.get("age_limit_years"),
            age_basis=raw.get("age_basis"),
            age_effective_from=_parse_date(raw.get("age_effective_from")),
            registration_after_date=_parse_date(raw.get("registration_after_date")),
            steering_required=raw.get("steering_required"),
            max_engine_cc=raw.get("max_engine_cc"),
            max_cylinders=raw.get("max_cylinders"),
            fuel_blocked_json=raw.get("fuel_blocked") or [],
            psi_required=raw.get("psi_required") or [],
            doc_translation_lang=raw.get("doc_translation_lang"),
            consular_required=bool(raw.get("consular_required", False)),
            pre_registration=raw.get("pre_registration"),
            blocked_conditions_json=raw.get("blocked_conditions") or [],
            required_documents_json=raw.get("required_documents") or [],
            effective_from=_parse_date(raw.get("effective_from")),
            effective_to=_parse_date(raw.get("effective_to")),
            source_url=raw.get("source_url"),
            last_verified_at=_parse_date(raw.get("last_verified_at")),
            notes=raw.get("notes"),
        )
        session.add(rule)
    return len(rules)


def seed_file(session: Session, path: Path) -> tuple[str, int]:
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    country_payload = data["country"]
    rules = data.get("rules") or []

    country = _upsert_country(session, country_payload)
    session.flush()
    rule_count = _replace_rules(session, country.code, rules)
    return country.code, rule_count


def seed_all(files: list[Path] | None = None) -> None:
    if files is None:
        rules_dir = _resolve_rules_dir()
        if not rules_dir.exists():
            print(f"❌ rules_dir not found: {rules_dir}", file=sys.stderr)
            sys.exit(1)
        files = sorted(rules_dir.glob("*.yaml")) + sorted(rules_dir.glob("*.yml"))

    if not files:
        print("⚠️  no YAML rule files found.", file=sys.stderr)
        return

    create_all()  # PoC 단계 — 운영은 Alembic 으로 전환

    with SessionLocal() as session:
        # 1. demo 사용자 (PoC: 모든 데이터의 owner)
        user_id = ensure_demo_user(session)
        session.flush()
        print(f"👤 demo user: {user_id}")

        # 2. 국가 + 룰
        for path in files:
            try:
                code, n = seed_file(session, path)
                print(f"✅ {path.name:40s}  →  {code}  ({n} rules)")
            except Exception as exc:  # noqa: BLE001
                session.rollback()
                print(f"❌ {path.name}: {exc}", file=sys.stderr)
                raise
        session.commit()
    print(f"🌱 seeded {len(files)} country file(s).")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed countries + import_rules from YAML.")
    parser.add_argument("--file", type=Path, action="append", help="단일 YAML 파일 (반복 가능)")
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    seed_all(args.file)
