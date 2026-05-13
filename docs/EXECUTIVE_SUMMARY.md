# Executive Summary — 중고차 수출 AI 에이전트

> 한양대 ERICA × ㈜하이쓰리디 산학 캡스톤 PoC · 2026.05.12

---

## 한 줄

**한국 영세 중고차 수출업체의 다국어 메일 작성 + 28국 통관 룰 + 컴플라이언스 차단을 LLM 으로 자동화하는 SaaS PoC.**

---

## 시장

| 지표 | 수치 | 출처 |
|------|------|------|
| 한국 중고차 수출 글로벌 점유율 | **4위 (약 10.5%)** — 일본 > EU > 미국 > 한국 | KITA·산업연구원 2024 |
| 인천 송도 영세 수출업체 수 | 약 **1,000곳** (대부분 1~2인) | 이데일리 송도 르포 |
| 2025.10 부산경찰청 적발 | 키르기스스탄 우회수출 **40여 대**, **대외무역법 위반** (전략물자 무허가 수출), 키르기스스탄인 2명 구속 | 서울신문/뉴시스 2025.10.23 |
| 2024.2.24 산자부 전략물자 확대 | 798 → **1,159개 품목** (2,000cc+ 내연 + 모든 EV/하이브리드 對러·벨라루스 상황허가) | KCTDI 무역개발원·KITA |
| 2024.6.24 EU 14차 제재 | 1,900cc+ 신차·중고차 + 모든 EV/하이브리드 對러 수출 금지 | EU Commission |

영세업체는 영어·아랍어·러시아어 응대 + 28국 규제 추적 + OFAC/Yestrade 검증을 사람이 다 처리하기 사실상 불가능.

---

## 차별화 5종

| # | 기능 | 시연 시간 |
|---|------|----------|
| 1 | **28국 통관 사전 검증** (관세·VAT·연식·핸들·언어 매트릭스) | 즉시 (룰엔진, 700ms) |
| 2 | **다국어 격식 메일 자동 작성** + 한국어 검증 패널 | 15초 / 30초 (검증 포함) |
| 3 | **수출 서류 4종 PDF 자동 생성** (Invoice/PL/SI/CO) | 7초 (5건 동시 8초) |
| 4 | **컴플라이언스 multi-finding 자동 차단** (OFAC SDN 18k + fuzzy + Russia-proxy + Yestrade) | 즉시 |
| 5 | **거래 상태 머신** 12 단계 + audit trail (Document.version) | <100ms |

---

## 핵심 지표

| 영역 | 결과 |
|------|------|
| **검증** | 21 라운드 · 70+ findings · 28국 1차 자료 cross-validate |
| **성능** | 5x mail 동시 생성 wall **15초** (5x speedup) · 다른 listings 4-PDF 병렬 **7.5초** |
| **다국어 품질** | AR/ES/RU/EN 격식 표현 native · 평균 2,006 chars · markdown post-process 3-tier 방어 |
| **컴플라이언스** | KG + Genesis G80 → 3-layer (russia_proxy_strategic blocked + 7 docs) 라이브 검증 |
| **보안** | 권한 격리 100% · stack trace 노출 0건 · deps 12개 latest stable · CORS dev/prod allowlist |

---

## 데모 시연 narrative (5분)

1. **마켓플레이스** (Autobell-style) → 차량 카드 → "Request Quote" 클릭
2. → admin 시스템 **자동 inquiry 거래 생성**
3. AI 메일 작성 (Arabic, 한국어 검증 패널 옵션 ON) → 30초 후 좌(Arabic)+우(한국어 검증) 표시
4. 한국어 패널에서 가격 수정 → **"한국어로 외국어 재생성"** 클릭 → 30초 후 새 Arabic + 새 한국어
5. **"보내기"** 클릭 → Mock SMTP + SENT 배지
6. **"4종 PDF 생성"** 클릭 → 7초 후 Invoice/PL/SI/CO 다운로드 가능
7. **컴플라이언스**: KG buyer + Genesis G80 입력 시 즉시 3-layer blocked + 7 docs 추천

---

## 기술적 강점 (멘토 어필 포인트)

- ✅ **LLM provider 추상화** — `.env` 1줄 스위치 (Gemini ↔ Claude ↔ Stub)
- ✅ **3-tier markdown 방어** — Prompt + Post-process + Placeholder fallback (Gemini 30% 룰 위반 대응)
- ✅ **Async I/O 5x speedup** — single-worker uvicorn 도 5건 동시 메일 15초
- ✅ **with_for_update lock** — 같은 listing 동시 PDF 생성 → 정합성 보장 (Document.version)
- ✅ **OFAC SDN 28MB XML in-memory** — exact + fuzzy (rapidfuzz) 라이브 검색
- ✅ **Document FSM 12 상태** + transition validation (잘못된 전환 100% 차단)
- ✅ **Mock SMTP graceful** — Phase 2 aiosmtplib 한 줄 교체로 실제 발송 가능

---

## Phase 1 ✅ 완료 (현재 PoC)

- 28국 룰 엔진 + 1차 자료 검증
- 5국 데모 시드 (DO/KE/LY/KG/SY) + 23 평가가능국 RANDOM_POOL
- 다국어 메일 (en/es/ar/ru) + 한국어 검증 패널 (Level 1 + 2)
- 수출 서류 4종 PDF 자동 생성
- OFAC SDN + Yestrade demo stub
- Mock SMTP send + sent_at audit trail
- Settings + Vehicle CRUD + Buyer CRUD + Listing FSM + Dashboard
- 마켓플레이스 (Autobell-style) + Admin SaaS 2-shell architecture

## Phase 2 (Roadmap → [PHASE_2_ROADMAP.md](PHASE_2_ROADMAP.md))

- JWT 인증 + multi-tenant
- 실제 SMTP 발송 (aiosmtplib + Mailgun/SendGrid)
- OFAC SDN 자동 cron 갱신 (매주)
- Yestrade 공식 API 통합 (사업자 인증서)
- WhatsApp Business API + 실시간 shipment tracking
- Frontend code-split + Security 헤더

---

## 한 장 결론

**"21 라운드 70 findings 검증된 PoC + 다국어 검증 패널 (Korean ↔ Foreign 양방향) 차별화 = 영세업체가 사용 가능한 수준의 LLM 자동화."**

발표 시 강조 포인트:
1. "단순 번역기가 아니라 **컴플라이언스 + 통관 + 비즈니스 격식** 모두 자동화"
2. "**한국어 검증 패널** — 외국어 모르는 사장님도 안심 발송"
3. "**Mock SMTP → 실제 발송** Phase 2 마이그레이션 = 1줄 교체"
