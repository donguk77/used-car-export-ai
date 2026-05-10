"""scripts/seed_demo_data.py — 시연용 매물 10건·바이어 5명·거래 5건 시드.

사용법:
    py -X utf8 scripts/seed_demo_data.py [--fresh]

--fresh: 기존 demo 사용자의 vehicles/buyers/listings 모두 삭제 후 재시드.
         (룰엔진 시드 import_rules.yaml 은 건드리지 않음)

연결 흐름:
    1. ensure_demo_user()
    2. 기존 demo 데이터 삭제 (옵션)
    3. Vehicle 10개 insert
    4. Buyer 5개 insert + compliance.check() 자동 트리거
    5. Listing 5개 insert + rule_engine.evaluate() 자동 트리거
"""

from __future__ import annotations

import argparse
import sys
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from sqlalchemy import delete, select  # noqa: E402
from sqlalchemy.orm import selectinload  # noqa: E402

from app.api.deps import ensure_demo_user  # noqa: E402
from app.core import compliance  # noqa: E402
from app.core.rule_engine import evaluate  # noqa: E402
from app.db import SessionLocal, create_all  # noqa: E402
from app.models import (  # noqa: E402
    Buyer,
    ComplianceCheck,
    Country,
    Document,
    Listing,
    Message,
    Shipment,
    Vehicle,
)

# ── Demo Vehicles (10) ────────────────────────────────────────
DEMO_VEHICLES = [
    dict(  # 1
        vin="KMHE41LBXLA000001", make="Hyundai", model="Sonata", year=2020,
        body_type="passenger", fuel_type="Gasoline", engine_cc=2000,
        transmission="A/T", steering="LHD", mileage_km=58000, seats=5,
        color_exterior="Pearl White", list_price_usd=14000, hs_code="8703.23",
        manufacture_date=date(2020, 4, 1), registration_date=date(2020, 5, 15),
    ),
    dict(  # 2
        vin="KMHJ381AAJA000002", make="Hyundai", model="Tucson", year=2019,
        body_type="passenger", fuel_type="Diesel", engine_cc=2000,
        transmission="A/T", steering="LHD", mileage_km=72000, seats=5,
        color_exterior="Black", list_price_usd=13500, hs_code="8703.32",
        manufacture_date=date(2019, 7, 10),
    ),
    dict(  # 3
        vin="KMHE41LBXJA000003", make="Hyundai", model="Sonata", year=2018,
        body_type="passenger", fuel_type="Gasoline", engine_cc=2000,
        transmission="A/T", steering="LHD", mileage_km=88000, seats=5,
        color_exterior="Silver", list_price_usd=10500, hs_code="8703.23",
        manufacture_date=date(2018, 3, 1),
    ),
    dict(  # 4 — G80 (high-cc, 키르기스스탄 차단 시연용)
        vin="KMHHU81KMNA000004", make="Genesis", model="G80", year=2022,
        body_type="passenger", fuel_type="Gasoline", engine_cc=3342,
        transmission="A/T", steering="LHD", mileage_km=42000, seats=5,
        color_exterior="Midnight Blue", list_price_usd=55000, hs_code="8703.24",
        manufacture_date=date(2022, 1, 15),
    ),
    dict(  # 5 — 1톤 트럭 (시리아 시연용) — Bongo 1톤 GVW 약 2,800kg
        vin="KMFGA17EPJA000005", make="Kia", model="Bongo", year=2020,
        body_type="truck", fuel_type="Diesel", engine_cc=2497,
        transmission="M/T", steering="LHD", mileage_km=95000,
        seats=3, gross_vehicle_weight_kg=2800,  # 1톤 트럭, 8704.21 (≤5t) confirm
        color_exterior="White", list_price_usd=18500, hs_code="8704.21",
        manufacture_date=date(2020, 8, 1),
    ),
    dict(  # 6
        vin="KMHD84LF2KU000006", make="Hyundai", model="Avante", year=2019,
        body_type="passenger", fuel_type="Gasoline", engine_cc=1591,
        transmission="A/T", steering="LHD", mileage_km=65000, seats=5,
        color_exterior="White", list_price_usd=11000, hs_code="8703.23",  # findings #032
        manufacture_date=date(2019, 5, 1),
    ),
    dict(  # 7 — RHD Tucson (케냐 시연용, 단 2017이라 발효 후 fail)
        vin="KMHJ381BFHU000007", make="Hyundai", model="Tucson", year=2017,
        body_type="passenger", fuel_type="Diesel", engine_cc=2000,
        transmission="A/T", steering="RHD", mileage_km=98000, seats=5,
        color_exterior="Gray", list_price_usd=11500, hs_code="8703.32",
        manufacture_date=date(2017, 3, 1), registration_date=date(2017, 5, 1),
    ),
    dict(  # 8
        vin="KNAGM4A75LA000008", make="Kia", model="K5", year=2020,
        body_type="passenger", fuel_type="Gasoline", engine_cc=2000,
        transmission="A/T", steering="LHD", mileage_km=53000, seats=5,
        color_exterior="Silver", list_price_usd=15000, hs_code="8703.23",
        manufacture_date=date(2020, 6, 1),
    ),
    dict(  # 9
        vin="KM8R5DHE6MU000009", make="Hyundai", model="Palisade", year=2021,
        body_type="passenger", fuel_type="Gasoline", engine_cc=3778,
        transmission="A/T", steering="LHD", mileage_km=38000, seats=8,  # Palisade 7-8 인승
        color_exterior="Midnight Black", list_price_usd=42000, hs_code="8703.24",
        manufacture_date=date(2021, 2, 1),
    ),
    dict(  # 10 — 승합차 — Grand Starex 12인승 (8702.10 confirm)
        vin="KMJWA37FBJU000010", make="Hyundai", model="Grand Starex", year=2018,
        body_type="van", fuel_type="Diesel", engine_cc=2497,
        transmission="A/T", steering="LHD", mileage_km=110000,
        seats=12, gross_vehicle_weight_kg=2900,  # 12인승 → 8702.10 (≥10 seats), GVW <5t
        color_exterior="White", list_price_usd=14000, hs_code="8702.10",  # findings #033 해소
        manufacture_date=date(2018, 4, 1),
    ),
]

# ── Demo Buyers (5) ───────────────────────────────────────────
DEMO_BUYERS = [
    dict(  # 1 — DR clean
        company_name="Rodriguez Motors S.R.L.", contact_person="Sr. Carlos Rodríguez",
        country_code="DO", city="Santo Domingo",
        address="Av. Winston Churchill 123, Santo Domingo, DN 10148",
        tax_id="DO-987654321", phone="+1-809-555-0123", whatsapp="+1-809-555-0123",
        email="carlos@rodriguezmotors.do",
        preferred_language="es", preferred_currency="USD", preferred_payment="T/T",
        preferred_port="Rio Haina", preferred_incoterm="CIF",
        total_orders=12,
    ),
    dict(  # 2 — LY clean
        company_name="Sahara Auto Trading", contact_person="Mr. Ahmed Al-Mansouri",
        country_code="LY", city="Misrata",
        address="Tripoli Street, Misrata Free Zone",
        tax_id="LY-456789", phone="+218-91-555-0001", whatsapp="+218-91-555-0001",
        email="ahmed@sahara-auto.ly",
        preferred_language="ar", preferred_currency="USD", preferred_payment="T/T",
        preferred_port="Misrata", preferred_incoterm="CIF",
        total_orders=28,
    ),
    dict(  # 3 — KG warning (러시아 우회 위험 — neutral on first check w/o vehicle)
        company_name="ABC Auto LLC", contact_person="Aibek Tashov",
        country_code="KG", city="Bishkek",
        address="Chui Avenue 100, Bishkek 720040",
        tax_id="KG-123456", phone="+996-555-000-001", whatsapp="+996-555-000-001",
        email="aibek@abc-auto.kg",
        preferred_language="ru", preferred_currency="USD", preferred_payment="T/T",
        preferred_port="Bandar Abbas (transit)", preferred_incoterm="CIF",
        total_orders=0,  # 신규 — 위험도 ↑
    ),
    dict(  # 4 — KE clean (RHD market)
        company_name="East Africa Motors Ltd", contact_person="Mr. James Kamau",
        country_code="KE", city="Mombasa",
        address="Moi Avenue, Mombasa 80100",
        tax_id="KE-P000001M", phone="+254-722-555-001", whatsapp="+254-722-555-001",
        email="kamau@eastafricamotors.co.ke",
        preferred_language="en", preferred_currency="USD", preferred_payment="L/C",
        preferred_port="Mombasa", preferred_incoterm="CIF",
        total_orders=15,
    ),
    dict(  # 5 — SY warning (제재)
        company_name="Damascus Auto Trading", contact_person="Mr. Karim Hadi",
        country_code="SY", city="Damascus",
        address="Mezzeh Highway, Damascus",
        tax_id="SY-555000", phone="+963-11-555-0001",
        email="karim@damascus-auto.sy",
        preferred_language="ar", preferred_currency="USD",
        preferred_port="Latakia", preferred_incoterm="CIF",
        total_orders=2,
    ),
]

# ── Demo Listings (5) — vehicle_idx, buyer_idx, dest, status, agreed_price
DEMO_LISTINGS = [
    dict(vehicle_idx=0, buyer_idx=0, destination_country="DO", status="quoted",
         agreed_price_usd=14000, incoterm="CIF", port_of_discharge="Rio Haina",
         shipping_method="container"),
    dict(vehicle_idx=2, buyer_idx=1, destination_country="LY", status="agreed",
         agreed_price_usd=10000, incoterm="CIF", port_of_discharge="Misrata",
         shipping_method="roro"),
    dict(vehicle_idx=3, buyer_idx=2, destination_country="KG", status="inquiry",
         incoterm="CIF",
         shipping_method="container"),
    dict(vehicle_idx=6, buyer_idx=3, destination_country="KE", status="inquiry",
         incoterm="CIF", port_of_discharge="Mombasa",
         shipping_method="roro"),
    dict(vehicle_idx=4, buyer_idx=4, destination_country="SY", status="quoted",
         agreed_price_usd=18500, incoterm="CIF", port_of_discharge="Latakia",
         shipping_method="roro"),
]


def seed(*, fresh: bool = False) -> None:
    create_all()
    with SessionLocal() as s:
        user_id = ensure_demo_user(s)
        s.flush()

        if fresh:
            print("  🧹 clearing existing demo vehicles/buyers/listings...")
            # findings #044 — Message.listing_id 가 ondelete=SET NULL 이라 listing 삭제 시
            # cascade 안됨. 명시적으로 messages 먼저 삭제 (user 의 listings 참조).
            user_listing_ids = [
                row[0] for row in s.execute(
                    select(Listing.id).where(Listing.user_id == user_id)
                ).all()
            ]
            if user_listing_ids:
                s.execute(delete(Message).where(Message.listing_id.in_(user_listing_ids)))
                s.execute(delete(Document).where(Document.listing_id.in_(user_listing_ids)))
                s.execute(delete(Shipment).where(Shipment.listing_id.in_(user_listing_ids)))
            # 그 다음 user 의 vehicles/buyers/listings (Buyer.compliance_checks 는 cascade)
            s.execute(delete(Listing).where(Listing.user_id == user_id))
            s.execute(delete(Vehicle).where(Vehicle.user_id == user_id))
            s.execute(delete(Buyer).where(Buyer.user_id == user_id))
            # 추가 안전장치: orphan messages (listing_id IS NULL) 정리
            s.execute(delete(Message).where(Message.listing_id.is_(None)))
            s.flush()

        # Vehicles
        vehicles: list[Vehicle] = []
        for v_data in DEMO_VEHICLES:
            v = Vehicle(user_id=user_id, **v_data)
            s.add(v)
            vehicles.append(v)
        s.flush()
        print(f"  🚗 inserted {len(vehicles)} vehicles")

        # Buyers + auto compliance
        buyers: list[Buyer] = []
        for b_data in DEMO_BUYERS:
            b = Buyer(user_id=user_id, **b_data)
            s.add(b)
            s.flush()
            report = compliance.check(b, vehicle=None)
            b.sanctions_status = report.overall
            b.russia_proxy_risk_score = (
                max(0, 100 - report.score) if report.overall != "clean" else 0
            )
            s.add(ComplianceCheck(
                buyer_id=b.id, check_type="auto_summary", result=report.overall,
                flags_json=[f.to_dict() for f in report.findings],
                raw_response={"overall": report.overall, "score": report.score},
                checked_at=date.today(),
            ))
            buyers.append(b)
        s.flush()
        print(f"  🧑 inserted {len(buyers)} buyers (compliance auto-checked)")

        # Listings + auto import-check
        for l_data in DEMO_LISTINGS:
            v = vehicles[l_data["vehicle_idx"]]
            b = buyers[l_data["buyer_idx"]]
            code = l_data["destination_country"]
            country = s.execute(
                select(Country).where(Country.code == code).options(selectinload(Country.rules))
            ).scalar_one()

            listing = Listing(
                user_id=user_id, vehicle_id=v.id, buyer_id=b.id,
                destination_country=code,
                agreed_price_usd=l_data.get("agreed_price_usd"),
                incoterm=l_data.get("incoterm"),
                port_of_discharge=l_data.get("port_of_discharge"),
                shipping_method=l_data.get("shipping_method"),
                status=l_data["status"],
                inquiry_at=datetime.now(timezone.utc),
            )
            # FSM 타임스탬프 채움
            if l_data["status"] in ("quoted", "negotiating", "agreed",
                                     "documenting", "shipping", "in_transit", "delivered"):
                listing.quoted_at = datetime.now(timezone.utc)
            if l_data["status"] in ("agreed", "documenting", "shipping",
                                     "in_transit", "delivered"):
                listing.agreed_at = datetime.now(timezone.utc)

            result = evaluate(v, country, rules=country.rules, buyer=b)
            listing.can_import = result.can_import
            listing.import_check_json = result.to_dict()
            s.add(listing)
        s.flush()
        print(f"  📋 inserted {len(DEMO_LISTINGS)} listings (import-check auto-evaluated)")

        s.commit()
        print(f"\n  ✅ demo data seeded for user {user_id}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fresh", action="store_true",
                        help="기존 demo vehicles/buyers/listings 삭제 후 재시드")
    args = parser.parse_args()
    seed(fresh=args.fresh)


if __name__ == "__main__":
    main()
