"""MailWriter 스모크 테스트 — provider 추상화 검증.

사용법:
    # 키 없이 stub 으로
    py -X utf8 scripts/demo_mail_writer.py

    # 실제 LLM 호출 (env 또는 인자)
    $env:LLM_PROVIDER="gemini";  py -X utf8 scripts/demo_mail_writer.py
    $env:LLM_PROVIDER="anthropic"; py -X utf8 scripts/demo_mail_writer.py
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from app.models import Buyer, Country, ImportRule, Vehicle  # noqa: E402
from app.services.mail_writer import MailRequest, MailWriter  # noqa: E402

RULES_DIR = ROOT / "configs" / "rules"


def load_country(code: str) -> tuple[Country, list[ImportRule]]:
    fname_map = {
        "DO": "dominican_republic.yaml",
        "KE": "kenya.yaml",
        "LY": "libya.yaml",
        "KG": "kyrgyzstan.yaml",
        "SY": "syria.yaml",
    }
    data = yaml.safe_load((RULES_DIR / fname_map[code]).read_text(encoding="utf-8"))
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
        consular_legalization=bool(cp.get("consular_legalization", False)),
        pre_registration_system=cp.get("pre_registration_system"),
    )
    rules = []
    for raw in data.get("rules") or []:
        rules.append(
            ImportRule(
                country_code=country.code,
                body_type_filter=raw.get("body_type_filter"),
                psi_required=raw.get("psi_required") or [],
                doc_translation_lang=raw.get("doc_translation_lang"),
                consular_required=bool(raw.get("consular_required", False)),
                pre_registration=raw.get("pre_registration"),
                required_documents_json=raw.get("required_documents") or [],
            )
        )
    return country, rules


def show(draft) -> None:
    print(f"  provider={draft.provider} model={draft.model}")
    print(f"  subject: {draft.subject}")
    print("  body (first 220 chars):")
    body_preview = draft.body[:220].replace("\n", "\n           ")
    print(f"           {body_preview}{'...' if len(draft.body) > 220 else ''}")


def banner(title: str) -> None:
    print()
    print("=" * 78)
    print(f"  {title}")
    print("=" * 78)


def main() -> None:
    writer = MailWriter()  # uses LLM_PROVIDER from env (default=stub)

    # 공통 차량
    sonata = Vehicle(
        vin="KMHE41LBXKA000001",
        make="Hyundai",
        model="Sonata",
        year=2020,
        body_type="passenger",
        fuel_type="Gasoline",
        engine_cc=2000,
        transmission="A/T",
        steering="LHD",
        mileage_km=58000,
        color_exterior="Pearl White",
        hs_code="8703.23",
        list_price_usd=14000,
        manufacture_date=date(2020, 4, 1),
    )

    # 케이스 1: 도미니카 / 스페인어 / 견적
    do, do_rules = load_country("DO")
    rodriguez = Buyer(
        company_name="Rodriguez Motors",
        contact_person="Sr. Carlos Rodríguez",
        country_code="DO",
        preferred_port="Rio Haina",
        preferred_incoterm="CIF",
        preferred_payment="T/T 100% advance",
    )
    banner("Case 1 — Sonata → 도미니카 (Spanish, quote)")
    show(
        writer.draft(
            MailRequest(
                scenario="quote",
                language="es",
                vehicle=sonata,
                buyer=rodriguez,
                country=do,
                rules=do_rules,
                extra_context="Buyer asked for total CIF Santo Domingo with 28-35 day shipping.",
            )
        )
    )

    # 케이스 2: 리비아 / 아랍어 / inquiry
    ly, ly_rules = load_country("LY")
    ahmed = Buyer(
        company_name="Sahara Auto Trading",
        contact_person="Mr. Ahmed Al-Mansouri",
        country_code="LY",
        preferred_port="Misrata",
        preferred_incoterm="CIF",
    )
    banner("Case 2 — Sonata → 리비아 (Arabic, inquiry)")
    show(
        writer.draft(
            MailRequest(
                scenario="inquiry",
                language="ar",
                vehicle=sonata,
                buyer=ahmed,
                country=ly,
                rules=ly_rules,
            )
        )
    )

    # 케이스 3: 케냐 / 영어 / shipping
    ke, ke_rules = load_country("KE")
    kamau = Buyer(
        company_name="East Africa Motors Ltd",
        contact_person="Mr. James Kamau",
        country_code="KE",
        preferred_port="Mombasa",
        preferred_incoterm="CIF",
    )
    rhd_tucson = Vehicle(
        make="Hyundai",
        model="Tucson",
        year=2020,
        body_type="passenger",
        fuel_type="Diesel",
        engine_cc=2000,
        steering="RHD",
        mileage_km=42000,
        color_exterior="Black",
        list_price_usd=18500,
    )
    banner("Case 3 — Tucson(RHD) → 케냐 (English, shipping)")
    show(
        writer.draft(
            MailRequest(
                scenario="shipping",
                language="en",
                vehicle=rhd_tucson,
                buyer=kamau,
                country=ke,
                rules=ke_rules,
                extra_context="Vessel: HMM Algeciras, voyage V-2026-05E. ETD 2026-05-20, ETA Mombasa 2026-06-15.",
            )
        )
    )

    # 케이스 4: 도미니카 / 스페인어 / negotiate
    banner("Case 4 — Sonata → 도미니카 (Spanish, negotiate)")
    show(
        writer.draft(
            MailRequest(
                scenario="negotiate",
                language="es",
                vehicle=sonata,
                buyer=rodriguez,
                country=do,
                rules=do_rules,
                extra_context="Buyer requested USD 13,000 (down from listed 14,000).",
            )
        )
    )

    # 케이스 5: 케냐 / 영어 / dispute
    banner("Case 5 — Tucson → 케냐 (English, dispute)")
    show(
        writer.draft(
            MailRequest(
                scenario="dispute",
                language="en",
                vehicle=rhd_tucson,
                buyer=kamau,
                country=ke,
                rules=ke_rules,
                extra_context="Buyer reports a dent on rear-left door upon arrival at Mombasa.",
            )
        )
    )

    print()


if __name__ == "__main__":
    main()
