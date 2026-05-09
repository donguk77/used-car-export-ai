"""우리 템플릿 vs 1차 자료 PDF — 필드 커버리지 매트릭스 자동 생성.

방식:
  1. 각 doc_type 별로 "표준 무역 양식 필드" (canonical fields) 정의 — bilingual EN/KR regex.
  2. 우리 Jinja 템플릿 텍스트에서 각 필드 라벨이 존재하는지 확인.
  3. docs/samples/ 의 1차 자료 PDF 에서 텍스트 추출 후 동일 검사.
  4. 매트릭스 markdown 으로 출력 → docs/validation/document_field_matrix.md

규칙: 라벨 매칭은 regex 기반이라 *존재* 만 본다. 정확성은 별개 검증 필요.
      단 *부재* 는 명백한 gap → findings.md 후보.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent.parent
SAMPLES_DIR = ROOT / "docs" / "samples"
TEMPLATES_DIR = ROOT / "backend" / "app" / "services" / "document_templates"
OUTPUT_PATH = ROOT / "docs" / "validation" / "document_field_matrix.md"


@dataclass(frozen=True)
class Field:
    id: str
    label: str
    pattern: str  # case-insensitive regex


# ──────────────────────────────────────────────────────────────────
# 표준 필드 정의 (bilingual EN/KR)
# ──────────────────────────────────────────────────────────────────
INVOICE_FIELDS: list[Field] = [
    Field("invoice_no", "Invoice No.", r"invoice\s*(no|number|#)|송장\s*번호|신고\s*번호"),
    Field("invoice_date", "Invoice / Issue Date", r"invoice\s*date|issue\s*date|발행일|작성일|신고일"),
    Field("shipper", "Shipper / Exporter", r"shipper|exporter|수출자|송하인|수출업자"),
    Field("consignee", "Consignee / Buyer", r"consignee|buyer|수입자|수하인|수입업자|구매자"),
    Field("notify_party", "Notify Party", r"notify\s*party|통지처"),
    Field("address", "Address", r"address|주소"),
    Field("vessel_voyage", "Vessel / Voyage", r"vessel|voyage|선박|항차"),
    Field("port_loading", "Port of Loading", r"port\s*of\s*loading|선적항|적재항"),
    Field("port_discharge", "Port of Discharge", r"port\s*of\s*discharge|양륙항|도착항"),
    Field("final_dest", "Final Destination", r"final\s*destination|최종\s*목적지|목적국|destination"),
    Field("incoterm", "Incoterms", r"incoterm|fob|cif|cfr|exw|거래조건|인도조건"),
    Field("payment_terms", "Payment Terms", r"payment\s*terms|결제\s*조건|결제\s*방법|t/?t"),
    Field("currency", "Currency", r"currency|통화|usd|eur"),
    Field("hs_code", "HS Code", r"hs\s*code|hts|hs[- ]?품목|세번"),
    Field("vin", "VIN / Chassis", r"vin|chassis|차대번호"),
    Field("description", "Description of Goods", r"description\s*of\s*goods|품명|상품명|품목"),
    Field("quantity", "Quantity", r"quantity|qty|수량"),
    Field("unit_price", "Unit Price", r"unit\s*price|단가"),
    Field("total_amount", "Total Amount", r"total\s*amount|amount|총\s*금액|총액|금액"),
    Field("country_origin", "Country of Origin", r"country\s*of\s*origin|원산지|원산국"),
    Field("bank_info", "Bank Information", r"bank|swift|iban|은행|계좌|송금"),
    Field("signature", "Signature", r"signature|stamp|서명|날인|인장|서명자"),
]

PACKING_LIST_FIELDS: list[Field] = [
    Field("invoice_ref", "Invoice Reference", r"invoice\s*(no|reference|ref)|송장|참조"),
    Field("date", "Date", r"date|발행일"),
    Field("shipper", "Shipper", r"shipper|exporter|수출자|송하인"),
    Field("consignee", "Consignee", r"consignee|수입자|수하인"),
    Field("vessel_voyage", "Vessel / Voyage", r"vessel|voyage|선박|항차"),
    Field("port_loading", "Port of Loading", r"port\s*of\s*loading|선적항"),
    Field("port_discharge", "Port of Discharge", r"port\s*of\s*discharge|양륙항"),
    Field("container_no", "Container No.", r"container\s*(no|number)|컨테이너\s*번호"),
    Field("seal_no", "Seal No.", r"seal\s*(no|number)|봉인\s*번호"),
    Field("marks_numbers", "Marks & Numbers", r"marks\s*(and|&)?\s*numbers?|기호\s*및\s*번호"),
    Field("description", "Description", r"description|품명|상품명"),
    Field("vin", "VIN per unit", r"vin|chassis|차대번호"),
    Field("quantity", "Quantity / No. of Packages", r"quantity|qty|number\s*of\s*packages|수량|포장수량"),
    Field("net_weight", "Net Weight", r"net\s*weight|순중량"),
    Field("gross_weight", "Gross Weight", r"gross\s*weight|총중량"),
    Field("measurement", "Measurement (CBM)", r"measurement|cbm|용적|체적"),
]

BL_SI_FIELDS: list[Field] = [
    Field("bl_no", "B/L No.", r"b/?l\s*(no|number)|bill\s*of\s*lading|선하증권\s*번호"),
    Field("vessel", "Vessel", r"vessel|선박"),
    Field("voyage", "Voyage No.", r"voyage|항차"),
    Field("container_no", "Container No.", r"container\s*(no|number)|컨테이너\s*번호"),
    Field("seal_no", "Seal No.", r"seal\s*(no|number)|봉인"),
    Field("shipper", "Shipper", r"shipper|송하인"),
    Field("consignee", "Consignee", r"consignee|수하인"),
    Field("notify_party", "Notify Party", r"notify\s*party|통지처"),
    Field("port_loading", "Port of Loading", r"port\s*of\s*loading|선적항"),
    Field("port_discharge", "Port of Discharge", r"port\s*of\s*discharge|양륙항"),
    Field("place_delivery", "Place of Delivery", r"place\s*of\s*delivery|delivery\s*place"),
    Field("marks_numbers", "Marks & Numbers", r"marks\s*(and|&)?\s*numbers?"),
    Field("description", "Description of Goods", r"description\s*of\s*goods|품명"),
    Field("gross_weight", "Gross Weight", r"gross\s*weight"),
    Field("measurement", "Measurement", r"measurement|cbm"),
    Field("freight", "Freight Term", r"freight|prepaid|collect|운임"),
    Field("number_originals", "Number of Originals", r"number\s*of\s*original|original\s*b/?l"),
    Field("date_of_issue", "Date of Issue", r"date\s*of\s*issue|발행일|issue\s*date"),
]

CO_FIELDS: list[Field] = [
    Field("exporter", "Exporter / Consignor", r"exporter|consignor|수출자"),
    Field("producer", "Producer", r"producer|manufacturer|제조자|생산자"),
    Field("importer", "Importer / Consignee", r"importer|consignee|수입자"),
    Field("country_origin", "Country of Origin", r"country\s*of\s*origin|원산지|원산국"),
    Field("country_destination", "Country of Destination", r"country\s*of\s*destination|목적국"),
    Field("means_transport", "Means of Transport", r"means\s*of\s*transport|운송수단|transport\s*details"),
    Field("port_loading", "Port of Loading", r"port\s*of\s*loading|선적항"),
    Field("port_discharge", "Port of Discharge", r"port\s*of\s*discharge|양륙항"),
    Field("marks_numbers", "Marks & Numbers", r"marks\s*(and|&)?\s*numbers?|기호"),
    Field("description", "Description of Goods", r"description\s*of\s*goods|품명"),
    Field("hs_code", "HS Code", r"hs\s*code|hts|tariff"),
    Field("origin_criterion", "Origin Criterion / Preference",
          r"origin\s*criterion|preference\s*criterion|criterion"),
    Field("quantity", "Quantity", r"quantity|qty|gross\s*weight|net\s*weight"),
    Field("invoice_ref", "Invoice Reference", r"invoice\s*(no|number|reference)"),
    Field("declaration", "Declaration / Certify",
          r"declaration|certify|hereby|undersigned|상기 사항|선언"),
    Field("signature", "Signature", r"signature|stamp|서명|날인"),
    Field("issuing_auth", "Issuing Authority",
          r"issuing\s*authority|certification|chamber\s*of\s*commerce|상공회의소"),
]


# ──────────────────────────────────────────────────────────────────
# Doc type → fields + 우리 템플릿 + 비교 대상 1차 자료
# ──────────────────────────────────────────────────────────────────
DOC_TYPES: dict[str, dict] = {
    "invoice": {
        "fields": INVOICE_FIELDS,
        "our_template": "invoice.html",
        "references": [
            ("KITA 수출신고필증", "korea_customs/KITA_export_declaration_form_loaded_pre.pdf"),
            ("KCS UNI-PASS FAQ", "korea_customs/UNIPASS_FAQ_2023-11-17.pdf"),
        ],
    },
    "packing_list": {
        "fields": PACKING_LIST_FIELDS,
        "our_template": "packing_list.html",
        "references": [
            ("KITA 수출신고필증", "korea_customs/KITA_export_declaration_form_loaded_pre.pdf"),
            ("Maersk B/L example", "shipping_lines/Maersk_BL_example.pdf"),
        ],
    },
    "shipping_instruction": {
        "fields": BL_SI_FIELDS,
        "our_template": "shipping_instruction.html",
        "references": [
            ("Maersk B/L example", "shipping_lines/Maersk_BL_example.pdf"),
            ("CMA CGM Paperless B/L", "shipping_lines/CMA_CGM_paperless_BL.pdf"),
        ],
    },
    "co_application": {
        "fields": CO_FIELDS,
        "our_template": "co_application.html",
        "references": [
            ("AKFTA C/O Form", "fta_co/AKFTA_certificate_of_origin_form.pdf"),
            ("Korea FTA Annex 5B", "fta_co/Korea_FTA_Annex5B_CO_format.pdf"),
        ],
    },
}


# ──────────────────────────────────────────────────────────────────
# 추출 함수
# ──────────────────────────────────────────────────────────────────
def extract_pdf_text(pdf_path: Path) -> tuple[str, str]:
    """리턴: (text, status). status ∈ {ok, empty, error}."""
    try:
        reader = PdfReader(str(pdf_path))
        parts = []
        for page in reader.pages:
            try:
                t = page.extract_text() or ""
                parts.append(t)
            except Exception:  # noqa: BLE001
                continue
        text = "\n".join(parts)
        return text, ("ok" if text.strip() else "empty")
    except Exception as e:  # noqa: BLE001
        return "", f"error: {type(e).__name__}"


_INCLUDE_RE = re.compile(r"""\{\%\s*include\s+["']([^"']+)["']\s*%\}""")


def gather_template_text(template_filename: str) -> str:
    """우리 템플릿 + include 된 partial + base + css 를 모두 합친 텍스트."""
    main_path = TEMPLATES_DIR / template_filename
    if not main_path.exists():
        return ""
    parts: list[str] = []
    seen: set[Path] = set()

    def add(p: Path) -> None:
        if p in seen or not p.exists():
            return
        seen.add(p)
        parts.append(p.read_text(encoding="utf-8"))

    add(main_path)
    add(TEMPLATES_DIR / "_base.html")
    add(TEMPLATES_DIR / "_styles.css")
    main_text = main_path.read_text(encoding="utf-8")
    for inc in _INCLUDE_RE.findall(main_text):
        add(TEMPLATES_DIR / inc)
    # HTML entity decoding so regex naturally matches "marks & numbers" etc.
    text = "\n".join(parts)
    return text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")


def check_fields(text: str, fields: list[Field]) -> dict[str, bool]:
    return {f.id: bool(re.search(f.pattern, text, re.IGNORECASE | re.UNICODE)) for f in fields}


# ──────────────────────────────────────────────────────────────────
# 매트릭스 생성
# ──────────────────────────────────────────────────────────────────
def build_report() -> tuple[str, list[dict]]:
    lines: list[str] = []
    lines.append("# Document Field Coverage Matrix\n")
    lines.append(
        "Auto-generated by `scripts/validate_document_fields.py`. "
        "Do NOT edit manually — re-run the script after updating "
        "templates or `configs/samples_registry.yaml`.\n"
    )
    lines.append(
        "**Legend**\n"
        "- ✅ label found in source\n"
        "- ❌ label missing\n"
        "- ⚠️ source could not be text-extracted (image-only PDF)\n"
        "- 🚫 source file missing on disk\n\n"
        "**Methodology:** bilingual EN/KR regex. Presence ≠ correctness, "
        "but *absence* in our template + *presence* in references = clear gap.\n"
    )

    summary: list[dict] = []

    for doc_type, cfg in DOC_TYPES.items():
        fields: list[Field] = cfg["fields"]
        our_text = gather_template_text(cfg["our_template"])
        our_check = check_fields(our_text, fields) if our_text else {f.id: False for f in fields}

        ref_results: list[tuple[str, dict[str, bool], str]] = []
        for label, rel_path in cfg["references"]:
            full = SAMPLES_DIR / rel_path
            if not full.exists():
                ref_results.append((label, {f.id: False for f in fields}, "missing"))
                continue
            text, status = extract_pdf_text(full)
            check = check_fields(text, fields) if status == "ok" else {f.id: False for f in fields}
            ref_results.append((label, check, status))

        # Section
        lines.append(f"\n## {doc_type}\n")
        lines.append(
            f"- our template: `backend/app/services/document_templates/{cfg['our_template']}`"
        )
        for label, _, status in ref_results:
            icon = "✅" if status == "ok" else ("⚠️" if status == "empty" else "🚫")
            lines.append(f"- ref: {label} — {icon} {status}")
        lines.append("")

        # Header row
        headers = ["Field", "Ours"] + [r[0] for r in ref_results]
        lines.append("| " + " | ".join(headers) + " |")
        lines.append("|" + "|".join("---" for _ in headers) + "|")

        gaps_we_miss: list[str] = []
        for f in fields:
            cells = [f.label]
            cells.append("✅" if our_check[f.id] else "❌")
            ref_present = 0
            for _, check, status in ref_results:
                if status != "ok":
                    cells.append("⚠️" if status == "empty" else "🚫")
                    continue
                if check[f.id]:
                    cells.append("✅")
                    ref_present += 1
                else:
                    cells.append("❌")
            lines.append("| " + " | ".join(cells) + " |")
            if not our_check[f.id] and ref_present > 0:
                gaps_we_miss.append(f.label)

        ours_count = sum(our_check.values())
        total = len(fields)
        lines.append(f"\n**Our coverage:** {ours_count}/{total} canonical fields\n")
        if gaps_we_miss:
            gap_list = ", ".join(f"`{g}`" for g in gaps_we_miss)
            lines.append(f"**🔴 Gaps (refs have, we miss):** {gap_list}\n")
        else:
            lines.append("**✅ No gaps detected against references.**\n")

        summary.append(
            {
                "doc_type": doc_type,
                "coverage": ours_count,
                "total": total,
                "gaps": gaps_we_miss,
                "extractable_refs": sum(1 for _, _, s in ref_results if s == "ok"),
                "total_refs": len(ref_results),
            }
        )

    # Top summary
    lines.append("\n---\n## Summary\n")
    lines.append("| Doc Type | Our Coverage | Refs Extractable | Gaps |")
    lines.append("|---|---|---|---|")
    for s in summary:
        gap_str = str(len(s["gaps"])) if s["gaps"] else "0 ✅"
        lines.append(
            f"| `{s['doc_type']}` | {s['coverage']}/{s['total']} | "
            f"{s['extractable_refs']}/{s['total_refs']} | {gap_str} |"
        )

    return "\n".join(lines) + "\n", summary


def main() -> None:
    report_md, summary = build_report()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(report_md, encoding="utf-8")
    print(f"  ✓ wrote {OUTPUT_PATH.relative_to(ROOT)}\n")

    print("  Coverage summary:")
    total_gaps = 0
    for s in summary:
        gap_n = len(s["gaps"])
        total_gaps += gap_n
        ext = f"{s['extractable_refs']}/{s['total_refs']}"
        print(
            f"    {s['doc_type']:25s}  ours={s['coverage']:>2}/{s['total']:<2}  "
            f"refs_ok={ext}  gaps={gap_n}"
        )
        if gap_n:
            for g in s["gaps"]:
                print(f"      ↳ missing: {g}")
    print(f"\n  total gaps: {total_gaps}")
    sys.exit(1 if total_gaps else 0)


if __name__ == "__main__":
    main()
