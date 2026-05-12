"""자동 데모 캡처 + 발표 PDF 생성.

Playwright 로 frontend (:5173) 의 핵심 화면들을 스크린샷 → Jinja2 HTML 결합
→ Playwright PDF 출력. mentor 에게 메일 첨부할 발표용 PDF 1개.

사용법:
    1. backend 실행 (:8000)
    2. frontend dev 서버 실행 (:5173)
    3. python scripts/generate_demo_pdf.py
    4. ./demo_captures/ 에 PNG, ./capstone_demo.pdf 생성

요구사항:
    - playwright (이미 backend requirements 에 있음)
    - jinja2 (동일)
    - requests (API 호출용)
"""

from __future__ import annotations

import base64
import logging
import sys
import time
from pathlib import Path

import requests
from jinja2 import Environment, FileSystemLoader, select_autoescape
from playwright.sync_api import Page, sync_playwright

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

FRONTEND_URL = "http://localhost:5173"
BACKEND_URL = "http://localhost:8000"

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CAPTURES_DIR = PROJECT_ROOT / "demo_captures"
SCRIPTS_DIR = Path(__file__).resolve().parent
OUTPUT_PDF = PROJECT_ROOT / "capstone_demo.pdf"

VIEWPORT = {"width": 1400, "height": 900}


# ── 시연 슬라이드 정의 ──────────────────────────────────────────
SLIDES = [
    {
        "no": 2,
        "title": "Admin Dashboard — 거짓말 안 하는 대시보드",
        "image_key": "01_dashboard",
        "route": "GET /api/dashboard/summary",
        "tags": "9/9 DB 정합성 검증 (#070)",
        "narrative": (
            "관리자 첫 화면. <strong>9개 핵심 지표</strong> + 최근 5건 거래 + "
            "컴플라이언스 알림. 모든 카운트가 SQL group_by + sum 으로 DB 진실과 "
            "100% 일치 (Round 20 검증)."
        ),
        "bullets": [
            "차량 / 바이어 / 거래 단계별 실시간 카운트",
            "최근 5건 거래 → status icon (blocked/in-progress/delivered)",
            "Compliance 경고 buyer 자동 표시",
        ],
    },
    {
        "no": 3,
        "title": "Marketplace — Autobell-style 외부 진입점",
        "image_key": "02_marketplace_landing",
        "route": "/marketplace",
        "tags": "Marketplace + Admin 2-shell architecture",
        "narrative": (
            "외부 buyer 가 보는 마켓플레이스. 33대 차량 카드 + 28국 통관 매트릭스. "
            "Autobell / BeForward 같은 기존 플랫폼 위에서 동작하는 도구로 포지셔닝."
        ),
        "bullets": [
            "Hero search + Featured cars + 100+ Countries Shipped 신뢰 표시",
            "Auction module 등 Phase 2 기능은 DemoModal 로 솔직히 안내",
            "Mobile responsive (Phase 2 햄버거 메뉴)",
        ],
    },
    {
        "no": 4,
        "title": "Marketplace Catalog — 33대 차량 + 다중 필터",
        "image_key": "03_marketplace_catalog",
        "route": "/marketplace/catalog",
        "tags": "TanStack Query · client-side 필터",
        "narrative": (
            "카테고리 / 연료 / 차종 / 연식 / 핸들 / 정렬 6종 필터. "
            "검색 가능. 카드 하트는 DemoModal 로 PoC 스코프 안내 (single-user)."
        ),
    },
    {
        "no": 5,
        "title": "Vehicle Detail + 28국 통관 매트릭스 실시간",
        "image_key": "04_vehicle_detail",
        "route": "/marketplace/{id}",
        "tags": "useQueries 23개 병렬 통관 평가",
        "narrative": (
            "단일 차량 페이지. 우측 통관 매트릭스가 <strong>28국 평가가능 23국</strong> 을 "
            "실시간 평가 (auto-blocked 5국 ZA/MM/TH/MY/SD 제외). <code>Request Quote</code> "
            "클릭 시 모달 오픈."
        ),
        "bullets": [
            "Spec / Image / Country Matrix 한 화면에",
            "각 국가별 OK / 차단 / 경고 + 사유 토글",
            "Round 15 #A1 해소 (5국 → 28국 동적)",
        ],
    },
    {
        "no": 6,
        "title": "Quote Request 모달 — 28국 드롭다운 + 시연 narrative",
        "image_key": "05_quote_request_modal",
        "route": "POST /api/listings",
        "tags": "Marketplace ↔ Admin 통합 (#057)",
        "narrative": (
            "<strong>Marketplace 견적 요청이 admin 시스템에 inquiry 거래로 자동 등록</strong>. "
            "도착국은 free-text Input 이 아닌 28국 dropdown (오타 방지, "
            "자동차단국 비활성). 바이어 sanctioned 시 경고 패널 표시."
        ),
        "bullets": [
            "바이어 선택 → 도착국 자동 inject (변경 가능)",
            "Blocked 바이어 dropdown 에서 자동 제외",
            "Round 16 E2E 검증 — listings 5 → 6 자동 추가",
        ],
    },
    {
        "no": 7,
        "title": "Admin Listing Detail — 메일·서류·상태 한 화면",
        "image_key": "06_listing_detail",
        "route": "/listings/{id}",
        "tags": "FSM 12 상태 + 메일/PDF 통합",
        "narrative": (
            "관리자가 거래 처리하는 메인 화면. 상단 status 전환 (next states 동적 표시), "
            "좌측 메일 작성 + 메일 history + PDF 생성, 우측 거래 메타 + compliance mini-card. "
            "Status 잘못된 전환은 100% 차단 (Round 17 #060)."
        ),
    },
    {
        "no": 8,
        "title": "🌟 다국어 메일 + 한국어 검증 패널 (Level 1+2)",
        "image_key": "07_mail_korean_panel",
        "route": "POST /api/listings/{id}/mail-draft (+ translation)",
        "tags": "Level 1 read-only · Level 2 양방향 + Strict 모드",
        "narrative": (
            "<strong>핵심 차별화</strong>. 좌측 외국어 (발송용 · 편집 가능, AR 은 RTL) ↔ "
            "우측 한국어 (검증·편집 가능). 사장님이 한국어로 의도 수정 → "
            "<code>한국어로 외국어 재생성</code> 버튼 → 30초 후 외국어 새로 + 한국어 재번역. "
            "Strict 모드는 톤·오타 보정 안 함 (계약 워딩 통제)."
        ),
        "bullets": [
            "5국 4언어 (en/es/ar/ru) 격식체 native + 회사명 자동 inject",
            "3-tier markdown 방어: prompt + post-process + placeholder fallback",
            "5 동시 메일 생성 wall 15초 (5x speedup, Round 19 #067)",
        ],
    },
    {
        "no": 9,
        "title": "메일 history + Mock SMTP — '보내기' 클릭 시연",
        "image_key": "08_mail_history",
        "route": "GET/POST /api/listings/{id}/messages",
        "tags": "audit trail + 409/400/404 edge cases",
        "narrative": (
            "ListingDetail 의 mail history 섹션. draft / sent 카운트 + status icon. "
            "<code>보내기</code> 클릭 → Mock SMTP (콘솔 로그 + sent_at 마킹) → 즉시 SENT 배지. "
            "<strong>Phase 2 aiosmtplib 한 줄 교체로 실제 발송 가능</strong>. "
            "이미 sent → 409, 같은 send pending 중 다른 클릭 → race 차단."
        ),
    },
    {
        "no": 10,
        "title": "수출 서류 4종 PDF 자동 생성",
        "image_key": "09_documents",
        "route": "POST /api/listings/{id}/documents",
        "tags": "Jinja2 + Playwright headless Chromium",
        "narrative": (
            "Invoice / Packing List / Shipping Instruction / C/O Application 동시 생성. "
            "다른 listings 동시 호출 wall 7.5초 (병렬), 같은 listing 동시 호출은 "
            "<code>with_for_update</code> lock 으로 직렬화 (정합성 보장, Document.version 자동 increment)."
        ),
        "bullets": [
            "4종 PDF 약 7초 (Playwright Chromium 1회 인스턴스 재사용)",
            "Document.version v1 → v2 → v3 audit trail",
            ".tmp 파일 → atomic rename → DB commit 원자성 보장",
        ],
    },
    {
        "no": 11,
        "title": "Compliance — KG + Genesis G80 자동 차단 demo",
        "image_key": "10_compliance",
        "route": "POST /api/listings/import-check",
        "tags": "OFAC SDN + Russia-proxy + Yestrade",
        "narrative": (
            "<strong>2025.10 부산경찰청 적발 패턴 자동 차단</strong>. KG bayer + 3,300cc + $58k 차량 → "
            "<code>russia_proxy_country</code> (warning) + <code>russia_proxy_strategic</code> (blocked) + "
            "<code>new_buyer_high_value</code> (warning) <strong>3-layer stacking</strong> + "
            "7개 필요 서류 자동 안내 (end_user_certificate, situational_license, translation_ru 등). "
            "Overall: blocked, score 20."
        ),
        "bullets": [
            "OFAC SDN 18,947건 exact + fuzzy match (rapidfuzz, threshold 85)",
            "Yestrade demo stub (Phase 2 사업자 인증서 통합)",
            "Round 23 라이브 재검증 #074",
        ],
    },
    {
        "no": 12,
        "title": "Settings — 회사 정보 + 신규 거래 기본값",
        "image_key": "11_settings",
        "route": "GET/PATCH /api/users/me",
        "tags": "Phase 2 안내 카드",
        "narrative": (
            "회사명 / 사업자번호 / 주소 / 기본 선적항 (7개) / 기본 메일 언어 (5개) / 기본 통화 (6개). "
            "메일 생성 시 회사명 자동 inject (시그니처 placeholder 방지). "
            "Phase 2 안내 카드: 비밀번호 변경 + JWT / LLM provider 선택 / 회사 로고 / API 토큰."
        ),
    },
]


# ── 캡처 함수 ──────────────────────────────────────────────────
def wait_settle(page: Page, ms: int = 1200) -> None:
    """네트워크 안정 + 추가 settle (애니메이션, font 로드 대비)."""
    try:
        page.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        pass
    page.wait_for_timeout(ms)


def capture(page: Page, name: str, *, url: str | None = None, full_page: bool = False) -> Path:
    if url:
        logger.info(f"  → goto {url}")
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
    wait_settle(page)
    path = CAPTURES_DIR / f"{name}.png"
    # screenshot timeout 도 길게 (full_page 시 큰 캔버스 + CountryMatrix 23 호출 안정화)
    page.screenshot(path=str(path), full_page=full_page, type="png", timeout=60000)
    logger.info(f"  ✓ captured {path.name}")
    return path


def safe_click(page: Page, selector: str, timeout: int = 10000) -> bool:
    try:
        page.locator(selector).first.click(timeout=timeout)
        return True
    except Exception as e:
        logger.warning(f"  click fail '{selector}': {e}")
        return False


def main() -> None:
    CAPTURES_DIR.mkdir(exist_ok=True)
    logger.info(f"Captures dir: {CAPTURES_DIR}")

    # 1. backend / frontend health
    try:
        r = requests.get(f"{BACKEND_URL}/health", timeout=3)
        if r.status_code != 200:
            raise RuntimeError(f"backend health: {r.status_code}")
        r = requests.get(FRONTEND_URL, timeout=3)
        if r.status_code != 200:
            raise RuntimeError(f"frontend: {r.status_code}")
    except Exception as e:
        logger.error(f"환경 점검 실패: {e}")
        logger.error("backend (:8000) 와 frontend (:5173) 가 모두 실행 중이어야 합니다.")
        sys.exit(1)

    # 2. 시연 데이터 ID 가져오기
    listings = requests.get(f"{BACKEND_URL}/api/listings", timeout=10).json()
    vehicles = requests.get(f"{BACKEND_URL}/api/vehicles", timeout=10).json()

    if not listings or not vehicles:
        logger.error("listings 또는 vehicles 가 비어있음. seed 먼저 실행.")
        sys.exit(1)

    # LY (Sahara Auto Trading) 또는 첫 listing
    target_listing = next(
        (l for l in listings if l.get("destination_country") == "LY"),
        listings[0],
    )
    listing_id = target_listing["id"]
    vehicle_id = vehicles[0]["id"]
    logger.info(f"Demo target listing: {listing_id} ({target_listing.get('destination_country')})")

    # 3. Playwright 실행
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport=VIEWPORT, locale="ko-KR")
        page = context.new_page()

        logger.info("=== 1) Dashboard ===")
        capture(page, "01_dashboard", url=f"{FRONTEND_URL}/")

        logger.info("=== 2) Marketplace Landing ===")
        capture(page, "02_marketplace_landing", url=f"{FRONTEND_URL}/marketplace")

        logger.info("=== 3) Marketplace Catalog ===")
        capture(page, "03_marketplace_catalog", url=f"{FRONTEND_URL}/marketplace/catalog")

        logger.info("=== 4) Vehicle Detail ===")
        capture(page, "04_vehicle_detail", url=f"{FRONTEND_URL}/marketplace/{vehicle_id}")

        logger.info("=== 5) Quote Request modal ===")
        # 차량 상세에서 Request Quote 버튼 클릭
        if safe_click(page, 'button:has-text("Request Quote")'):
            page.wait_for_timeout(800)
            capture(page, "05_quote_request_modal")
            # 닫기
            safe_click(page, 'button[aria-label="닫기"]')
            page.wait_for_timeout(400)
        else:
            logger.warning("Request Quote 버튼 못 찾음 — vehicle detail 그대로 사용")

        logger.info("=== 6) Listing Detail (full page) ===")
        capture(page, "06_listing_detail", url=f"{FRONTEND_URL}/listings/{listing_id}", full_page=True)

        logger.info("=== 7) Mail history section ===")
        # 6번 캡처에서 메일 history 섹션이 포함됨
        # 추가로 mail composer 부분만 따로 캡처
        page.goto(f"{FRONTEND_URL}/listings/{listing_id}")
        wait_settle(page)
        # mail composer 섹션 (다국어 메일 작성) 영역 캡처
        mail_card = page.locator('text="다국어 메일 작성"').first
        try:
            mail_card.scroll_into_view_if_needed(timeout=5000)
            page.wait_for_timeout(500)
        except Exception:
            pass
        capture(page, "07_mail_korean_panel")

        # 메일 history 섹션
        history_card = page.locator('text="메일 history"').first
        try:
            history_card.scroll_into_view_if_needed(timeout=5000)
            page.wait_for_timeout(500)
        except Exception:
            pass
        capture(page, "08_mail_history")

        # 서류 4종 섹션
        docs_card = page.locator('text="수출 서류 4종"').first
        try:
            docs_card.scroll_into_view_if_needed(timeout=5000)
            page.wait_for_timeout(500)
        except Exception:
            pass
        capture(page, "09_documents")

        logger.info("=== 10) Compliance — Genesis + KG (admin VehicleDetail) ===")
        # Genesis G80 vehicle id 찾기
        genesis = next(
            (v for v in vehicles if v.get("model") == "G80"),
            vehicles[0],
        )
        page.goto(f"{FRONTEND_URL}/vehicles/{genesis['id']}", wait_until="domcontentloaded")
        # CountryMatrix 28국 evaluate 가 진행 — networkidle 기다리지 말고
        # 충분히 wait_for_timeout 으로 안정화 후 viewport 만 캡처 (full_page X)
        page.wait_for_timeout(8000)
        path = CAPTURES_DIR / "10_compliance.png"
        page.screenshot(path=str(path), full_page=False, type="png", timeout=60000)
        logger.info(f"  ✓ captured {path.name}")

        logger.info("=== 11) Settings ===")
        capture(page, "11_settings", url=f"{FRONTEND_URL}/settings")

        browser.close()
        logger.info("스크린샷 캡처 완료.")

    # 4. HTML 렌더링 → PDF
    logger.info("=== PDF 생성 ===")
    generate_pdf()


def generate_pdf() -> None:
    """캡처된 PNG 를 HTML 에 base64 inline → Playwright PDF."""
    env = Environment(
        loader=FileSystemLoader(str(SCRIPTS_DIR)),
        autoescape=select_autoescape(enabled_extensions=("html",)),
    )
    template = env.get_template("demo_pdf_template.html")

    # 슬라이드별 이미지 base64 inline
    slides_with_images = []
    for s in SLIDES:
        img_path = CAPTURES_DIR / f"{s['image_key']}.png"
        img_data = ""
        if img_path.exists():
            with img_path.open("rb") as f:
                img_data = "data:image/png;base64," + base64.b64encode(f.read()).decode("ascii")
            logger.info(f"  inline {img_path.name}: {img_path.stat().st_size // 1024} KB")
        slides_with_images.append({**s, "image": img_data})

    html = template.render(
        slides=slides_with_images,
        total_pages=len(SLIDES) + 4,
    )

    # 디버그용 HTML 저장
    html_path = CAPTURES_DIR / "_assembled.html"
    html_path.write_text(html, encoding="utf-8")
    logger.info(f"  HTML 조립: {html_path.name} ({len(html) // 1024} KB)")

    # Playwright 로 HTML → PDF
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        page.set_content(html, wait_until="networkidle")
        page.pdf(
            path=str(OUTPUT_PDF),
            format="A4",
            margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
            print_background=True,
        )
        browser.close()

    size_kb = OUTPUT_PDF.stat().st_size // 1024
    logger.info(f"✅ PDF 생성 완료: {OUTPUT_PDF}")
    logger.info(f"   크기: {size_kb} KB / 페이지 추정: ~{len(SLIDES) + 4}")


if __name__ == "__main__":
    main()
