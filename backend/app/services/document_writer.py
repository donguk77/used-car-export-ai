"""수출 서류 4종 PDF 자동 생성 — Jinja2 + Playwright(헤드리스 Chromium).

docs/userflow_and_erd.md 시나리오 4. 한글·아랍어 등 모든 언어 지원.
실제 레이아웃은 backend/app/services/document_templates/*.html 에서 관리.

generate_all() 호출 시 4종을 한 번에 만들어 dict[doc_type, bytes] 로 반환.
브라우저 인스턴스는 1번만 띄워서 재사용한다 (대량 생성 시 속도 차이 큼).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Literal

from jinja2 import Environment, FileSystemLoader, select_autoescape
from playwright.sync_api import Browser, sync_playwright

DocType = Literal["invoice", "packing_list", "shipping_instruction", "co_application"]

TEMPLATE_FILES: dict[DocType, str] = {
    "invoice": "invoice.html",
    "packing_list": "packing_list.html",
    "shipping_instruction": "shipping_instruction.html",
    "co_application": "co_application.html",
}

TEMPLATES_DIR = Path(__file__).parent / "document_templates"

_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(enabled_extensions=("html",)),
    trim_blocks=True,
    lstrip_blocks=True,
)


# ── 데이터 컨테이너 ────────────────────────────────────────────────────
@dataclass
class DocumentInput:
    """4종 서류 모두에 필요한 통합 데이터."""

    invoice_no: str
    invoice_date: date

    # Shipper
    shipper_name: str
    shipper_address: str
    shipper_phone: str
    shipper_business_no: str

    # Consignee
    consignee_name: str
    consignee_contact: str
    consignee_address: str
    consignee_country: str
    consignee_tax_id: str

    # Vehicle
    make: str
    model: str
    year: int
    vin: str
    body_type: str
    fuel_type: str
    engine_cc: int
    color: str
    mileage_km: int
    hs_code: str
    net_weight_kg: int
    gross_weight_kg: int

    # Pricing
    unit_price_usd: float
    quantity: int = 1
    currency: str = "USD"

    # Shipping
    incoterm: str = "CIF"
    payment_terms: str = "T/T 100% advance"
    port_of_loading: str = "Incheon, Korea"
    port_of_discharge: str = ""
    final_destination: str = ""
    vessel_name: str | None = None
    voyage_no: str | None = None
    shipping_method: str = "Container"  # Container | RoRo
    container_no: str | None = None
    seal_no: str | None = None

    notify_party: str | None = None

    # Bank
    bank_name: str = ""
    bank_swift: str = ""
    bank_account: str = ""

    # FTA / C/O
    fta_used: str | None = None
    producer: str | None = None  # FTA C/O 시 제조자 (수출자와 다를 때만)
    origin_criterion: str | None = None  # 예: "WO" / "PE" / "PSR" — FTA 별 다름

    @property
    def total_usd(self) -> float:
        return float(self.unit_price_usd) * self.quantity


# ── HTML 렌더 ──────────────────────────────────────────────────────────
def render_html(doc_type: DocType, d: DocumentInput) -> str:
    template = _env.get_template(TEMPLATE_FILES[doc_type])
    return template.render(d=d, doc_type=doc_type)


# ── HTML → PDF (Playwright) ────────────────────────────────────────────
_PDF_OPTIONS = {
    "format": "A4",
    "margin": {"top": "0", "right": "0", "bottom": "0", "left": "0"},  # CSS @page 가 처리
    "print_background": True,
    "prefer_css_page_size": True,
}


def _html_to_pdf(browser: Browser, html: str) -> bytes:
    page = browser.new_page()
    try:
        # 정적 HTML + 폰트 CDN 한 번 로드라 "load" 면 충분 (networkidle 보다 ~3초 빠름)
        page.set_content(html, wait_until="load", timeout=20_000)
        return page.pdf(**_PDF_OPTIONS)
    finally:
        page.close()


def generate(doc_type: DocType, d: DocumentInput) -> bytes:
    html = render_html(doc_type, d)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            return _html_to_pdf(browser, html)
        finally:
            browser.close()


def generate_all(d: DocumentInput) -> dict[DocType, bytes]:
    """4종을 한 번의 브라우저 세션으로 모두 생성."""
    results: dict[DocType, bytes] = {}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            for doc_type in TEMPLATE_FILES:
                results[doc_type] = _html_to_pdf(browser, render_html(doc_type, d))
        finally:
            browser.close()
    return results
