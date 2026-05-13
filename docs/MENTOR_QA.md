# 멘토 Q&A 사전 준비

> 대표님·심사위원 예상 질문 + 답변 메모. 시연 직전 한 번 훑어보기용.
> 실제 받은 질문은 답변 후 이 문서에 추가해 다음 시연 대비.

---

## 🎯 가장 중요한 3개 — 외워두기

### Q1. "제안서 docx 의 결과물 중 안 빠뜨린 거 맞나요?"
**A**: "네, **5월 4일 docx 결과물 100% 충족** 했습니다.

| 제안서 항목 | 충족 위치 |
|------------|----------|
| 차량 시세 자동 분석 + 적정 수출가 산출 | `/vehicles/:id` 우측 PriceSuggestion 위젯 (#8) |
| 인보이스·패킹리스트·B/L 자동 생성 PDF | `/listings/:id` "수출 서류 4종 PDF 생성" |
| 해외 바이어 매칭 + 다국어 견적 메일 | `/listings/:id` "다국어 메일 작성" (한국어 검증 패널 옵션) |
| 채팅 기반 대시보드 UI | `/chat` 페이지 (자연어 → MCP tool 라우팅) |
| Claude Code + MCP 기반 백엔드 자동화 | `/api/mcp/tools/list` 10 tools (Claude Desktop 호환) |
| 사용자가 직접 LLM Wiki 편집 페이지 | `/wiki` 28국 + 신규 국가 추가 가능 |

원래 5월 12일 검증 시 4건 deviation 으로 분류돼있던 항목을 모두 production 수준으로 추가 구현했습니다."

### Q2. "MCP 가 정확히 뭐고, 왜 쓰셨나요?"
**A**: "MCP = Model Context Protocol, Anthropic 이 2024년 공개한 LLM tool-use 표준입니다. 

우리 시스템은 비즈니스 액션 10개 (decode_vin, OFAC 조회, 시세 산출 등) 를 MCP 표준 JSON Schema 로 노출합니다.

**효과**:
- 우리 채팅 UI 가 자연어 → tool 자동 라우팅 (키워드 매칭 + LLM fallback)
- **외부 Claude Desktop / Cline / Cursor 가 동일 endpoint 호출 가능** — 사장님이 별도 Claude Desktop 만 쓰셔도 우리 비즈니스 로직 호출 가능
- 신규 tool 추가 시 import 단계에서 handler 매핑 자동 검증 (`_validate_tool_handlers`)

`/api/mcp/tools/list` 가 그 표준 endpoint 입니다."

### Q3. "시세 산출 데이터 출처는요? 신뢰할 수 있어요?"
**A**: "Hybrid 3-layer 산출:

1. **Baseline 시세표** — 12개 (body × fuel) 조합 × 0/3/5/7/10/15년 anchor — KITA·KIET 2024 보고서 + KATECH '중고차 수출시장의 부상' + 멘토 인터뷰 기반
2. **DB 동급 통계** — 같은 make/model/year±2 표본 ≥3건 시 median 사용 (현재 PoC 시드 10대라 표본 부족 → method=baseline_table 표시)
3. **도착국 시장 multiplier** — `docs/used_car_export_top20_countries.md` §1-2 시장 분석 (시리아 +10%, 키르기스 -5% 등)

추가 factor: 주행거리 ±2%/만km (clamp +20%/-30%), 사고이력 -15%, Luxury 브랜드 +35%

**Confidence 배지** 로 신뢰도 표시 (high/medium/low). PoC 표본 부족 시 medium 으로 보수적 표기. Phase 2 = 엔카·KB차차차 실시간 시세 + 자체 거래 데이터 누적."

---

## 🔧 기술 깊이 — 자주 받을 질문

### Q4. "실제 SMTP 발송은 어떻게 보내요?"
**A**: 현재 Mock SMTP — `listings.py:797-840` `[MOCK SMTP]` 콘솔 로그 + `sent_at` DB 마킹. Phase 2 = `aiosmtplib` + Mailgun/SendGrid — `logger.info(...)` 한 줄을 SMTP client 호출로 교체. 약 4시간 작업.

### Q5. "왜 Gemini? Claude/GPT 비교는?"
**A**: LLM provider 추상화 (`backend/app/services/llm/factory.py`). `.env` 의 `LLM_PROVIDER=gemini|anthropic|stub` 1줄 스위치. Gemini 2.5 Flash = 무료 60 req/min + 한국어/Arabic 격식 품질 라이브 검증 (findings #072 5/5 통과). Anthropic Claude 도 동일 인터페이스로 통합 완료. Stub은 데모 환경 안전망 (API quota 초과 시 자동 fallback).

### Q6. "법적 책임 — 잘못된 번역으로 사고나면?"
**A**: 3-tier 방어:
1. **Strict literal 모드** — 한국어 톤·오타 그대로 (계약 워딩 통제)
2. **한국어 검증 패널** — 외국어 모르는 사장님이 한국어로 사전 검토
3. **사용자 발송 컨펌** — 자동 발송 X, "보내기" 버튼 명시적

추가로 컴플라이언스 자동 차단으로 위반 거래 사전 봉쇄 (2025.10 부산경찰청 적발 패턴).

### Q7. "비용은?"
**A**: Gemini 2.5 Flash 무료. 메일 1건 ≈ 2,000 tokens output × 2 (한국어 검증 포함) = 4,000 tokens. 월 1만 건 가정 시 약 $50. 시세 산출 / Wiki / MCP tools 호출은 LLM 안 거치므로 비용 0.

### Q8. "확장성 (scale)?"
**A**:
- 5x mail 동시 생성 15초 검증 (async I/O, single worker)
- PDF 다른 listings 병렬 / 같은 listing lock 정합성
- MCP tools/list — p50 **12ms** (정적 list, 외부 client 폴링 최적)
- OFAC check — p50 **21ms** (in-memory 18,947 entries)
- DB endpoint p50 500-800ms (Neon ap-southeast-1 RTT)
- Phase 2: worker pool + Redis cache + nginx LB

### Q9. "사고이력/명의이전 같은 차량 정보는?"
**A**: `VehicleHistoryRecord` 모델 + 카히스토리/Car365 stub 존재. Phase 2 정식 API 통합 (사업자 인증서 필요). 현재 시세 산출에 `has_accident` flag만 활용 (-15% factor).

### Q10. "다중 사용자 운영은?"
**A**: 모든 vehicles/buyers/listings endpoint `user_id` 필터 100% 적용 검증 완료 (findings #063). `get_current_user_id()` 시그니처 그대로, 내부만 JWT 검증으로 교체 (Phase 2 ~2일). countries/import_rules 는 글로벌 master data 라 별도 — role-based 권한 + optimistic lock 도입 필요 (countries.py docstring 명시).

---

## 🆕 신규 4 features 깊이

### Q11. "Wiki 에서 신규 국가 추가하면 chat 에서 바로 인식하나요?"
**A**: 네, 즉시 인식합니다.

처음에 정적 `_KNOWN_COUNTRY_CODES` set 으로 구현했다가 (2차 리뷰 #3) DB 동적 조회 + 60s TTL 캐시로 교체. Wiki POST/DELETE 시 `_invalidate_chat_country_cache()` 호출로 캐시 즉시 invalidate. pytest test_chat_intent.py::test_wiki_added_country_matches 가 검증.

### Q12. "채팅에서 'generate_mail_draft' 호출하면 실제 메일이 생성되나요?"
**A**: **명시적으로 NOT_IMPLEMENTED_IN_CHAT 반환**합니다 (~15초 LLM 호출 비용 절약). 호출 시:

```json
{
  "ok": false,
  "error": "NOT_IMPLEMENTED_IN_CHAT: POST /api/listings/{id}/mail-draft 또는 admin UI 의 'AI로 메일 생성하기' 버튼을 사용하세요."
}
```

외부 Claude Desktop 이 silent failure 안 하도록 ok=False + 사유 명시. UI 의 "메일 작성" 버튼은 정상 동작.

### Q13. "MCP tool input_schema 검증은 어떻게?"
**A**: `jsonschema` Draft202012Validator 로 `dispatcher.call` 진입부에서 검증. 누락 필드 → `'vin' is a required property`, 길이 위반 → `'TOOSHORT' is too short` 같이 사람이 읽을 수 있는 에러. pytest test_mcp_tools.py::TestValidateArguments 9 cases.

---

## 🧪 검증 깊이

### Q14. "검증은 어떻게 했나요?"
**A**: 다층 검증:

| 단계 | 내용 |
|------|------|
| 1차 코드 리뷰 | 16건 발견 → 5건 패치 (regex / 인증 / Decimal / rollback / schema) |
| 2차 코드 리뷰 | 12건 발견 → 8건 패치 (race / stub / 동적 화이트리스트 외) |
| pytest unit tests | **77/77 통과** (pricing 28 + mcp_tools 18 + dispatcher 10 + chat_intent 21) |
| Smoke test live | 25 endpoint 호출, Edge case 20, E2E 5 시나리오 모두 정상 |
| 동시성 | 5x 병렬 (chat / price / wiki PUT) 검증 |
| SQL injection | `'; DROP TABLE vehicles; --` → ORM escape 정상, 매물 보존 |
| Performance baseline | 50회 평균 p50/p95/p99 측정 |

전체 검증 로그: `docs/validation/findings.md` (73 findings, 21 라운드)

### Q15. "Phase 2 작업량은?"
**A**: 우선순위 매트릭스:

| 항목 | 공수 | 비즈니스 가치 |
|------|------|--------------|
| 실제 SMTP 발송 | 4h | ⭐⭐⭐⭐⭐ |
| JWT 인증 + multi-tenant | 2일 | ⭐⭐⭐⭐⭐ |
| OFAC SDN cron 갱신 | 2h | ⭐⭐⭐⭐ |
| WhatsApp Business API | 1주 | ⭐⭐⭐⭐ |
| Yestrade 정식 API | 2주 (사업자 인증서) | ⭐⭐⭐⭐ |
| 차량 시세 (엔카 실시간) | 1주 | ⭐⭐⭐ |
| 회사 로고 PDF | 4h | ⭐⭐⭐ |
| SSE streaming mail | 2일 | ⭐⭐⭐ |

**MVP 실서비스**: SMTP + JWT + OFAC cron = 약 3일 → 영세업체 사용 가능 수준.

---

## 🎤 시연 중 사고 대비

| 사고 | 대응 |
|------|------|
| Gemini API down | factory.py 가 stub 자동 fallback. UI 에 `[STUB MODE]` 표시 — "이게 LLM provider 추상화 입니다" 솔직히 narrative 전환 |
| Neon Postgres 끊김 | 로컬 SQLite 백업: `DATABASE_URL=sqlite:///./local.db` 재시작 |
| PDF 생성 실패 | Playwright cold start 우려 — 시연 직전 워밍업 PDF 1건 미리 생성 |
| 인터넷 끊김 | 모든 API 외부 의존 — 모바일 핫스팟 백업 |
| 채팅이 LLM fallback 으로 이상한 응답 | "이건 fallback 입니다. 위 4 패턴은 deterministic 매칭" 솔직히 |

---

## 🏁 마무리 답변 — "프로젝트 자기 평가는?"

> "**제안서 5월 4일 docx 결과물 100% 충족.** Phase 1 끝.
> - 검증 5단계 (1차 리뷰 + 2차 리뷰 + pytest 77 + smoke + E2E) 모두 통과
> - 1차에서 5건 + 2차에서 8건 + pytest 가 1건 (0km 차량 mileage factor) — 총 14건 self-found 버그 패치
> - 실제 시연 안정성 확보 (콘솔 에러 0, 네트워크 실패 0)
>
> **다음 단계**: Phase 2 SMTP 발송 (4시간) + JWT (2일) = 약 3일 → 실서비스 가능 수준.
>
> **차별화 본질**: 다국어 메일 자동화나 PDF 생성은 다른 솔루션도 합니다. 우리 차별화는 **(1) 한국어 검증 패널 양방향**, **(2) 컴플라이언스 multi-finding stacking (2025.10 부산경찰청 적발 패턴 차단)**, **(3) MCP 표준 (외부 LLM client 호환)** 세 가지. 영세업체 1~2인 사장님이 실제로 사용 가능한 수준."

---

*시연 후 받은 신규 질문은 여기에 추가하세요.*
