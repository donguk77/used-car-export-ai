"""룰엔진 + 컴플라이언스 통합 스모크 테스트 (DB 없이).

사용법:
    cd backend
    python ../scripts/demo_rule_engine.py

발표 시연 시나리오 5개를 그대로 실행한다 (docs/userflow_and_erd.md §1.3).
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import yaml

# backend/ 경로 추가 — 스크립트는 프로젝트 루트에서 실행 가정
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from app.core import compliance  # noqa: E402
from app.core.rule_engine import evaluate  # noqa: E402
from app.models import Buyer, Country, ImportRule, Vehicle  # noqa: E402

RULES_DIR = ROOT / "configs" / "rules"


def load_country(code: str) -> tuple[Country, list[ImportRule]]:
    """YAML 한 파일을 읽어 메모리 위 Country + ImportRule 객체로 만든다."""
    fname_map = {
        "DO": "dominican_republic.yaml",
        "KE": "kenya.yaml",
        "LY": "libya.yaml",
        "KG": "kyrgyzstan.yaml",
        "SY": "syria.yaml",
    }
    path = RULES_DIR / fname_map[code]
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    cp = data["country"]
    country = Country(
        code=cp["code"],
        name_en=cp["name_en"],
        name_ko=cp.get("name_ko"),
        primary_language=cp.get("primary_language"),
        steering=cp.get("steering"),
        is_high_risk=bool(cp.get("is_high_risk", False)),
        is_russia_proxy_risk=bool(cp.get("is_russia_proxy_risk", False)),
        is_sanctioned=bool(cp.get("is_sanctioned", False)),
        is_blocked=bool(cp.get("is_blocked", False)),
        notes=cp.get("notes"),
    )
    rules = []
    for raw in data.get("rules") or []:
        rules.append(
            ImportRule(
                country_code=country.code,
                body_type_filter=raw.get("body_type_filter"),
                age_limit_years=raw.get("age_limit_years"),
                age_basis=raw.get("age_basis"),
                age_effective_from=_d(raw.get("age_effective_from")),
                registration_after_date=_d(raw.get("registration_after_date")),
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
            )
        )
    return country, rules


def _d(v):
    if v is None:
        return None
    if isinstance(v, date):
        return v
    return date.fromisoformat(v)


def banner(title: str) -> None:
    print()
    print("=" * 72)
    print(f"  {title}")
    print("=" * 72)


def show(label: str, result) -> None:
    icon = "OK " if result.can_import else "NO "
    print(f"\n  [{icon}] {label}")
    if result.reasons:
        print("        reasons:")
        for r in result.reasons:
            print(f"          - {r}")
    if result.warnings:
        print("        warnings:")
        for w in result.warnings:
            print(f"          ! {w}")
    if result.required_documents:
        print(f"        required_docs: {', '.join(result.required_documents)}")


def show_compliance(label: str, report) -> None:
    print(f"\n  [{report.overall.upper():>7s}] {label}  (score={report.score})")
    for f in report.findings:
        sev = {"blocked": "X", "warning": "!", "clean": "."}[f.severity]
        print(f"        {sev} {f.code}: {f.message}")


# ──────────────────────────────────────────────────────────────────────
# 시나리오 1: Sonata 2018 LHD 가솔린
# ──────────────────────────────────────────────────────────────────────
def scenario_sonata_2018() -> None:
    banner("시나리오 1 — Hyundai Sonata 2018 (LHD, 2.0L 가솔린)")
    sonata = Vehicle(
        vin="KMHE41LBXKA000001",
        make="Hyundai",
        model="Sonata",
        year=2018,
        body_type="passenger",
        fuel_type="Gasoline",
        engine_cc=2000,
        steering="LHD",
        list_price_usd=12500,
        registration_date=date(2018, 6, 1),
        manufacture_date=date(2018, 3, 1),
    )

    today = date(2026, 5, 9)

    do, do_rules = load_country("DO")
    show("Sonata → 도미니카공화국", evaluate(sonata, do, rules=do_rules, today=today))

    ke, ke_rules = load_country("KE")
    show("Sonata → 케냐 (RHD only)", evaluate(sonata, ke, rules=ke_rules, today=today))

    ly, ly_rules = load_country("LY")
    show("Sonata → 리비아", evaluate(sonata, ly, rules=ly_rules, today=today))


# ──────────────────────────────────────────────────────────────────────
# 시나리오 2: Genesis G80 → 키르기스스탄 (러시아 우회 차단)
# ──────────────────────────────────────────────────────────────────────
def scenario_genesis_to_kg() -> None:
    banner("시나리오 2 — Genesis G80 3.3L → 키르기스스탄 (러시아 우회 차단)")
    g80 = Vehicle(
        vin="KMHHU81KMNA000001",
        make="Genesis",
        model="G80",
        year=2022,
        body_type="passenger",
        fuel_type="Gasoline",
        engine_cc=3342,
        steering="LHD",
        list_price_usd=55000,
        manufacture_date=date(2022, 1, 1),
    )
    new_buyer = Buyer(
        company_name="ABC Auto LLC",
        country_code="KG",
        tax_id="KG-123456",
        total_orders=0,
    )

    kg, kg_rules = load_country("KG")
    today = date(2026, 5, 9)

    show(
        "G80 → 키르기스스탄 (상황허가 미보유, 신규 바이어)",
        evaluate(g80, kg, rules=kg_rules, buyer=new_buyer, today=today),
    )

    show(
        "G80 → 키르기스스탄 (상황허가 보유 가정)",
        evaluate(
            g80,
            kg,
            rules=kg_rules,
            buyer=new_buyer,
            today=today,
            granted_flags={"has_situational_license"},
        ),
    )

    show_compliance("Buyer ABC Auto + G80 컴플라이언스 검사", compliance.check(new_buyer, g80))


# ──────────────────────────────────────────────────────────────────────
# 시나리오 3: 케냐 8년 룰 — 2026.1.1 발효 vs 그 이전
# ──────────────────────────────────────────────────────────────────────
def scenario_kenya_age_rule() -> None:
    banner("시나리오 3 — 케냐 2026.1.1 8년 룰 발효 시점")
    rhd_old = Vehicle(
        make="Hyundai",
        model="Tucson",
        year=2017,
        body_type="passenger",
        fuel_type="Diesel",
        engine_cc=2000,
        steering="RHD",
        registration_date=date(2017, 5, 1),
    )
    ke, ke_rules = load_country("KE")

    show(
        "2017 RHD Tucson → 케냐 (today=2025-12-31, 룰 발효 전)",
        evaluate(rhd_old, ke, rules=ke_rules, today=date(2025, 12, 31)),
    )
    show(
        "2017 RHD Tucson → 케냐 (today=2026-01-02, 룰 발효 후)",
        evaluate(rhd_old, ke, rules=ke_rules, today=date(2026, 1, 2)),
    )


# ──────────────────────────────────────────────────────────────────────
# 시나리오 4: 시리아 — 매뉴얼 검토 + OFAC 사전 조회 경고
# ──────────────────────────────────────────────────────────────────────
def scenario_syria_warning() -> None:
    banner("시나리오 4 — 시리아 (정세 격변, OFAC 경고)")
    pickup = Vehicle(
        make="Kia",
        model="Bongo",
        year=2020,
        body_type="truck",
        fuel_type="Diesel",
        engine_cc=2497,
        steering="LHD",
        manufacture_date=date(2020, 3, 1),
    )
    sy, sy_rules = load_country("SY")
    show(
        "Bongo 1톤 → 시리아",
        evaluate(pickup, sy, rules=sy_rules, today=date(2026, 5, 9)),
    )


# ──────────────────────────────────────────────────────────────────────
# 시나리오 5: 정상 거래 — 도미니카 클린 케이스
# ──────────────────────────────────────────────────────────────────────
def scenario_clean_dominican() -> None:
    banner("시나리오 5 — 정상 거래 (도미니카 + 클린 바이어)")
    sonata = Vehicle(
        make="Hyundai",
        model="Sonata",
        year=2020,
        body_type="passenger",
        fuel_type="Gasoline",
        engine_cc=2000,
        steering="LHD",
        list_price_usd=14000,
        manufacture_date=date(2020, 4, 1),
    )
    rodriguez = Buyer(
        company_name="Rodriguez Motors",
        country_code="DO",
        tax_id="DO-987654",
        total_orders=12,
    )
    do, do_rules = load_country("DO")
    show(
        "Sonata → 도미니카",
        evaluate(sonata, do, rules=do_rules, today=date(2026, 5, 9)),
    )
    show_compliance("Rodriguez Motors + Sonata", compliance.check(rodriguez, sonata))


def main() -> None:
    scenario_sonata_2018()
    scenario_genesis_to_kg()
    scenario_kenya_age_rule()
    scenario_syria_warning()
    scenario_clean_dominican()
    print()


if __name__ == "__main__":
    main()
