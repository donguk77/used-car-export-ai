# 중고차 수출 AI 에이전트

> 한국 영세 중고차 수출업체용 AI 자동화 SaaS — 한양대학교 ERICA × ㈜하이쓰리디 캡스톤 PoC

[![Status](https://img.shields.io/badge/Status-PoC%20Demo%20Ready-success)]() [![Findings](https://img.shields.io/badge/Validated%20Findings-70+-blue)]() [![Coverage](https://img.shields.io/badge/Countries-28-orange)]()

---

## 30초 컷

| 문제 | 해결 |
|------|------|
| 한국 영세 중고차 수출업체 1~2인 운영 — 영어/아랍어/스페인어/러시아어 응대 + 28국 통관 규제 + 컴플라이언스 추적 사람이 다 처리 | **AI Agent** 가 다국어 메일·수출 서류·통관 룰 평가·컴플라이언스 차단을 자동화 |
| 2025.10 부산경찰청 키르기스스탄 우회수출 적발 — 영세업체 OFAC/Yestrade 검증 사실상 불가 | **OFAC SDN 18,947건 + fuzzy match + Russia-proxy 5국** 자동 차단 |
| Arabic/Russian 메일이 잘 작성됐는지 사용자가 검증 불가 | **한국어 검증 패널** — 외국어 ↔ 한국어 양방향 (Level 2: 한국어 수정 → 외국어 재생성) |

---

## 핵심 기능 5종 (시연 시나리오)

| # | 기능 | 동작 시간 |
|---|------|----------|
| 1 | **차량 등록 + NHTSA VIN 자동 디코딩** | ~2초 (NHTSA vPIC API) |
| 2 | **바이어 등록 + 자동 컴플라이언스** (OFAC SDN exact/fuzzy, Russia-proxy, Yestrade) | ~700ms |
| 3 | **AI 다국어 메일 작성** (5국 4언어: en/es/ar/ru) — 옵션: 한국어 검증 패널 | ~15초 (단일) / ~30초 (한국어 번역 포함) |
| 4 | **수출 서류 4종 자동 생성 PDF** (Invoice/PL/SI/CO) | ~7초 (5건 동시 → 8초 병렬화) |
| 5 | **거래 상태 머신 12 단계** (inquiry → quoted → ... → delivered) + Mock SMTP send | <100ms (전환) |

---

## 검증 완료

21 라운드 ⨯ **70+ findings** 라이브 검증 (`docs/validation/findings.md`)

- ✅ **28국 1차 자료** cross-validate (관세·운임·통관·언어 매트릭스)
- ✅ **컴플라이언스 multi-finding stacking** (KG+Genesis G80 → 3-layer blocked, 7 documents)
- ✅ **5x mail 동시 생성**: wall 15.2초 (5x speedup, async I/O)
- ✅ **PDF 동시성**: 다른 listings 7.5s 병렬, 같은 listing `with_for_update` 직렬화 (16.2s)
- ✅ **다국어 품질 sample**: AR/ES/RU/EN 격식 표현 native, 평균 2,006 chars
- ✅ **권한 격리**: 모든 endpoint user_id 필터 100% 적용
- ✅ **에러 stack trace 노출 0건**, CORS dev/prod allowlist, dependency 12개 latest stable

---

## 다음 단계 (Phase 2)

PoC 검증을 마치고, 실 사업화 / 추가 협업으로 넘어가기 전 풀어야 할 항목과 확장 아이디어.

### 사업화 직전 풀어야 할 것

- **실제 SMTP 발송** — Mock 콘솔 로그 → `aiosmtplib` + Mailgun/SendGrid (1줄 교체)
- **JWT 인증 + Multi-tenant 격리** — 모든 endpoint user_id 필터 검증 완료, 내부만 JWT 로 교체
- **OFAC SDN 자동 갱신** — cron 또는 startup background task
- **Yestrade 정식 API** — 사업자 인증서 + 우려거래자 자동 차단
- **WhatsApp Business API** — 메일 외 채널, AI 응대로 BeForward/SBT 대비 차별화
- **실시간 shipment tracking** — MarineTraffic/Maersk + 도착 24h 전 자동 알림
- **Security headers + HSTS + Dependabot** — 표준 보안 헤더, 의존성 모니터링

### 확장 아이디어 — 들어가면 좋을 기능

영세업체 사장님의 일상 업무를 더 좁혀가는 방향:

- **차량 사진 자동 보정** — 배경 제거·색감 보정 (Imagen·Firefly), 카탈로그 퀄리티 균질화
- **동급 차량 시세 가이드** — 매물 등록 시 적정 FOB 자동 추천 (엔카·KB차차차 시세 + 자체 통계)
- **환율·환차손 자동 처리** — KRW↔USD 자동 환산, 메일/Invoice 발송 시점 환율 lock
- **클레임/분쟁 관리 모듈** — 도착 후 바이어 클레임 사진/영상 업로드 → 대응 메일 자동
- **매출/운영 리포트** — 월별·국가별·차종별 listings 통계 + 수익 분석
- **다중 셀러 협업 모드** — 영세업체 N개 한 플랫폼 공유 (장기, 시장 검증 후)

> 세부 공수 추정·우선순위 매트릭스는 [docs/PHASE_2_ROADMAP.md](docs/PHASE_2_ROADMAP.md) 참조.

---

## 기술 스택

| 영역 | 기술 |
|------|------|
| **Backend** | FastAPI · SQLAlchemy 2.0 sync · Pydantic v2 · psycopg 3 |
| **DB** | Neon PostgreSQL (managed, ap-southeast-1) |
| **LLM** | **Gemini 2.5 Flash** (default) · Anthropic Claude · Stub (자동 fallback) |
| **VIN** | NHTSA vPIC API (무료, 인증 불필요) |
| **PDF** | Jinja2 + Playwright (headless Chromium) |
| **OFAC** | sdn.xml (28MB, 18,947 entries) — in-memory + rapidfuzz fuzzy match |
| **Frontend** | React 19 · Vite 6 · TypeScript strict · TanStack Query v5 · Tailwind 3.4 |
| **Routing** | React Router v7 |

---

## 빠른 시작

### 1. 사전 준비
- Python 3.11+ / Node 18+
- Gemini API 키 ([Google AI Studio](https://aistudio.google.com/app/apikey) 무료)
- Neon Postgres 또는 로컬 PostgreSQL

### 2. Backend
```bash
cd backend
python -m venv venv
.\venv\Scripts\activate   # Windows
pip install -e .
cp .env.example .env
# .env 편집: GEMINI_API_KEY, DATABASE_URL

# 마이그레이션 + 시드
alembic upgrade head
python -m scripts.seed_demo_data --fresh

# 서버 시작
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend
```bash
cd frontend
npm install
npm run dev  # http://localhost:5173
```

### 4. Playwright (PDF 생성용, 1회)
```bash
python -m playwright install chromium
```

---

## 시연 가이드

→ **[docs/DEMO_GUIDE.md](docs/DEMO_GUIDE.md)** — 5분 시연 step-by-step 스크립트

## 발표 자료

| 문서 | 용도 |
|------|------|
| [docs/EXECUTIVE_SUMMARY.md](docs/EXECUTIVE_SUMMARY.md) | 1-page 요약 (멘토/심사위원용) |
| [docs/DEMO_GUIDE.md](docs/DEMO_GUIDE.md) | 5분 라이브 시연 스크립트 |
| [docs/PHASE_2_ROADMAP.md](docs/PHASE_2_ROADMAP.md) | 미구현 항목 + 우선순위 (멘토 Q&A 대비) |
| [docs/validation/findings.md](docs/validation/findings.md) | 21 라운드 검증 70+ findings |
| [docs/validation/data_audit.md](docs/validation/data_audit.md) | 데이터 정합성 종합 audit |

## 1차 자료 (사전 조사)

| 파일 | 내용 |
|------|------|
| [docs/used_car_export_research_v2.md](docs/used_car_export_research_v2.md) | 시장 리서치 정식판 (690줄) |
| [docs/used_car_export_top20_countries.md](docs/used_car_export_top20_countries.md) | 28국 매트릭스 (언어/PSI/영사관/사전등록) |
| [docs/competitor_analysis_and_features.md](docs/competitor_analysis_and_features.md) | 경쟁사 분석 + MVP 10개 + 로드맵 |
| [docs/userflow_and_erd.md](docs/userflow_and_erd.md) | User flow + ERD + 페르소나 (912줄) |

---

## 📞 컨택

- **산학 파트너**: ㈜하이쓰리디 이정욱 대표
- **개발**: 조우진 (한양대 ERICA 수리데이터사이언스)

---

## License & 보안

- `.env`, `backend/data/ofac/sdn.xml` 은 `.gitignore` 처리
- OFAC SDN List 는 [Treasury 공개 데이터](https://www.treasury.gov/ofac/downloads/sdn.xml) 사용
- LLM 메일 본문은 사용자가 발송 전 검토·편집 가능 (한국어 검증 패널 권장)
- Mock SMTP — 실제 발송은 Phase 2 (aiosmtplib + Mailgun/SendGrid)
