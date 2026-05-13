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

# 경쟁사 실제 사이트 — 벤치마크 비교 캡처용
# Autowini 는 Cloudflare bot 차단 → 대체로 Encar 영문판 사용 (한국 자동차 매매 No.1)
COMPETITOR_SITES = [
    ("encar", "https://www.encar.com/", "Encar (엔카 — 한국 No.1)"),
    ("beforward", "https://www.beforward.jp/", "BeForward (일본 1위, 400K차)"),
    ("sbtjapan", "https://www.sbtjapan.com/", "SBT Japan (200K+)"),
]


# ── 벤치마크/포지셔닝 슬라이드 (시연 슬라이드 앞에 삽입) ────────
BENCHMARK_SLIDES = [
    {
        "no": "A",
        "label": "BENCHMARK 1",
        "title": "한국 중고차 수출 시장 — 3-tier 구조 분석",
        "tags": "📚 시장 조사 + 멘토 ㈜하이쓰리디 인터뷰",
        "route": "사전 조사 단계",
        "html": """
<div class="narrative">
  한국 중고차 수출 시장은 <strong>3 계층</strong>으로 구분.
  대기업 (현대글로비스·롯데) 운영 자체 플랫폼은 <strong>해외 IP only</strong> · <strong>자체 차량 보유</strong>.
  영세업체는 마켓플레이스 (오토위니 등) 에 매물 올리고 메일·서류·번역은 본인이 처리.
  <strong>빈 공간 = 영세업체용 AI 자동화 SaaS.</strong>
</div>

<table class="benchmark-table">
  <thead>
    <tr>
      <th style="width:18%">계층</th>
      <th style="width:24%">대표 플랫폼</th>
      <th>특징</th>
      <th style="width:25%">접근성</th>
    </tr>
  </thead>
  <tbody>
    <tr style="background:#fff7ed">
      <td><strong>🏢 1. 대기업<br>자체 플랫폼</strong></td>
      <td><strong>Autobell Global</strong> (현대글로비스)<br>LOTTE AUTO GLOBAL (롯데렌탈)</td>
      <td>자체 차량 보유 · 검수·통관·운송 통합 · 해외 바이어 B2B 전용</td>
      <td>한국 IP 차단<br>(해외 IP only)</td>
    </tr>
    <tr>
      <td><strong>🛒 2. 마켓플레이스</strong></td>
      <td><strong>Autowini</strong> (한국 No.1, SK엔카 출신)<br>BeForward (일본 1위, 400K차)<br>SBT Japan (200K+)<br>CarFromJapan</td>
      <td>영세 셀러가 매물 올리는 채널 · 16~30개 언어 · WhatsApp 영업 (사람) · <strong>AI 자동화 거의 없음</strong></td>
      <td>Autowini Cloudflare 차단<br>나머지 캡처 OK</td>
    </tr>
    <tr style="background:#dcfce7">
      <td><strong>⭐ 3. 우리 (PoC)</strong></td>
      <td><strong>AutoExport AI</strong></td>
      <td>마켓플레이스 위에서 동작하는 <strong>영세업체용 AI SaaS</strong> — 다국어 메일·통관·컴플라이언스·4종 서류 자동화 + 한국어 검증 패널</td>
      <td>웹·로컬 사용<br>(영세 1~2인)</td>
    </tr>
  </tbody>
</table>

<div class="differentiator-list">
  <h4>📍 우리 포지셔닝 (멘토 ㈜하이쓰리디 인터뷰 기반)</h4>
  <ol>
    <li><strong>대기업과 경쟁 X</strong> — 그들은 자체 차량 보유 + 해외 IP only, 영세업체는 접근 X</li>
    <li><strong>마켓플레이스와 경쟁 X</strong> — 그 위에서 작동하는 도구 (재고 경쟁 X)</li>
    <li><strong>영세업체 1~2인 사장님</strong>이 메일·서류·번역 부담 안 지고 거래할 수 있게 함</li>
    <li>2025.10 부산경찰청 적발 — 영세업체는 OFAC·Russia-proxy 검증 사실상 불가 → AI 가 대신</li>
  </ol>
</div>
""",
    },
    {
        "no": "B-0",
        "label": "BENCHMARK 2-tour",
        "title": "Autobell Global UI 라이브 투어 — 우리 reference",
        "tags": "autobellglobal.com 라이브 캡처 · 2026-05-12",
        "route": "https://www.autobellglobal.com/",
        "html": """
<div class="narrative">
  현대글로비스 자체 운영 수출 플랫폼 (2022.1 론칭). 사이트 표시 <strong>24,801대 (Hero 시점) / 26,885 Units (Used Car Total, 2026-05-12 캡처)</strong> ·
  영어 단일언어 · 해외 바이어 B2B 전용. 헤럴드경제: 年 10만 차량 거쳐가는 K-중고차 수출 허브.
  우리 marketplace shell 의 디자인·메뉴 패턴 reference.
  <strong>실제 라이브 사이트를 4 섹션으로 캡처</strong>.
</div>

<div class="ui-grid">
  <div class="ui-cell">
    <img src="{autobell_hero}" alt="autobell hero">
    <div class="ui-cap">
      <strong>① Hero</strong> — "Autobell Global, Your Reliable Ride, Explore with Pride!" ·
      HYUNDAI GLOVIS 로고 · Used Car / About Autobell / Login / WhatsApp · Warranty Service 배너
    </div>
  </div>
  <div class="ui-cell">
    <img src="{autobell_section2}" alt="special cars">
    <div class="ui-cap">
      <strong>② Special used cars</strong> — Autobell Stock / Condition Reported / Autobell X X Car / New Arrivals 탭 ·
      차량 카드 (Mini Countryman 2.0 D 등) + FOB 가격 + Condition report 표시
    </div>
  </div>
  <div class="ui-cell">
    <img src="{autobell_section3}" alt="popular vehicles + warranty">
    <div class="ui-cap">
      <strong>③ Quality Assurance + Most popular</strong> — 101 검사항목 · Warranty Service · Global Reach 3-카드 +
      "Most popular used vehicles now" 차량 그리드 (E-Class Coupe, K3, Focus, Sonic Elina)
    </div>
  </div>
  <div class="ui-cell">
    <img src="{autobell_inventory}" alt="inventory list">
    <div class="ui-cap">
      <strong>④ Used Car 진입 페이지</strong> — "Recommended by Autobell Global" 5-카드 +
      <strong>26,885 Units in Total</strong> (사이트 카탈로그 표시, 2026-05-12 캡처 시점) · 좌측 필터 (Autobell Global Special / Condition Reported / Autobell X X Car)
    </div>
  </div>
</div>

<div class="differentiator-list">
  <h4>📍 우리가 reference 로 가져갈 점</h4>
  <ol>
    <li>Used Car / Auction / About 3-tab 메뉴 → 우리도 동일 (단순화)</li>
    <li>차량 카드 ⇒ <strong>FOB 가격 + Condition 토글 + 좌측 필터</strong> 구조 그대로</li>
    <li>Warranty / Global Reach 3-카드 trust badge → 우리는 "100+ Countries Shipped"</li>
    <li><strong>차이점</strong>: Autobell 은 자체 차량 보유, 우리는 셀러 위탁 · AI 자동화 5종 추가</li>
  </ol>
</div>
""",
    },
    {
        "no": "B-1",
        "label": "BENCHMARK 2",
        "title": "Autobell Global (현대글로비스) — 우리 reference UI",
        "tags": "autobellglobal.com 라이브 캡처 · 2026-05-12",
        "route": "직접 hero 비교",
        "html": """
<div class="narrative">
  <strong>우리 marketplace shell 의 reference UI</strong>는 <strong>현대글로비스의 Autobell Global</strong>.
  영세업체용 마켓플레이스 (오토위니) 가 아닌, <strong>대기업이 운영하는 해외 바이어 전용 수출 플랫폼</strong> 디자인을 따라감.
  바로 앞 슬라이드에서 Autobell 의 4-섹션 라이브 UI 를 봤으니, 여기서는 우리 marketplace 와 직접 비교.
</div>

<div class="compare-pair">
  <div class="compare-card competitor">
    <div class="compare-header">🏢 Autobell Global (현대글로비스)</div>
    <img src="{competitor_autobell}" alt="autobell global">
    <div class="compare-caption">
      <strong>"Autobell Global, Your Reliable Ride, Explore with Pride!"</strong><br>
      <strong>"Trusted Used Car Marketplace by Hyundai Motor Group."</strong><br>
      메뉴: Used Car · Auction · About Autobell · WhatsApp<br>
      필터: Certified Vehicles · Warranty · SUV+Diesel · 4wd 등<br>
      대기업 신뢰감 · 자체 검수·통관·운송 · 해외 IP only
    </div>
  </div>
  <div class="compare-card us">
    <div class="compare-header">📦 우리 Marketplace shell</div>
    <img src="{compare_marketplace}" alt="our marketplace">
    <div class="compare-caption">
      <strong>"Korea's Trusted Used Car Marketplace"</strong><br>
      <strong>"Korean Used Cars, Inspected & Globally Shipped"</strong><br>
      메뉴: Browse Inventory · Auction · About · Language<br>
      필터: Category · Fuel · Body · Year · Steering · Sort<br>
      <strong>Autobell Global 의 UI 패턴 따라 + 영세업체 사용 가능</strong>
    </div>
  </div>
</div>

<table class="benchmark-table" style="margin-top:6px;font-size:9pt">
  <thead>
    <tr><th style="width:22%">UI 요소</th><th>Autobell Global</th><th class="us-col">우리</th></tr>
  </thead>
  <tbody>
    <tr><td>운영주체</td><td>현대글로비스 (대기업)</td><td class="us-col">영세 1~2인 업체용 SaaS</td></tr>
    <tr><td>차량 보유</td><td>자체 (검수·통관·운송 통합)</td><td class="us-col">오토위니 등 마켓플레이스에서 끌어옴</td></tr>
    <tr><td>UI 패턴</td><td>Used Car / Auction / About</td><td class="us-col yes">동일 (Browse / Auction / About)</td></tr>
    <tr><td>다국어</td><td>English (해외 IP only)</td><td class="us-col yes">English + KR + 5 LLM 언어</td></tr>
    <tr><td>채팅</td><td>WhatsApp (사람)</td><td class="us-col yes">Quote Request → admin SaaS 자동</td></tr>
    <tr><td>차량 보증</td><td>현대 그룹 보증</td><td class="us-col">28국 1차 자료 검증 + 영세 셀러 책임</td></tr>
    <tr><td>AI 자동화</td><td class="no">0건</td><td class="us-col star">★ 5종 차별화 (메일·서류·통관·컴플라이언스)</td></tr>
  </tbody>
</table>
""",
    },
    {
        "no": "B-2",
        "label": "BENCHMARK 2",
        "title": "우리 2-Shell 아키텍처 — Autobell UI + AI 자동화",
        "tags": "Marketplace shell + Admin AI SaaS",
        "route": "/marketplace ↔ /listings",
        "html": """
<div class="narrative">
  <strong>이전 슬라이드 Autobell Global UI 패턴을 따라가되</strong>, 영세업체용으로 단순화.
  왼쪽은 Autobell 스타일 buyer 진입점, 오른쪽은 <strong>경쟁사에 없는 Admin AI SaaS</strong>
  (다국어 메일·서류·통관·컴플라이언스 자동화).
</div>

<div class="compare-pair">
  <div class="compare-card us">
    <div class="compare-header">📦 우리 Marketplace shell (Autobell-style)</div>
    <img src="{compare_marketplace}" alt="our marketplace">
    <div class="compare-caption">
      <strong>"Korea's Trusted Used Car Marketplace"</strong><br>
      Autobell Global 메뉴 구조 (Browse / Auction / About) 따라감.
      차량 카드 · 통관 매트릭스 · 10대 시드.<br>
      <strong>대기업 corporate 톤 + 영세 SME 접근성</strong>.
    </div>
  </div>
  <div class="compare-card us">
    <div class="compare-header">🤖 우리 Admin AI SaaS ⭐ 진짜 차별화</div>
    <img src="{compare_admin}" alt="our admin">
    <div class="compare-caption">
      Autobell Global · 오토위니 · BeForward <strong>어디에도 없음</strong>.<br>
      다국어 메일 + 한국어 검증 패널 + 4종 PDF + OFAC/Russia-proxy 자동 차단.<br>
      <strong>"오토위니에 매물 올린 영세 사장님이 사용하는 AI 비서"</strong>.
    </div>
  </div>
</div>

<div class="differentiator-list" style="margin-top:6px">
  <h4>🎯 narrative 한 줄</h4>
  <ol>
    <li><strong>UI</strong>: Autobell Global (현대글로비스) 디자인 패턴 따라감 (corporate 톤, Used Car / Auction / About)</li>
    <li><strong>기능</strong>: AI 자동화 5종 추가 — 어떤 경쟁사도 안 함</li>
    <li><strong>타겟</strong>: 오토위니에 매물 올리는 영세업체 1~2인 (1,000여곳, 인천 송도 중심)</li>
  </ol>
</div>
""",
    },
    {
        "no": "C",
        "label": "BENCHMARK 3",
        "title": "기능 매트릭스 — 경쟁사 vs 우리 5종 차별화",
        "tags": "Trade.gov · Trustpilot · 오토위니 공식 자료 분석",
        "route": "차별화 지점 도출",
        "html": """
<table class="benchmark-table">
  <thead>
    <tr>
      <th style="width:32%">기능</th>
      <th>BeForward</th>
      <th>SBT Japan</th>
      <th>오토위니</th>
      <th class="us-col">우리 (PoC ✓)</th>
    </tr>
  </thead>
  <tbody>
    <tr><td>검색·필터</td><td class="yes">✓</td><td class="yes">✓</td><td class="yes">✓</td><td class="us-col yes">✓</td></tr>
    <tr><td>다국어 사이트 UI</td><td>30개 언어</td><td>다국어</td><td>16개 언어</td><td class="us-col">5 LLM 언어</td></tr>
    <tr><td>WhatsApp 채팅</td><td>사람</td><td>사람</td><td class="partial">△</td><td class="us-col">AI 24/7 (Phase 2)</td></tr>
    <tr><td>VIN 디코딩</td><td class="partial">△</td><td class="partial">△</td><td class="partial">△</td><td class="us-col yes">✓ NHTSA</td></tr>
    <tr style="background:#fef9c3"><td><strong>국가별 통관 사전 검증</strong></td><td class="no">✗</td><td class="no">✗</td><td class="no">✗</td><td class="us-col star">★ 차별화 1</td></tr>
    <tr style="background:#fef9c3"><td><strong>다국어 격식 메일 자동 작성</strong></td><td class="no">✗</td><td class="no">✗</td><td class="no">✗</td><td class="us-col star">★ 차별화 2</td></tr>
    <tr style="background:#fef9c3"><td><strong>수출 서류 4종 자동 생성</strong></td><td class="partial">수동</td><td class="partial">수동</td><td class="partial">수동</td><td class="us-col star">★ 차별화 3</td></tr>
    <tr style="background:#fef9c3"><td><strong>컴플라이언스 자동 검사</strong></td><td class="no">✗</td><td class="no">✗</td><td class="no">✗</td><td class="us-col star">★ 차별화 4 (OFAC+Yestrade)</td></tr>
    <tr style="background:#fef9c3"><td><strong>한국어 검증 패널 (Level 2)</strong></td><td class="no">✗</td><td class="no">✗</td><td class="no">✗</td><td class="us-col star">★ 차별화 5 ⭐ 신규</td></tr>
    <tr><td>선적 후 추적·알림</td><td class="partial">수동</td><td class="partial">수동</td><td class="partial">수동</td><td class="us-col">Phase 2</td></tr>
    <tr><td>재고 규모</td><td>400K</td><td>200K+</td><td>다수</td><td class="us-col" style="font-size:8.5pt;color:#64748b">N/A (별도)</td></tr>
  </tbody>
</table>

<div class="differentiator-list">
  <h4>🎯 우리 5종 차별화 핵심</h4>
  <ol>
    <li><strong>오토위니/BeForward 등 모든 경쟁사가 안 하는 5가지를 자동화</strong></li>
    <li>한국 측 No.1 (오토위니) 이 16개 언어 사이트 운영하지만, <strong>메일은 본인 작성</strong></li>
    <li>일본 측 BeForward 가 400K 차량 보유하지만, <strong>사후관리 평판 악화</strong> (Trustpilot)</li>
    <li>우리는 <strong>재고 경쟁 안 함</strong> — 매물은 오토위니에, 자동화는 우리에</li>
    <li><strong>한국어 검증 패널</strong>은 어디에도 없는 신규 UX (외국어 ↔ 한국어 양방향)</li>
  </ol>
</div>
""",
    },
]


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
            "100% 일치 (#070 라이브 검증)."
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
            "외부 buyer 가 보는 마켓플레이스. 10대 차량 카드 + 28국 통관 매트릭스. "
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
        "title": "Marketplace Catalog — 10대 차량 + 다중 필터",
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
            "라이브 재검증 #074 (Round 12 후속)",
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
    # ── 제안서 docx 명시 결과물 추가 구현 (Phase 1 보강) ─────────
    {
        "no": 13,
        "title": "🆕 LLM Wiki — 28국 통관 룰 web 편집 (제안서 결과물)",
        "image_key": "12_wiki_country",
        "route": "/wiki/:code  ·  GET/POST/PUT/DELETE /api/countries[/{code}/rules]",
        "tags": "제안서 §결과물 - '사용자가 직접 LLM Wiki 편집 페이지'",
        "narrative": (
            "<strong>대표님 제안서 결과물 충족</strong>. yaml 시드 28국 외에도 web UI 에서 신규 국가 추가, "
            "Country meta + 통관 룰 (연식·핸들·검사·영사관·서류) CRUD. "
            "<code>jsonschema</code> Draft202012 input 검증 + <code>get_current_user_id</code> 인증 dep."
        ),
        "bullets": [
            "Country meta 14 필드 + Rule 20 필드 풀 폼 — chip/toggle/select 컴포넌트",
            "신규 국가 추가 모달 (예: KW 쿠웨이트), cascade rule 삭제 confirm 다이얼로그",
            "TanStack Query invalidate — 룰 엔진/메일/PDF 모두 자동 반영",
        ],
    },
    {
        "no": 14,
        "title": "🆕 시세 자동 분석 + 적정 FOB 산출 (제안서 결과물)",
        "image_key": "13_pricing",
        "route": "/vehicles/:id  ·  GET /api/vehicles/{id}/price-suggestion?destination_country=XX",
        "tags": "제안서 §결과물 - '시세 분석 및 적정 수출가 자동 산출'",
        "narrative": (
            "<strong>차량 정보 + 도착국 → 추정 FOB USD + range + 산출 근거</strong>. "
            "Hybrid: DB 동급 통계(make/model/year ±2) + body×fuel×age baseline 표 + 도착국 시장 보정. "
            "라이브 검증: 동일 차량 SY $9,539 > DO $9,106 > KG $8,238 (단가 강세 순서)."
        ),
        "bullets": [
            "Mileage / 사고이력 / Luxury 브랜드 자동 factor 적용",
            "도착국 multiplier — 시리아 +10%, 키르기스 -5% (러우회 할인) 등",
            "Confidence (high/medium/low) + 산출 근거 factor breakdown 노출",
        ],
    },
    {
        "no": 15,
        "title": "🆕 AI 에이전트 채팅 + MCP 서버 (제안서 결과물 2종)",
        "image_key": "14_chat_mcp",
        "route": "/chat  ·  POST /api/agent/chat  ·  GET/POST /api/mcp/tools/{list,call}",
        "tags": "제안서 §결과물 - '채팅 기반 대시보드 UI' + 'Claude Code + MCP'",
        "narrative": (
            "<strong>자연어 채팅 → MCP tool 자동 라우팅</strong>. "
            "키워드 패턴 fast-path (28국 화이트리스트로 false positive 차단) + LLM fallback. "
            "10 tools (decode_vin, lookup_country_rules, check_compliance, suggest_price, "
            "check_ofac_sdn, evaluate_import, list_vehicles 등) MCP 표준 호환 — "
            "<strong>Claude Desktop / Cline 등 외부 MCP client 도 동일 호출 가능</strong>."
        ),
        "bullets": [
            "/api/mcp/tools/list — Anthropic tool-use + MCP tools/list 표준 JSON Schema",
            "Tool call trace 표시 + 후속 액션 추천 버튼 (Wiki / 매물 등)",
            "Smoke test 25 케이스 통과 — false positive ('OK 룰', 'US 통관') 차단 검증 ✓",
        ],
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


def capture_competitors(page: Page) -> None:
    """경쟁사 실제 사이트 자동 캡처 — 벤치마크 비교 슬라이드용.

    봇 차단 회피 위해 user_agent 일반 브라우저로 설정, 충분한 wait.
    실패해도 PoC narrative 영향 없음 (graceful — 캡처 누락 시 placeholder).
    """
    for key, url, label in COMPETITOR_SITES:
        path = CAPTURES_DIR / f"competitor_{key}.png"
        if path.exists():
            logger.info(f"  → skip {key} (캐시됨: {path.name})")
            continue
        try:
            logger.info(f"  → goto competitor {label}: {url}")
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            # 외부 사이트는 광고/lazy-load 로 networkidle 안 됨 → 고정 wait
            page.wait_for_timeout(6000)
            page.screenshot(path=str(path), full_page=False, type="png", timeout=30000)
            logger.info(f"  ✓ captured {path.name}")
        except Exception as e:  # noqa: BLE001
            logger.warning(f"  ✗ competitor {key} 캡처 실패: {type(e).__name__}: {e}")
            # 실패해도 다음 진행


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
        # 봇 차단 회피용 일반 브라우저 user agent
        context = browser.new_context(
            viewport=VIEWPORT,
            locale="ko-KR",
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
            ),
        )
        page = context.new_page()

        logger.info("=== 0) Competitor sites (벤치마크용) ===")
        capture_competitors(page)

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

        # ── 제안서 docx 결과물 추가 구현 캡처 ─────────────────
        logger.info("=== 12) LLM Wiki — DO 국가 편집 페이지 ===")
        # /wiki 목록보다 /wiki/DO 편집이 더 임팩트 (Country meta + Rules CRUD)
        page.goto(f"{FRONTEND_URL}/wiki/DO", wait_until="domcontentloaded")
        page.wait_for_timeout(2500)
        capture(page, "12_wiki_country", full_page=True)

        logger.info("=== 13) 시세 자동 산출 — VehicleDetail 우측 위젯 ===")
        # admin VehicleDetail 우측 PriceSuggestion 카드. KG 도착국 선택 후 캡처.
        page.goto(f"{FRONTEND_URL}/vehicles/{vehicle_id}", wait_until="domcontentloaded")
        page.wait_for_timeout(3000)
        # PriceSuggestion 카드로 스크롤 — '적정 수출가 산출' 텍스트 기준
        try:
            price_card = page.locator('text="적정 수출가 산출"').first
            price_card.scroll_into_view_if_needed(timeout=5000)
            page.wait_for_timeout(800)
            # 도착국 KG 선택 (할인 시연)
            page.locator('select').nth(0).select_option("KG")
            page.wait_for_timeout(1500)
        except Exception as e:  # noqa: BLE001
            logger.warning(f"  price card scroll/select 실패: {e}")
        capture(page, "13_pricing")

        logger.info("=== 14) AI 에이전트 채팅 + MCP tools 사이드바 ===")
        page.goto(f"{FRONTEND_URL}/chat", wait_until="domcontentloaded")
        page.wait_for_timeout(2000)
        # 빠른 prompt 1개 클릭해서 결과 + tool_call trace 가 같이 보이게
        try:
            btn = page.locator('button:has-text("DO 통관 가능 조건")').first
            btn.click(timeout=5000)
            page.wait_for_timeout(2500)  # API 응답 대기
        except Exception as e:  # noqa: BLE001
            logger.warning(f"  chat quick prompt 실패: {e}")
        capture(page, "14_chat_mcp", full_page=True)

        browser.close()
        logger.info("스크린샷 캡처 완료.")

    # 4. HTML 렌더링 → PDF
    logger.info("=== PDF 생성 ===")
    generate_pdf()


def _to_data_url(img_path: Path) -> str:
    if not img_path.exists():
        return ""
    with img_path.open("rb") as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode("ascii")


def generate_pdf() -> None:
    """캡처된 PNG 를 HTML 에 base64 inline → Playwright PDF.

    슬라이드 순서: 표지 → 30초 컷 → BENCHMARK 3 슬라이드 → 시연 11 슬라이드
    → 핵심 지표 → 차별화 결론.
    """
    env = Environment(
        loader=FileSystemLoader(str(SCRIPTS_DIR)),
        autoescape=select_autoescape(enabled_extensions=("html",)),
    )
    template = env.get_template("demo_pdf_template.html")

    # 벤치마크 슬라이드의 image placeholder 치환
    placeholders = {
        "{compare_marketplace}": _to_data_url(CAPTURES_DIR / "02_marketplace_landing.png"),
        "{compare_admin}": _to_data_url(CAPTURES_DIR / "07_mail_korean_panel.png"),
        "{competitor_autobell}": _to_data_url(CAPTURES_DIR / "competitor_autobell.png"),
        "{autobell_hero}": _to_data_url(CAPTURES_DIR / "competitor_autobell.png"),
        "{autobell_section2}": _to_data_url(CAPTURES_DIR / "competitor_autobell_section2.png"),
        "{autobell_section3}": _to_data_url(CAPTURES_DIR / "competitor_autobell_section3.png"),
        "{autobell_inventory}": _to_data_url(CAPTURES_DIR / "competitor_autobell_inventory.png"),
        "{competitor_autowini}": _to_data_url(CAPTURES_DIR / "competitor_autowini.png"),
        "{competitor_encar}": _to_data_url(CAPTURES_DIR / "competitor_encar.png"),
        "{competitor_beforward}": _to_data_url(CAPTURES_DIR / "competitor_beforward.png"),
        "{competitor_sbtjapan}": _to_data_url(CAPTURES_DIR / "competitor_sbtjapan.png"),
    }

    benchmark_with_images = []
    for s in BENCHMARK_SLIDES:
        html_content = s.get("html", "")
        for key, val in placeholders.items():
            html_content = html_content.replace(key, val)
        benchmark_with_images.append({**s, "html": html_content, "image": ""})

    # 시연 슬라이드: 이미지 base64 inline
    demo_with_images = []
    for s in SLIDES:
        img_path = CAPTURES_DIR / f"{s['image_key']}.png"
        img_data = _to_data_url(img_path)
        if img_data:
            logger.info(f"  inline {img_path.name}: {img_path.stat().st_size // 1024} KB")
        demo_with_images.append({**s, "image": img_data})

    all_slides = benchmark_with_images + demo_with_images

    html = template.render(
        slides=all_slides,
        total_pages=len(all_slides) + 5,
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
    logger.info(f"   크기: {size_kb} KB / 페이지 추정: ~{len(SLIDES) + 5}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description="자동 UI 캡처 + 발표 PDF 생성 (Playwright + Jinja2)"
    )
    parser.add_argument(
        "--pdf-only",
        action="store_true",
        help="캡처 단계 건너뛰고 기존 demo_captures/ 의 PNG 로 PDF 만 재생성 (backend 불필요)",
    )
    args = parser.parse_args()

    if args.pdf_only:
        if not CAPTURES_DIR.exists() or not list(CAPTURES_DIR.glob("*.png")):
            logger.error(f"{CAPTURES_DIR} 에 PNG 없음. --pdf-only 사용 전 한번은 전체 실행 필요.")
            sys.exit(1)
        logger.info("PDF only 모드 — 캡처 단계 건너뜀.")
        generate_pdf()
    else:
        main()
