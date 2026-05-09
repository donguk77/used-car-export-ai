"""국가별 통관 가능성 판정.

Vehicle + Country(+rules) → ImportCheckResult.
docs/userflow_and_erd.md 시나리오 1, configs/rules/*.yaml 의 룰을 평가.

기본 사용:
    result = evaluate(vehicle, country, buyer=buyer)
    listing.can_import = result.can_import
    listing.import_check_json = result.to_dict()
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass, field
from datetime import date
from typing import Any

from app.models import Buyer, Country, ImportRule, Vehicle


@dataclass
class ImportCheckResult:
    can_import: bool
    reasons: list[str] = field(default_factory=list)  # blocking
    warnings: list[str] = field(default_factory=list)  # non-blocking flags
    required_documents: list[str] = field(default_factory=list)
    matched_rule_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def evaluate(
    vehicle: Vehicle,
    country: Country,
    *,
    rules: Iterable[ImportRule] | None = None,
    buyer: Buyer | None = None,
    today: date | None = None,
    granted_flags: set[str] | None = None,
) -> ImportCheckResult:
    """차량 + 도착국 → 통관 가능 여부.

    granted_flags: {"has_situational_license"} 같이 사전에 받아둔 면제권한.
    """
    today = today or date.today()
    granted_flags = granted_flags or set()
    rules_list = list(rules) if rules is not None else list(country.rules)

    if country.is_blocked:
        return ImportCheckResult(
            can_import=False,
            reasons=[f"{country.code} is system-blocked ({country.notes or 'no further detail'})"],
        )

    rule = _pick_rule(rules_list, vehicle)
    if rule is None:
        return ImportCheckResult(
            can_import=False,
            reasons=[f"no import rule defined for {country.code} / body_type={vehicle.body_type}"],
        )

    reasons: list[str] = []
    warnings: list[str] = []

    _check_steering(rule, vehicle, reasons)
    _check_age(rule, vehicle, today, reasons, warnings)
    _check_engine(rule, vehicle, reasons)
    _check_fuel(rule, vehicle, reasons)
    _check_blocked_conditions(rule, vehicle, buyer, granted_flags, reasons)
    _attach_country_warnings(country, warnings)

    required_documents = list(rule.required_documents_json or [])
    if rule.consular_required and "consular_legalization" not in required_documents:
        required_documents.append("consular_legalization")
    if rule.psi_required:
        for psi in rule.psi_required:
            tag = f"psi_{psi.lower()}"
            if tag not in required_documents:
                required_documents.append(tag)
    if rule.doc_translation_lang:
        tag = f"translation_{rule.doc_translation_lang}"
        if tag not in required_documents:
            required_documents.append(tag)

    return ImportCheckResult(
        can_import=not reasons,
        reasons=reasons,
        warnings=warnings,
        required_documents=required_documents,
        matched_rule_id=str(rule.id) if rule.id else None,
    )


def _pick_rule(rules: list[ImportRule], vehicle: Vehicle) -> ImportRule | None:
    """body_type 일치 룰 우선, 없으면 wildcard(NULL) 룰."""
    specific = [r for r in rules if r.body_type_filter and r.body_type_filter == vehicle.body_type]
    if specific:
        return specific[0]
    wildcard = [r for r in rules if r.body_type_filter is None]
    return wildcard[0] if wildcard else None


def _check_steering(rule: ImportRule, vehicle: Vehicle, reasons: list[str]) -> None:
    req = rule.steering_required
    if not req or req == "MIXED":
        return
    if req == "LHD_only" and vehicle.steering != "LHD":
        reasons.append(f"steering: country requires LHD, vehicle is {vehicle.steering or 'unknown'}")
    elif req == "RHD_only" and vehicle.steering != "RHD":
        reasons.append(f"steering: country requires RHD, vehicle is {vehicle.steering or 'unknown'}")


def _check_age(
    rule: ImportRule,
    vehicle: Vehicle,
    today: date,
    reasons: list[str],
    warnings: list[str],
) -> None:
    if rule.age_limit_years is None and rule.registration_after_date is None:
        return
    if rule.age_effective_from and today < rule.age_effective_from:
        return  # rule not yet in force

    basis = _basis_date(rule, vehicle)
    if basis is None:
        warnings.append("age basis date unknown — could not verify age limit")
        return

    if rule.registration_after_date and basis < rule.registration_after_date:
        reasons.append(
            f"age: vehicle date {basis} earlier than required {rule.registration_after_date}"
        )

    if rule.age_limit_years is not None:
        age_years = (today - basis).days / 365.25
        if age_years > rule.age_limit_years:
            reasons.append(
                f"age: max {rule.age_limit_years} years allowed, vehicle is {age_years:.1f} years"
            )


def _basis_date(rule: ImportRule, vehicle: Vehicle) -> date | None:
    if rule.age_basis == "first_registration":
        return vehicle.registration_date or _from_year(vehicle.year)
    # default: manufacture year
    return vehicle.manufacture_date or _from_year(vehicle.year)


def _from_year(year: int | None) -> date | None:
    return date(year, 1, 1) if year else None


def _check_engine(rule: ImportRule, vehicle: Vehicle, reasons: list[str]) -> None:
    if rule.max_engine_cc and vehicle.engine_cc and vehicle.engine_cc > rule.max_engine_cc:
        reasons.append(
            f"engine: max {rule.max_engine_cc}cc allowed, vehicle is {vehicle.engine_cc}cc"
        )


def _check_fuel(rule: ImportRule, vehicle: Vehicle, reasons: list[str]) -> None:
    blocked = rule.fuel_blocked_json or []
    if blocked and vehicle.fuel_type and vehicle.fuel_type in blocked:
        reasons.append(f"fuel: type {vehicle.fuel_type} blocked by destination")


def _check_blocked_conditions(
    rule: ImportRule,
    vehicle: Vehicle,
    buyer: Buyer | None,
    granted_flags: set[str],
    reasons: list[str],
) -> None:
    for cond in rule.blocked_conditions_json or []:
        if not _condition_matches(cond, vehicle, buyer):
            continue
        unless = cond.get("unless")
        if unless and unless in granted_flags:
            continue
        reasons.append(cond.get("reason") or f"blocked condition met: {cond}")


def _condition_matches(cond: dict[str, Any], vehicle: Vehicle, buyer: Buyer | None) -> bool:
    field_path = cond["field"]
    op = cond["op"]
    expected = cond["value"]

    if field_path.startswith("buyer."):
        if buyer is None:
            return False
        actual = getattr(buyer, field_path.split(".", 1)[1], None)
    else:
        actual = getattr(vehicle, field_path, None)

    if actual is None:
        return False

    if op == "gt":
        return actual > expected
    if op == "lt":
        return actual < expected
    if op == "eq":
        return actual == expected
    if op == "in":
        return actual in expected
    raise ValueError(f"unknown condition operator: {op}")


def _attach_country_warnings(country: Country, warnings: list[str]) -> None:
    if country.is_high_risk:
        warnings.append(f"{country.code} flagged HIGH RISK — manual review recommended")
    if country.is_russia_proxy_risk:
        warnings.append(f"{country.code} = Russia-proxy risk — compliance check required")
    if country.is_sanctioned:
        warnings.append(f"{country.code} subject to sanctions — OFAC clearance required")
