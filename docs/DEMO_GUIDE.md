# 시연 가이드 — 5분 라이브 데모 스크립트

> 멘토/심사위원 앞에서 발표할 5분 시나리오. 클릭 순서·화면 전환·narrative 멘트.

---

## 시연 직전 5분 체크리스트

```bash
# 1. Backend 헬스
curl http://localhost:8000/health  # 200 OK 확인

# 2. .env 의 GEMINI_API_KEY 유효한지
# (factory.py 가 fallback 하지만 실제 메일 생성에 필요)

# 3. Fresh seed
cd backend
python -m scripts.seed_demo_data --fresh

# 4. Playwright 워밍업 (cold start 4s 회피)
LID=$(curl -s http://localhost:8000/api/listings | head -1 | grep -oE '"[a-f0-9-]{36}"' | head -1)
# 시연 listings 중 하나 PDF 미리 1회 생성
curl -X POST http://localhost:8000/api/listings/$LID/documents

# 5. Frontend dev 서버
cd frontend
npm run dev  # http://localhost:5173

# 6. 브라우저 캐시 클리어 (Ctrl+Shift+R)
```

---

## 시나리오 5분 (시연 순서 고정)

### 🎬 STEP 1 — 마켓플레이스 (30초)
**URL**: `http://localhost:5173/marketplace`

**클릭**: 차량 카드 1개 (예: Hyundai Sonata 2018)

**보여줄 것**:
- Autobell-style 마켓플레이스 (시드 10대 차량 카드)
- 차량 상세 화면 — Spec, 이미지, 28국 통관 매트릭스 우측

**Narrative**:
> "Autobell, BeForward 같은 외부 마켓플레이스 위에서 동작하는 SaaS. 일반 buyer 가 차량 보고 견적 요청 클릭."

---

### 🎬 STEP 2 — Quote Request → Admin 자동 생성 (45초)
**클릭**: "Request Quote" 버튼

**모달 입력**:
- 바이어: `Sahara Auto Trading (LY)` 선택 (드롭다운에서)
- 도착국: **자동 입력** (LY) — 28국 드롭다운에서 변경 가능
- 메모: "급한 견적, CIF Misrata"
- "견적 요청 보내기" 클릭

**보여줄 것**:
- ✅ **자동 도착국 inject** + 28국 드롭다운
- ✅ Sanctioned/blocked 국가 자동 비활성 표시
- 성공 모달: "admin SaaS 에 inquiry 거래로 자동 등록됐습니다"

**Narrative**:
> "외부 마켓플레이스의 견적 요청이 admin 시스템에 inquiry 상태 거래로 자동 등록. 한 화면에서 메일·서류 작성."

---

### 🎬 STEP 3 — AI 메일 작성 + 한국어 검증 (75초)
**클릭**: "Admin UI 에서 보기" → ListingDetail

**입력**:
- 시나리오: **견적 발송**
- 언어: **العربية (ar)**
- ☑ **"한국어 번역도 함께 표시 (검증용)"** 체크
- "AI로 메일 생성하기 (한국어 검증 포함)" 클릭

**대기**: ~30초 (LLM 외국어 생성 + 한국어 번역)

**보여줄 것**:
- 좌(📤 AR, 발송용 RTL) ↔ 우(🇰🇷 KO, 검증용)
- **격식 표현**: `السيد المحترم،\nتحية طيبة وبعد،`
- 라벨-값 가격표: `FOB 인천 ......... 미화 10,500달러`
- 자동 inject: 회사명 "동강그린모터스 (Demo)", VIN, 차종

**Narrative**:
> "Arabic 메일이 잘 작성됐는지 모를 사장님 위해 한국어 옆에 띄움. Markdown/표/오타 자동 클린, 회사명 자동 inject."

---

### 🎬 STEP 4 — Level 2 한국어 수정 → 외국어 재생성 (60초)
**한국어 패널에서 수정**:
> "FOB **9,800달러로 700달러 할인**, 보험 무료 제공"

**보여줄 것**:
- KO 패널 dirty 표시 (노란색 배지 "● 수정됨")
- 재생성 박스 "한국어로 외국어 재생성" 버튼 활성

**☐ Strict literal 모드** 옵션 설명:
- off (default): 비즈니스 격식체 자동 polish (영세업체 친화)
- on: 한국어 톤·오타·구두점 그대로 (계약 워딩 통제 시)

**클릭**: "한국어로 외국어 재생성" → 대기 ~30초

**결과**:
- 새 Arabic: `9,800 دولار أمريكي`, `700 دولار تخفيض`, `تأمين بحري مجاناً`
- 새 Korean 재번역: "9,800달러", "700달러 할인", "해상 보험 무료"

**Narrative**:
> "외국어 모르는 사장님이 한국어로 의도 입력 → AI 가 외국어 다시 작성 → 한국어로 다시 검토. **양방향 검증 cycle**."

---

### 🎬 STEP 5 — Mock SMTP Send + 서류 4종 PDF (45초)
**스크롤 → "메일 history" 섹션**:
- draft 2건, sent 0건 (Level 1 + Level 2 draft 2개)
- 최신 draft 의 **"보내기"** 클릭

**결과**:
- Mock SMTP — 즉시 SENT 배지 (콘솔에 로그)
- "메일 history": draft 1 · sent 1 변경

**스크롤 → "수출 서류 4종 자동 생성"**:
- "4종 PDF 생성하기" 클릭 → ~7초

**결과**:
- ✅ Invoice / Packing List / Shipping Instruction / C/O Application
- Document.version: v1 → v2 (재생성 시 audit trail)

**Narrative**:
> "AI 메일 → 발송 1초. PDF 4종 → 7초. 동일 거래 동시 호출은 lock 으로 직렬화 (정합성 보장), 다른 거래는 병렬 (5건 동시 8초)."

---

### 🎬 STEP 6 — 컴플라이언스 자동 차단 (45초)
**Vehicles 탭 → 새 차량 등록** 또는 **기존 Genesis G80 선택**

**버튼**: "이 매물로 거래 만들기"
**모달**: bayer `ABC Auto LLC (KG)` 선택

**결과 (CountryMatrix + import-check)**:
- ❌ **차단**: `russia_proxy_strategic` (engine >2000cc + price >$50,000)
- ⚠ 경고: `russia_proxy_country` + `new_buyer_high_value`
- 📄 **7개 서류 자동 추천**: end_user_certificate, situational_license, translation_ru 등

**Narrative**:
> "키르기스스탄 + 고가 차량 = **2025.10 부산경찰청 적발 패턴**. AI 가 multi-finding stacking + 7 서류 자동 안내. 영세업체가 모르고 위반하는 사고 방지."

---

## 마무리 멘트 (15초)

> "21 라운드 70 findings 검증 PoC. **한국어 검증 패널** 차별화 + Phase 2 SMTP 발송 1줄 교체. 영세업체가 실제 사용 가능한 수준."

---

## 백업 시나리오 (사고 발생 시)

| 사고 | 대응 |
|------|------|
| **Gemini API down** | factory.py 가 stub 자동 fallback. UI 에 `[STUB MODE] ...` 표시 — "이게 LLM provider 추상화 입니다" 솔직히 narrative 전환 |
| **Neon Postgres 끊김** | 로컬 SQLite 백업 시드: `DATABASE_URL=sqlite:///./local.db` 로 재시작 |
| **PDF 생성 실패** | Playwright cold start 우려 — 시연 직전 워밍업 PDF 1건 미리 만들어둠 |
| **인터넷 끊김** | 모든 API 외부 의존: Gemini (LLM) / NHTSA (VIN) / Neon (DB). 인터넷 필수 — 시연 PC 에서 모바일 핫스팟 백업 |
| **시연 PC 환경 누락** | 사전 fresh OS 에서 `git clone` → README 빠른 시작 6단계로 동작 확인 |

---

## 멘토 Q&A 준비 → [PHASE_2_ROADMAP.md](PHASE_2_ROADMAP.md)
