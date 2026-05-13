# Phase 2 Roadmap — 멘토 Q&A 대비

> 발표 시 "이건 왜 안 했어요?" "다음 단계는?" 질문 대비 미구현 항목 정리.

---

## 우선순위 1 (Production 배포 전 필수)

### 1.1 인증 / Multi-tenant
- **현재**: PoC 단일 사용자 (`get_current_user_id()` → fixed UUID)
- **Phase 2**:
  - JWT 발급/갱신 (`/api/auth/login`, `/api/auth/refresh`)
  - `get_current_user_id()` 시그니처 그대로 두고 **내부만 교체** (#063 audit)
  - Multi-tenant 데이터 격리 — 이미 모든 endpoint user_id 필터 100% 적용됨 (검증 완료)
- **공수**: 약 2일 (FastAPI-users 또는 fastapi-jwt-auth 도입)

### 1.2 실제 SMTP 발송
- **현재**: Mock SMTP — 콘솔 로그 + `sent_at` DB 마킹
- **Phase 2**:
  - `aiosmtplib` + Mailgun 또는 SendGrid 통합
  - `listings.py:797-840` 의 `logger.info(...)` 부분을 SMTP client 호출로 교체 (1줄)
  - 발송 실패 시 Message.sent_at 롤백 + 에러 표시
- **공수**: 약 4시간

### 1.3 OFAC SDN 자동 갱신
- **현재**: `backend/data/ofac/sdn.xml` 수동 다운로드 (스크립트 `fetch_ofac_sdn.py` 존재)
- **Phase 2**:
  - GitHub Actions cron (매주 월요일) 또는 backend startup background task
  - 갱신 후 in-memory loader 자동 reload
- **공수**: 약 2시간

### 1.4 Security 헤더 + HSTS
- **현재**: CORS dev/prod allowlist OK, 다른 헤더 없음 (#066)
- **Phase 2**:
  - `secure` 라이브러리 미들웨어 또는 nginx 단
  - X-Frame-Options DENY, X-Content-Type-Options nosniff, Referrer-Policy strict-origin
  - production HTTPS 시 HSTS max-age=31536000
- **공수**: 약 1시간

---

## 우선순위 2 (사용자 경험 보강)

### 2.1 WhatsApp Business API
- **현재**: 메일만 지원 (Message.channel='email')
- **Phase 2**:
  - Message.channel='whatsapp' 활용
  - WhatsApp Cloud API (Meta) 통합
  - mail-draft 결과를 WhatsApp 포맷 (160자 chunking + 미디어 첨부)
- **공수**: 약 1주 (Business 계정 인증 포함)

### 2.2 실시간 shipment tracking
- **현재**: Shipment 모델 존재 (vessel/voyage TBA placeholder)
- **Phase 2**:
  - MarineTraffic API 또는 Maersk API 통합
  - 매일 cron 으로 shipment.estimated_arrival 자동 갱신
  - 도착 24시간 전 buyer/seller 양쪽에 알림 (메일 + WhatsApp)
- **공수**: 약 3일 (API 키 신청 + 통합)

### 2.3 Yestrade 정식 API
- **현재**: 2개 demo tax_id stub (`_YESTRADE_DEMO_TAX_IDS`)
- **Phase 2**:
  - 사업자 인증서 + Yestrade (산자부 무역안보관리원) 가입
  - 회사명·tax_id 검색 API 통합
  - 우려거래자 자동 차단 + UI 경고
- **공수**: 약 2주 (가입 절차 포함)

### 2.4 LLM provider 선택 UI
- **현재**: `.env` 의 `LLM_PROVIDER` 환경변수 (gemini/anthropic/stub)
- **Phase 2**:
  - Settings 페이지 dropdown
  - 사용자별 API 키 입력 (안전한 저장)
  - 모델별 비용 표시 (Gemini ~$0.001/req, Claude ~$0.005/req)
- **공수**: 약 1일

### 2.5 회사 로고 + 명함 정보 → PDF 헤더
- **현재**: PDF 헤더에 동강그린모터스 (Demo) 텍스트만
- **Phase 2**:
  - Settings 에 로고 업로드 (S3/Cloudflare R2)
  - PDF 템플릿 (Jinja2) 에 logo 이미지 inject
- **공수**: 약 4시간

---

## 우선순위 3 (Production 운영 보강)

### 3.1 SSE streaming mail-draft
- **현재**: 동기 ~15초 대기 (axios timeout 120s)
- **Phase 2**:
  - FastAPI StreamingResponse + Gemini stream API
  - Frontend EventSource 로 token 단위 실시간 표시
  - 첫 token 1-2초 → 인지 latency 대폭 단축
- **공수**: 약 2일

### 3.2 Frontend bundle code-split
- **현재**: single chunk 569.84 KB raw / 171.12 KB gzip (#076 실측 2026-05-12)
- **Phase 2**:
  - `vite.config.ts` 의 `manualChunks`: vendor / query / ui 분리
  - 페이지 단위 `React.lazy()` (Settings, Mail, Documents 등)
  - 첫 화면 로드 ~500ms 단축 예상
- **공수**: 약 4시간

### 3.3 VIN ISO 3779 강제
- **현재**: `max_length=17` 만, min 없음 + I/O/Q 허용 (#061)
- **Phase 2**:
  - `pattern=r"^[A-HJ-NPR-Z0-9]{17}$"` (ISO 3779)
  - 클라이언트 + 서버 양쪽 검증
- **공수**: 약 30분

### 3.4 Documents 복합 인덱스
- **현재**: `documents.listing_id` 단일 인덱스 (#059)
- **Phase 2**:
  - `CREATE INDEX idx_docs_listing_type_version ON documents (listing_id, doc_type, version)`
  - MAX(version)+1 쿼리 최적화 (100건 미만이면 OK, 1k+ 부터 효과)
- **공수**: alembic migration ~30분

### 3.5 pip-audit / Dependabot
- **현재**: 12개 deps 수동 확인 latest (#068)
- **Phase 2**:
  - GitHub Dependabot 활성화
  - 주간 pip-audit cron + safety 통합
- **공수**: 약 30분 (GitHub UI)

---

## 우선순위 4 (검증/문서 보강)

### 4.1 E2E 테스트 자동화
- **현재**: 라이브 curl 검증 (`docs/validation/findings.md` 21 라운드)
- **Phase 2**:
  - pytest + httpx async client
  - Playwright frontend E2E (시연 시나리오 5건 자동화)
- **공수**: 약 1주

### 4.2 i18n admin UI
- **현재**: 한국어 only
- **Phase 2**:
  - react-i18next 도입
  - 영어/일본어 번역 (시장 확장 시)
- **공수**: 약 3일

### 4.3 모바일 반응형 보강
- **현재**: 데스크탑 위주 (Tailwind sm/md breakpoint)
- **Phase 2**:
  - 모바일 햄버거 메뉴 (현재 disabled)
  - PDF preview 모바일 fit-to-width
- **공수**: 약 2일

---

## 코드 리뷰에서 발견된 minor (데모 후)

| # | 발견 | 공수 |
|---|------|------|
| #6 | `translation_ko` null 시 toast 안내 | 30분 |
| #7 | `\r\n` 처리 (`content_text.split` 안전화) | 15분 |
| #8 | Settings empty string → null PATCH 변환 | 30분 |
| - | Strict mode temperature 0.2 → 0.1 (더 결정론적) | 5분 |

---

## 멘토 예상 질문 + 답변

### Q1. "실제 SMTP 발송 어떻게 보내요?"
**A**: 현재 Mock SMTP — `listings.py:797-840` 의 `logger.info(...)` 부분을 `aiosmtplib.send()` 호출로 교체. 1줄. Phase 2 Mailgun/SendGrid 통합 ~4시간.

### Q2. "다중 사용자 운영은?"
**A**: 모든 endpoint `user_id` 필터 100% 적용 검증 완료 (#063). `get_current_user_id()` 시그니처 그대로, 내부만 JWT 검증으로 교체. 데이터 격리는 이미 보장.

### Q3. "OFAC SDN List 매주 갱신 어떻게?"
**A**: `scripts/fetch_ofac_sdn.py` 존재. Phase 2 GitHub Actions cron 또는 backend startup background task. 갱신 후 in-memory loader 자동 reload.

### Q4. "왜 Gemini? Claude/GPT 비교는?"
**A**: LLM provider 추상화. `.env` 의 `LLM_PROVIDER=gemini|anthropic|stub` 1줄 스위치. Gemini 무료 + 한국어/Arabic 격식 품질 검증 (Round 21 다국어 sample). Anthropic 도 동일 시그니처로 통합 완료.

### Q5. "법적 책임 (오번역 등)?"
**A**: 3-tier 방어:
1. **Strict literal 모드** — 한국어 톤·오타 그대로 번역 (계약 워딩 통제)
2. **한국어 검증 패널** — 외국어 모르는 사장님 사전 검토
3. **사용자 발송 컨펌** — 자동 발송 아님, "보내기" 버튼 명시적

### Q6. "비용은?"
**A**: Gemini 2.5 Flash 무료 (60 req/min). 메일 1건 ≈ 2,000 tokens output × 2 (검증 옵션) = 4,000 tokens. 월 1만 건 가정 시 약 $50.

### Q7. "확장성 (scale)?"
**A**:
- 5x mail 동시 생성 15초 검증 (async I/O, single worker)
- PDF 다른 listings 병렬 / 같은 listing lock 정합성
- DB 12개 핵심 컬럼 100% indexed
- Phase 2 worker pool + Redis cache + nginx LB

### Q8. "사고이력/명의이전 같은 차량 정보는?"
**A**: VehicleHistoryRecord 모델 + 카히스토리/Car365 stub 존재. Phase 2 정식 API 통합 (사업자 인증서 필요).

---

## 우선순위 매트릭스

| 항목 | 공수 | 비즈니스 가치 |
|------|------|--------------|
| 1.2 SMTP | 4h | ⭐⭐⭐⭐⭐ |
| 1.1 JWT | 2일 | ⭐⭐⭐⭐⭐ |
| 1.3 OFAC cron | 2h | ⭐⭐⭐⭐ |
| 2.1 WhatsApp | 1주 | ⭐⭐⭐⭐ |
| 2.5 회사 로고 | 4h | ⭐⭐⭐ |
| 3.1 SSE | 2일 | ⭐⭐⭐ |
| 3.2 Bundle split | 4h | ⭐⭐ |

**총 Phase 2 MVP**: SMTP + JWT + OFAC cron = 약 3일 → 실제 서비스 가능 수준
