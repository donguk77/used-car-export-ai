"""Document writer 스모크 테스트 — 4종 PDF 생성.

사용법:
    py -X utf8 scripts/demo_documents.py
출력:
    generated_pdfs/<invoice_no>/{invoice,packing_list,shipping_instruction,co_application}.pdf
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from app.services.document_writer import DocumentInput, generate_all  # noqa: E402

OUT_BASE = ROOT / "generated_pdfs"


def main() -> None:
    sample = DocumentInput(
        invoice_no="SN-2026-0001",
        invoice_date=date(2026, 5, 9),
        # Shipper
        shipper_name="동강그린모터스 (Donggang Green Motors Co., Ltd.)",
        shipper_address="123-4 Songdo-dong, Yeonsu-gu, Incheon 21984, Republic of Korea",
        shipper_phone="+82-32-555-1234",
        shipper_business_no="123-45-67890",
        # Consignee
        consignee_name="Rodriguez Motors S.R.L.",
        consignee_contact="Sr. Carlos Rodríguez",
        consignee_address="Av. Winston Churchill 123, Santo Domingo, DN 10148",
        consignee_country="Dominican Republic",
        consignee_tax_id="DO-987654321",
        # Vehicle
        make="Hyundai",
        model="Sonata",
        year=2020,
        vin="KMHE41LBXKA000001",
        body_type="passenger",
        fuel_type="Gasoline",
        engine_cc=2000,
        color="Pearl White",
        mileage_km=58000,
        hs_code="8703.23",
        net_weight_kg=1480,
        gross_weight_kg=1620,
        # Pricing
        unit_price_usd=14000.00,
        quantity=1,
        currency="USD",
        # Shipping
        incoterm="CIF",
        payment_terms="T/T 100% in advance",
        port_of_loading="Incheon, Korea",
        port_of_discharge="Rio Haina, Dominican Republic",
        final_destination="Santo Domingo, DR",
        vessel_name="HMM Algeciras",
        voyage_no="V-2026-05E",
        shipping_method="Container",
        container_no="HMMU1234567",
        seal_no="KR0098765",
        notify_party="Same as Consignee",
        # Bank
        bank_name="KEB Hana Bank, Songdo Branch",
        bank_swift="KOEXKRSE",
        bank_account="123-456789-01-001",
        # FTA — 도미니카는 FTA 없음
        fta_used=None,
    )

    out_dir = OUT_BASE / sample.invoice_no
    out_dir.mkdir(parents=True, exist_ok=True)

    pdfs = generate_all(sample)
    for doc_type, content in pdfs.items():
        path = out_dir / f"{doc_type}.pdf"
        path.write_bytes(content)
        print(f"  ✓ {path.relative_to(ROOT)}  ({len(content):,} bytes)")

    print(f"\n  → {len(pdfs)} PDFs generated in {out_dir.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()
