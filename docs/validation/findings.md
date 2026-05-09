# 검증 발견 사항 (Validation Findings)

> 우리 시스템(룰엔진·서식·컴플라이언스)을 1차 자료와 비교해서 발견한 차이점·오류·미확인 항목을 모은 곳.
> 모든 항목은 **출처 URL + 검증일 + 영향받는 파일** 을 함께 적는다.
> 새 발견은 위에 추가 (역시간 순).

---

## 🔴 #001 — 도미니카공화국 연식 룰 불일치

**발견일:** 2026-05-09
**심각도:** HIGH (잘못된 룰로 차 보내면 통관 거부)
**영향 파일:**
- `configs/rules/dominican_republic.yaml`
- `docs/used_car_export_research_v2.md` §5.4
- `docs/used_car_export_top20_countries.md` §8

### 우리가 적어둔 룰

```yaml
rules:
  - body_type_filter: passenger
    age_limit_years: 10           # ← 의심
  - body_type_filter: bus
    age_limit_years: 7            # ← 의심
  - body_type_filter: truck
    age_limit_years: 10           # ← 의심
```

### 1차/2차 자료가 말하는 룰

| 출처 | 승용 | 트럭 | 엔진 |
|------|------|------|------|
| **U.S. Department of Commerce (trade.gov)** | 5년 | 15년 | (미명시) |
| **Contadores Dominicanos (현지 회계법인)** | 5년 | 15년 | 200,000cc |
| 인용된 도미니카 법령 | **Law 04-07 (2007.01.05)** + Decree 671 (2002.08.27) | | |

### 가능한 시나리오

1. **우리 룰이 틀림** — 원본 리포트가 잘못된 출처를 인용했을 가능성. 이 경우 `dominican_republic.yaml` 수정 필요.
2. **법이 개정됐고 둘 다 부분적으로 맞음** — 2007년 이후 개정 가능성. 추가 확인 필요.
3. **차종 분류 차이** — "승용차" 범주 안에 SUV·승합 포함 여부 등 정의 차이.

### 다음 액션

- [ ] 멘토 (이정touched 대표) 한테 도미니카 거래 경험 있는지 + 실제 적용 룰 문의
- [ ] DGA (Dirección General de Aduanas) 공식 사이트에서 1차 자료 (Law 04-07 원문) 직접 확인
- [ ] 위 3개 가능 시나리오 중 어느 것인지 확정 후 YAML 수정
- [ ] 수정 후 commit 메시지에 본 findings 번호 (#001) 인용

### 참고 링크

- https://www.trade.gov/country-commercial-guides/dominican-republic-prohibited-restricted-imports
- https://contadoresdominicanos.com/en/post/customs/requirements-for-importing-vehicles-to-the-dominican-republic/
- DGA 본부: Avenida Abraham Lincoln No. 1101, Santo Domingo / +1 809 547 7070 / info@dga.gov.do

---

## 🟢 #005 — PDF 4종 필드 커버리지 검증 통과 (자동화)

**발견일:** 2026-05-09
**상태:** ✅ resolved (1차 자료 대비 0 gap)
**도구:** `scripts/validate_document_fields.py`
**리포트:** `docs/validation/document_field_matrix.md`

### 1차 결과 (gap 9개 발견)

| Doc Type | 우리 커버리지 | gaps |
|---|---|---|
| invoice | 21/22 | Invoice Date 라벨 누락 |
| packing_list | 10/16 | Marks & Numbers · Net Weight · Gross Weight 라벨 |
| shipping_instruction | 11/18 | B/L No. · Marks & Numbers |
| co_application | 13/17 | Producer · Marks & Numbers · Origin Criterion |

### 적용한 수정

1. 검증기: `&amp;` → `&` HTML entity 디코딩 (false positive 제거)
2. `invoice.html`: "Date:" → "Invoice Date:"
3. `packing_list.html`: "Net Wt" → "Net Weight" / "Gross Wt" → "Gross Weight" / Marks & Numbers 섹션 추가
4. `co_application.html`: Producer 행 + Origin Criterion 컬럼 추가
5. `shipping_instruction.html`: B/L No. (carrier 발급 예정) + Marks & Numbers 섹션 추가
6. `DocumentInput`: `producer`, `origin_criterion` 필드 추가

### 최종 결과 (재실행 후)

| Doc Type | 우리 커버리지 | gaps |
|---|---|---|
| invoice | 22/22 | 0 ✅ |
| packing_list | 13/16 | 0 ✅ |
| shipping_instruction | 13/18 | 0 ✅ |
| co_application | 16/17 | 0 ✅ |

남은 ❌ 칸은 우리 문서엔 있는데 reference 에는 없는 항목 (예: 우리 invoice 의 Bank Info ↔ KCS UNI-PASS FAQ). 즉 우리가 더 풍부함, gap 아님.

### 의미

발표 시 평가위원 질문 *"이게 표준 양식 맞아?"* 에 대한 답:
> **"네, 1차 자료 6건과 자동 비교한 매트릭스가 있습니다. 처음 9개 gap 발견했고 전부 수정해서 현재 0 gap입니다."**

---

## 🟡 #002 — PDF 4종 양식 (Invoice / PL / SI / C/O) 검증 미완료

**발견일:** 2026-05-09
**심각도:** MEDIUM (실제 통관에서 거부될 위험, 단 시연 자체는 가능)
**영향 파일:**
- `backend/app/services/document_writer.py`
- `backend/app/services/document_templates/*.html`

### 상황

현재 4종 PDF 템플릿은 web research + 통상 관행 추정으로 만든 것. **단 한 번도 실제 통관용 양식과 1:1 비교된 적 없음.**

### 비교 대상이 되는 1차 자료 (수집 완료)

`scripts/fetch_public_samples.py` 로 다운받은 것:
- **Korea-ASEAN FTA C/O Form** — `docs/samples/fta_co/AKFTA_certificate_of_origin_form.pdf`
- **Korea FTA Annex 5B C/O Format** — `docs/samples/fta_co/Korea_FTA_Annex5B_CO_format.pdf`
- **UNI-PASS FAQ 2023.11** — `docs/samples/korea_customs/UNIPASS_FAQ_2023-11-17.pdf`

### 비교 대상이 되는 1차 자료 (아직 미수집)

- 실제 거래에서 발급된 Commercial Invoice (멘토 요청 필요)
- 실제 Packing List (동상)
- 실제 B/L (선사 발급, 한 번 받아봐야 함)
- 수출신고필증 견본 (관세사 또는 멘토)

### 다음 액션

- [ ] 위 4종 1차 자료의 필수 필드 vs 우리 템플릿 필드 매트릭스 작성 → `docs/validation/document_field_matrix.md`
- [ ] 시각 비교용 사이드바이사이드: `docs/validation/comparison/<doc_type>/{ours,reference}.pdf`
- [ ] 멘토 검수 1차 라운드 (요청 메일 draft 준비 필요)

---

## 🟡 #003 — 룰엔진 5개국 1차 출처 미확인

**발견일:** 2026-05-09
**심각도:** MEDIUM (도미니카 외 4개국)
**영향 파일:** `configs/rules/{kenya,libya,kyrgyzstan,syria}.yaml`

### 상황

도미니카(#001)에서 기존 리포트의 신뢰도가 떨어짐을 확인. 나머지 4개국 룰도 1차 자료로 재검증 필요.

### 진행 상황

| 국가 | 1차 자료 | 비고 |
|------|---------|------|
| 케냐 | ✅ KEBS PUBLIC NOTICE 2025-07 + 2023-12 | 8년 룰 + 2019.1.1 cutoff 확정 |
| 리비아 | ✅ Libya Customs ACI 매뉴얼 3종 | ACI 의무화 2024.11.1 부터 |
| 키르기스스탄 | ❌ 없음 | EAEU 통합 통관 자료 필요 |
| 시리아 | ❌ 없음 | 정세 변동 — 수동 검토 모드라 일단 보류 |

### 다음 액션

- [ ] 키르기스스탄: EAEU Customs Code 찾기
- [ ] 시리아: 일단 수동 검토 모드로 두고 발표 후크로만 사용

---

## 🟢 #004 — 컴플라이언스 모듈 stub 상태 (의도된 것)

**발견일:** 2026-05-09
**심각도:** LOW (PoC 단계 의도)
**영향 파일:** `backend/app/core/compliance.py`

### 상황

`_OFAC_SDN_DEMO_NAMES`·`_YESTRADE_DEMO_TAX_IDS` 가 인메모리 stub. 실제 매칭 로직 없음.

### 발표 시 대응

발표 슬라이드에 "Phase 2 에서 OFAC SDN XML 일일 동기화 + Yestrade API 연동 예정" 명시.
실제 차단 로직 (러시아 우회 등) 은 작동하므로 시연 자체는 OK.

### 다음 액션 (Phase 2)

- [ ] OFAC SDN XML 다운로더 (`https://www.treasury.gov/ofac/downloads/sdn.xml`)
- [ ] Yestrade 우려거래자 조회 자동화 검토 (가능 여부 확인 필요)
