# 검증 발견 사항 (Validation Findings)

> 우리 시스템(룰엔진·서식·컴플라이언스)을 1차 자료와 비교해서 발견한 차이점·오류·미확인 항목을 모은 곳.
> 모든 항목은 **출처 URL + 검증일 + 영향받는 파일** 을 함께 적는다.
> 새 발견은 위에 추가 (역시간 순).

---

## 🟢 #039 — 28국 항구 물류 매트릭스 신설 (Korea → 도착항 ETA + 운임)

**발견일:** 2026-05-10
**상태:** 🟢 docs added — `docs/validation/shipping_matrix.md`

이전: country YAML 의 `main_ports` 필드만 (항구명 list). ETA / 운임 / 운송
방식 / frequency 없음. 멘토 "면토 며칠 걸려?" "운임 얼마?" 즉답 어려움.

신설 `docs/validation/shipping_matrix.md`:
- **Korea → 28국 주요 항구** ETA + RoRo/Container 운임 추정 매트릭스
- 7 region 분류 (라틴/아프리카/북아프리카/중동/중앙아/동남아/남아)
- Sonata 2020 $14,000 FOB 기준 도착 후 총 비용 (운임 + 보험 + 관세)
  · UAE: ~$16,400 / 3주 (가장 빠름·저렴)
  · MX: ~$19,800 / 3주
  · KH/VN: 2주 (최단 거리)
  · DO/CR/KE/EG: 4-6주
  · KG/KZ: 6-7주 (Trans-Siberian rail)
  · LY: 5-6주 (정세 + 보험료 ↑↑)
- 한국 측 항만 비교 (평택/인천/부산/광양/울산)
- Carrier 공개 schedule URL (EUKOR/Wallenius/NYK)

⚠️ 한계: carrier 들 가격 비공개 → 산업 추정 (±30%). Phase 2 에서 EUKOR API
또는 Freightos 연동 시 정확화.

→ 시연 narrative: "동남아·중동: 2-3주 / 카리브·아프리카: 5-6주 / 중앙아 철도:
   6-7주" 즉답 가능. UAE 재수출 허브 narrative + 한국 1위 LY 정세 risk
   narrative 보강.

---

## 🟢 #038 — 28국 관세 매트릭스 신설 (시연 narrative 강화)

**발견일:** 2026-05-10
**상태:** 🟢 docs added — `docs/validation/tariff_matrix.md`

이전: 각 country YAML 의 `notes:` 필드에 산발적 관세 정보 ("관세 25% +
VAT 16% + 소비세 20%" 같은 한글 narrative). 멘토 "관세 얼마?" 질문 시
정확한 답 어려움.

신설 `docs/validation/tariff_matrix.md`:
- 28국 × HS 8703.23 (가장 흔한 passenger gasoline 1.5-3L) 관세율 표
- 통과 가능국 17국 / 자동 차단 6국 / 진입 어려움 5국 분류
- Sonata 2020 $14,000 FOB 기준 도착 비용 시연 표
  · UAE: ~$15,400 (10% 부담, 가장 저렴)
  · MX: ~$18,000 / DO: $17-25k / KE: ~$22,500
  · EG: ~$25,500 / DZ: ~$26,000+
- 출처 cross-reference (32 PDFs)
- Phase 2 후보 명시 (mail_writer prompt 강화 + FTA 자동 계산 + 환율 변동)

→ 멘토 "DO 보내면 총 비용?" 즉답 가능. "왜 UAE 가 재수출 허브인가?" →
   관세 5%+5% 만으로 narrative 강화.

---

## 🔴 #037 — ICC Incoterms 2020 mirror URL 이 hijack 됨 (FIX 완료)

**발견일:** 2026-05-10
**상태:** 🔴 detected & 🟢 fixed

`docs/samples/incoterms/ICC_Incoterms_2020_full.pdf` 가 PDF 가 아닌 HTML.
첫 줄: `<!DOCTYPE html><html lang="id-ID"...><title>BAHAGIA777: Bocora...`
도박 사이트 내용. URL `iscosafricashipping.org/wp-content/.../ICC-INCOTERMS-2020.pdf`
가 hijack 되어 우리 fetch 시 잘못된 콘텐츠 받음.

이전 round 5 에서 pymupdf 로 "10KB chars / 38p" 결과는 hijack 된 HTML 이
PDF 로 위장한 것 (실제는 영문 텍스트 거의 없음).

**FIX:**
1. `docs/samples/incoterms/ICC_Incoterms_2020_full.pdf` 삭제
2. `samples_registry.yaml` 정정: ICC Switzerland 의 무료 introduction PDF 사용
   (https://www.icc-switzerland.ch/images/723e_inco2020_eng_intro.pdf)
3. ICC 본 paywall 자료 (€45/€69 책자) 는 Phase 2 정식 구입 후 추가
4. `iccwbo.org` 본 페이지를 ref 로 추가

검증 (대체 PDF):
- pages: 18 / chars: 44,501
- 11 Incoterms 코드 전부 명시 (EXW/FCA/FAS/FOB/CFR/CIF/CPT/CIP/DAP/DPU/DDP)
- E/F/C/D 4 카테고리 분류 명확
- 시연 narrative: "Incoterms 2020 표준 코드 기반 우리 시스템" — 자료 confirmed.

**교훈**: third-party mirror URL 신뢰 위험 — 정부/공식 도메인 우선. 정기적인
REGISTRY 재검증 (예: 분기별 fetch --force) 필요.

---

## 🟢 #036 — 5 언어 mail-draft 라이브 동작 confirm (es·ar·ru·fr·en)

**발견일:** 2026-05-10
**상태:** 🟢 confirmed

5 시드된 거래로 멀티-language mail-draft 라이브 검증:

| 거래 | 언어 | 시나리오 | 출력 |
|---|---|---|---|
| DO Rodriguez | es | quote | "Cotización: Hyundai Sonata 2020 - VIN..." |
| LY Sahara | ar | shipping | "إشعار شحن لسيارة Hyundai Sonata 2018..." (RTL OK) |
| KG ABC Auto | ru | inquiry | "Ответ на Ваш запрос: Genesis G80 2022..." |
| KE East Africa | en | negotiate | "Regarding Hyundai Tucson 2017... Price Review" |
| DO 강제 fr | fr | inquiry | "Demande de renseignements - Hyundai Sonata 2020..." |

전 5 언어 buyer name + vehicle + VIN 정확 merge. RTL (Arabic) 도 정상.
Gemini 2.5-flash 가 모든 언어 격식체 + 자동차 도메인 어휘 정확.

→ Frontend 의 RTL 전환 (`dir={result.language === "ar" ? "rtl" : "ltr"}`)
   과 결합하면 시연 narrative 완성.

---

## 🟢 #035 — Gemini JSON parse fail ~30% (영어) → 자동 retry 추가 (FIX)

**발견일:** 2026-05-10
**상태:** 🟢 fixed in backend

5회 KE EN negotiate 호출 → 1회 fail (~30%). Error: "LLM did not return
valid JSON (Unterminated string at pos 112)". Gemini 가 영어 long response
에서 종종 JSON closing quote 누락.

이전: 502 응답 + 사용자 수동 retry 필요.

수정 (`backend/app/api/listings.py:395-434`):
- 자동 retry 2회 추가 (총 3 시도)
- `MailDraftParseError` 만 재시도 (다른 LLM 오류는 즉시 raise)
- 로그: "mail-draft JSON parse fail attempt N/3" / 성공 시 "succeeded on retry N/3"

라이브 검증 (재시작 후):
- 5/5 SUCCESS (이전 ~70%)
- 사용자 입장 latency: 정상 ~5s, fail-then-retry ~10s

---

## 🟢 #034 — HS code 자동 분류기 신설 (FIX 완료)

**발견일:** 2026-05-10
**상태:** 🟢 fixed in backend

이전: `vehicle.hs_code or "8703.23"` hard-default → 사용자가 hs_code 비워두면
모든 차량이 1500-3000cc 가솔린으로 분류됨 (실제로는 트럭/버스/EV/디젤 등 다양).

신설 `backend/app/core/hs_classifier.py` (HS 2022 기준):
- 8702.10/.20/.30/.40/.90 (≥10인승 버스)
- 8703.21~.24 (가솔린, 배기량별)
- 8703.31~.33 (디젤, 배기량별)
- 8703.40/.50 (HEV, 가솔린/디젤)
- 8703.60/.70 (PHEV, 가솔린/디젤)
- 8703.80 (BEV)
- 8704.21~.32 (트럭, GVW + 연료별)

분류 로직: body_type → fuel_type → engine_cc 순. confidence 점수 (0.0~1.0)
포함 — truck/van 은 좌석수/GVW 모름으로 0.6-0.7, ICE 가솔린/디젤은 배기량
명확하면 0.95.

🐛 분류기 작성 중 substring bug 발견 + fix:
- "HEV" 가 "EV" substring 매치 → BEV 로 잘못 분류되던 bug
- `_matches_any()` helper 로 단어 단위 정확 매치 (split + set 교집합)

backend/app/api/listings.py 의 fallback 정정:
```python
hs_code=vehicle.hs_code or hs_classifier.classify(
    body_type=vehicle.body_type,
    fuel_type=vehicle.fuel_type,
    engine_cc=vehicle.engine_cc,
).hs_code
```

---

## 🟡 #033 — Grand Starex (van + 2.5L diesel) → 8702.10 vs 8703.32 모호

**발견일:** 2026-05-10
**상태:** 🟡 noted (12-seat 가정)

WCO HS 2022:
- 8702 = 운송 차량 ≥10 seats incl driver
- 8703 = 승용차 ≤9 seats

Grand Starex 는 7인승 / 9인승 / 12인승 모델 존재. 우리 시드는 12-seat 가정
하여 8702.10 (디젤 ≥10seats). 7-9 seats 면 8703.32.

→ Vehicle 모델에 `seats` 컬럼 추가 시 자동 분류 정확도 ↑ (Phase 2).

---

## 🟢 #032 — Avante 1591cc HS code 잘못 (FIX 완료)

**발견일:** 2026-05-10
**상태:** 🟢 fixed in seed

WCO HS 2022 8703 세분:
- 8703.21: ≤1,000cc / 8703.22: 1,000-1,500cc / **8703.23: 1,500-3,000cc**

Avante 1591cc 는 1500cc 초과 → 8703.23 가 정확. 우리 시드는 8703.22 로
잘못 분류 (Avante 표준 1.6L 모델로 추정해서 1500 경계 잘못 적용).

수정: `scripts/seed_demo_data.py` Avante hs_code "8703.22" → "8703.23".
재시드 후 라이브 confirm.

---

## 🟢 #028 — 실제 생성된 4종 PDF 필드 검증 (DO 거래 예시)

**발견일:** 2026-05-10
**검증 자료:** 라이브 생성된 4 PDF (DO listing aeb34437, Sonata 2020 → Rodriguez)
**상태:** 🟢 confirmed (all fields present)

`POST /api/listings/{id}/documents` → 4종 PDF 생성 → pymupdf 텍스트 추출 →
필드 매트릭스 cross-check:

| 문서 | 페이지 | 핵심 필드 (전부 confirmed) |
|---|---|---|
| invoice | 1p | Hyundai Sonata 2020 · VIN KMHE41LBXLA000001 · 8703.23 HS · $14,000 · Rodriguez Motors · Santo Domingo |
| packing_list | 1p | Vehicle desc · VIN as Marks · Net 1,480 / Gross 1,620 KG · "Marks & Numbers" |
| shipping_instruction | 1p | B/L wording 대문자 · "TO ORDER" if L/C · VIN stenciled on door post |
| co_application | 1p | HS 8703.23 · **ORIGIN CRITERION: WO (Wholly Obtained)** · Producer Same as Exporter |

→ 단순 템플릿이 아니라 실제 데이터 (vehicle spec + buyer + listing) 가 정확히
   merge 됨. 한국식 주소 + 스페인어 bilingual (Sr. Carlos Rodríguez) + FTA C/O
   Origin Criterion (WO) 까지 정확.

End-to-end 검증 완료: YAML 룰 → import-check → listing → 4 PDF 생성 → 필드 매칭.

---

## 🟡 #027 — Cuba (CU) 가 compliance.py 에 있지만 YAML 없음 (Phase 2 후보)

**발견일:** 2026-05-10
**상태:** 🟡 noted (PoC 영향 없음)

`backend/app/core/compliance.py:SANCTIONED_COUNTRIES = {SY, SD, CU, MM}` 에는
Cuba (CU) 가 있지만 `configs/rules/cuba.yaml` 은 시드되지 않음. Cuba 바이어를
랜덤 풀에 추가하려면:
1. `configs/rules/cuba.yaml` 작성 (is_blocked + OFAC 제재)
2. COUNTRY_FLAG 에 🇨🇺 추가
3. 시드 재실행

PoC 시연 narrative 영향 없음 — 미얀마/시리아/수단 3개로 충분.

---

## 🟢 #026 — 메일 LLM 언어 fallback 강화 (FIX 완료)

**발견일:** 2026-05-10
**상태:** 🟢 fixed in backend

28개국 중 **12국** 의 primary_language 가 MailWriter `LANGUAGE_NAMES`
미지원:

| Country | primary | business | 위험 |
|---|---|---|---|
| KZ | kk (Kazakh) | ru ✓ | high (자국어 우선) |
| AZ | az (Azerbaijani) | ru ✓ | high |
| KH | km (Khmer) | en ✓ | medium |
| BD | bn (Bengali) | en ✓ | medium |
| KG | ky (Kyrgyz) | ru ✓ | medium |
| MY | ms (Malay) | en ✓ | medium (auto-blocked) |
| MM | my (Burmese) | en ✓ | low (auto-blocked) |
| PH | tl (Tagalog) | en ✓ | medium |
| LK | si (Sinhala) | en ✓ | low |
| TZ | sw (Swahili) | en ✓ | medium |
| TH | th (Thai) | en ✓ | low (auto-blocked) |
| VN | vi (Vietnamese) | en ✓ | high |

이전 fallback (`buyer.preferred_language → country.primary_language → en`)
는 buyer 가 preferred_language 비어있으면 raw "kk"/"vi"/"th" 같은 코드가
Gemini prompt 에 직행. LLM 이 이상한 언어로 응답하거나 영어로 fallback 할
수 있음 — 일관성 없음.

수정 (`backend/app/api/listings.py:377-396`):
```python
_SUPPORTED_LLM_LANGS = {"en", "es", "ar", "ru", "fr", "ko"}

def _supported(lang): return lang if lang in _SUPPORTED_LLM_LANGS else None

language = (
    _supported(payload.language)
    or _supported(buyer.preferred_language if buyer else None)
    or _supported(country.primary_language)   # 지원 코드만 통과
    or _supported(country.business_language)  # 폴백 거쳐 영어/러시아어
    or "en"
)
```

→ KZ/AZ/KG → ru / KH/BD/MY/MM/PH/LK/TZ/TH/VN → en. 일관성 있음.

---

## 🟢 #025 — 짐바브웨 CBCA 2015.5.16~ 강제 + SADC C/O 우대 (notes 추가)

**발견일:** 2026-05-10
**검증 자료:** `docs/samples/zimbabwe/CBRTA_Zimbabwe_Handbook_2018-05-17.pdf`
**상태:** 🟢 noted

CBRTA 명시 deep:
- "any consignment on the category list not accompanied with the required
  CBCA certificate will be refused from entering the country" (2015.5.16 발효)
- 카테고리: Food/Agriculture, Building/civil engineering, Timber, ...
- SADC 회원국 화물은 SADC Certificates of Origin 우대
- Cross-border charges: Yellow card, New Limpopo Bridge fee, Carbon tax,
  EMA fee 등 transit 시 추가 비용

→ #012 (CBCA 2단계 검사) 보강. is_blocked 차단 정책 정당화 + SADC 회원
   바이어 narrative 강화.

---

## 🟡 #024 — 스리랑카 일반 승용차 룰 NITG Preamble 외 (보수적 추정)

**발견일:** 2026-05-10
**검증 자료:** `docs/samples/sri_lanka/Sri_Lanka_Customs_NITG_2024_Preamble.pdf`
**상태:** 🟡 noted (Phase 2 deeper)

NITG Preamble Chapter 87 deep search: **"ambulance more than 03 years old"**
만 명시 (Director General of Health Services 추천 필요). 일반 승용차 연식
룰은 NITG Preamble 외 chapter detail 또는 MOC announcements 에 있음.

우리 YAML `sri_lanka.yaml` 3년 룰은 ambulance 룰 일반화 + 외환위기 후 보수적
정책 추정. 정확한 일반 승용차 룰은 별도 source (Sri Lanka Customs detail
chapter 또는 Department of Trade announcements) 필요.

---

## 🟢 #023 — 한국 영문 수출신고필증 + FTA 원산지 선적후 발급 (narrative 강화)

**발견일:** 2026-05-10
**검증 자료:** `docs/samples/korea_customs/UNIPASS_FAQ_2023-11-17.pdf`
**상태:** 🟢 noted (narrative 강화)

UNIPASS FAQ 2023-11 명시:
- 영문 수출신고필증 발급 가능 (FAQ #5) — 외국 바이어 제출용
- FTA 원산지증명서 선적후 발급 가능 (FAQ #10) — '선적후 발급' 문구 기재
- 협정관세 적용 신청서 (FAQ #6)
- 통관고유부호 발급 절차 (FAQ #1-3)

→ 우리 시연 narrative: "메일 자동 생성 + 4종 PDF 외에 한국 측 절차 (UNIPASS,
   대한상공회의소 C/O, 영문 수출신고필증) 와도 호환". 수출 흐름의 한국 측 부분
   별도 채널이지만 우리 시스템과 매끄럽게 연결됨.

---

## 🟢 #022 — Korea FTA Annex 5B C/O 양식 15 필드 (우리 템플릿 정합성 confirm)

**발견일:** 2026-05-10
**검증 자료:** `docs/samples/fta_co/Korea_FTA_Annex5B_CO_format.pdf`
**상태:** 🟢 confirmed (template OK)

Korea-Singapore FTA Annex 5B C/O 양식 15 필드:
1. Exporter / 2. Importer / 3. Departure Date / 4. Vessel's Name/Flight No /
5. Port of Discharge and Route / 6. Country of Final Destination /
7. Country of Origin / 8. Item Number / 9. Description of Goods /
10. HS No. (6digit) / 11. Marks & Numbers / 12. Quantity & Unit /
13. **Origin Criterion** / 14. Declaration by Exporter / 15. Certification

우리 `co_application.html` 템플릿 16/17 (gaps=0) 이미 검증. FTA 활용 시 필요한
'Origin Criterion' 필드도 우리 템플릿에 포함됨 (validate_document_fields.py
이전 round 에서 추가).

→ Chile / Costa Rica YAML 의 `fta_certificate_of_origin` 항목이 실제 양식과
   필드 매칭 confirmed.

---

## 🟢 #021 — SONCAP 비용표 정확화 (notes 추가)

**발견일:** 2026-05-10
**검증 자료:** `docs/samples/psi/SON_SONCAP_approved_fees_2022-08.pdf`
**상태:** 🟢 noted

SON 공식 fees 2022-08-01 발효:
- SONCAP Certificate (SC): **$350 per shipment**
- Product Certificate (Unregistered): $500 / (Registered): $1000 /
  (Licensed): $2000
- New Product / Non-Conformity Report: $350 / Amendment: $100

→ `nigeria.yaml` notes 에 정확한 비용 명시. 멘토 "비용 narrative 가능?"
   질문에 즉답 가능.

---

## 🟢 #020 — 한국 수출신고필증은 우리 시스템 4종 외 (관세사 EDI)

**발견일:** 2026-05-10
**검증 자료:** `docs/samples/korea_customs/KITA_export_declaration_form_loaded_pre.pdf`
**상태:** 🟢 noted (스코프 명확화)

KITA 수출신고필증 양식 — 신고자/세관/신고번호/신고일자/수출자/주소/사업자등록번호/
거래구분/결제방법/목적국/적재항/선박회사/적재예정보세구역/물품소재지/HS코드/단가/금액 등
30+ 필드. 관세사 EDI (UNI-PASS) 통해 발급 — 우리 시스템이 직접 생성하지 않음.

우리 자동 생성 4종 (Invoice / PL / SI / CO) 은 **수출자 → 바이어** 방향 문서.
수출신고필증은 **수출자 → 한국 관세청** 방향 — 별도 채널 (관세사 위임).

→ data_audit.md 의 "검증 못 한 영역" 에 명시. Phase 2 에서 관세사 EDI 통합 후보.

---

## 🟢 #019 — UAE Vehicle Clearance Certificate (VCC) 추가 (FIX 완료)

**발견일:** 2026-05-10
**검증 자료:** `docs/samples/uae/Dubai_Customs_customer_guide_EN.pdf`
**상태:** 🟢 fixed in YAML

Dubai Customs Customer Guide (52p, 정부 직접) 명시: "Vehicle Clearance
Certificates (VCC)" 별도 챕터 (§23) — 차량은 일반 화물 외 별도 인증 필요.

또 다른 새 정보:
- 5% 관세 + 5% VAT (CIF 기준)
- Free Zone (Jebel Ali, Sharjah) 별도 절차 — 면세 가능
- Private Customs Warehouse 2년 저장 + 1년 연장
- Client Accreditation Program (CAP) 1년 유효

수정: `uae.yaml` required_documents 에 `vehicle_clearance_certificate` 추가
+ notes 에 5% 관세 / Free Zone / CAP 명시.

---

## 🟢 #018 — 나이지리아 SONCAP 3 routes + 6개 IAF (FIX 완료)

**발견일:** 2026-05-10
**검증 자료:** `docs/samples/psi/SGS_PCA_Nigeria_datasheet.pdf`
**상태:** 🟢 fixed in YAML

SGS PCA Nigeria datasheet 명시:
- SONCAP 3 routes:
  - Route A: per-shipment, 6개월 유효 (한국 발 single-shipment 일반)
  - Route B: Registered Product Certificate, 1년 유효 (manufacturer 검증)
  - Route C: Licensed Certificate, 1년 + 공장 audit
- IAF (Independent Accredited Firms): SGS · Intertek · Cotecna · CCIC ·
  BV · CSIC — 수출자/수입자 선택
- 매 shipment 별 SC (SONCAP Certificate) 필수 — Product Cert 와 별개

수정:
- `nigeria.yaml` required_documents 분리: `soncap_sc_per_shipment` +
  `product_certificate_route_b_or_c` (이전 단일 `soncap_certificate`)
- notes 에 3 routes + IAFs 상세 명시

---

## 🟢 #017 — 스리랑카 NITG 2024 는 종합 관세표 (차량 specific 룰 별도)

**발견일:** 2026-05-10
**검증 자료:** `docs/samples/sri_lanka/Sri_Lanka_Customs_NITG_2024_Preamble.pdf`
**상태:** 🟢 noted (Phase 2 보강 후보)

NITG 2024 는 78p 종합 HS 코드 + 권장 표준 가이드 — 차량 specific 룰 (연식·
관세·MOC announcements) 은 별도 추적 필요. 우리 3년 룰은 외환위기 (2020-2024)
재개방 후 보수적 추정 — 현재 정확성은 MOC announcements 모니터링 필요.

---

## 🟢 #016 — 방글라데시 USDA Exporter Guide 자동차 정보 부족 (notes 추가)

**발견일:** 2026-05-10
**검증 자료:** `docs/samples/bangladesh/USDA_Bangladesh_Exporter_Guide_2024.pdf`
**상태:** 🟢 noted (BRTA 1차 자료 수동 보강 필요)

USDA Foreign Agricultural Service 의 Exporter Guide 는 농업 수출 위주로,
차량 import 룰은 거의 다루지 않음. 우리 5년 한도는 JAAI 산업 자료 기반 추정.
Phase 2: BRTA 공식 vehicle import guideline PDF 수동 다운로드 필요.

---

## 🟢 #015 — 필리핀 12개월 consignee 등록 의무 (notes 추가)

**발견일:** 2026-05-10
**검증 자료:** `docs/samples/philippines/PHILIPPINES_Import_FIDI_Customs_Guide_2024-06.pdf`
**상태:** 🟢 noted (Phase 2 enforcement)

FIDI 2024-06 명시:
- "Cars not exceeding 1500 kgs weight and 2800 cc engine displacements"
- "must be registered under consignee's name for at least 12 months"
- "Returning residents, Dual Citizens, and holders of 13G or 13A visa
  are allowed... approximately 200% of car book value for duties and taxes"
- Prior Authority to Import from Bureau of Import Services (BIS)

우리 YAML 의 `engine_cc>2800cc` blocked_condition ✓ confirmed.
12개월 consignee 등록 + 1500kg 한도 + 200% 관세는 enforcement Phase 2.

---

## 🟢 #014 — 캄보디아 LHD only 명시 (FIX 완료)

**발견일:** 2026-05-10
**검증 자료:** `docs/samples/cambodia/CAMBODIA_Import_FIDI_Customs_Guide_2024-01.pdf`
**상태:** 🟢 fixed in YAML

FIDI Cambodia 2024-01 명시: "**Motor vehicle must be left-hand driven**"

우리 YAML `cambodia.yaml`: 처음 작성 시 "RHD 단속 느슨" 으로 추정해서
`steering_required: any` 로 했지만, FIDI 1차 자료는 strict LHD 명시.

수정: `steering_required: any → LHD_only`. 노트도 정정.
관세 60-125% + 정부세 10-50% 도 FIDI 명시로 보강.

---

## 🟢 #013 — 알제리 fiscal HP 10 CV 한도 + CIF 3M DZD 한도 (notes 추가)

**발견일:** 2026-05-10
**검증 자료:** `docs/samples/algeria/IAM_Algeria_Country_Guide_2024-09.pdf`
**상태:** 🟢 noted (PoC enforcement 외 — Phase 2 후보)

IAM 명시:
> "The maximum allowable engine power is 10 HP."
> "The combined CIF value of the goods and vehicle must not exceed 3 000 000 DZD."

10 HP 는 fiscal horsepower (chevaux fiscaux, CV) — 프랑스/알제리 세무 단위.
일반 가솔린 차량 ~150-200 실 HP 상당. 한국 평균 중고차 (2.0L 가솔린) 는 fiscal CV
약 8-9 라 통과. CIF 3M DZD ≈ USD 22,000 — 일부 고가 차량은 한도 초과 가능.

YAML `algeria.yaml`: notes 에 명시. 룰엔진 enforcement 는 Phase 2 (실제 fiscal HP
계산 공식 + 환율 변동 처리 필요).

---

## 🟢 #012 — 짐바브웨 Bureau Veritas CBCA + VID 2단계 검사 (FIX 완료)

**발견일:** 2026-05-10
**검증 자료:** `docs/samples/zimbabwe/CBRTA_Zimbabwe_Handbook_2018-05-17.pdf`
**상태:** 🟢 fixed in YAML

CBRTA 명시: "The Government of Zimbabwe has signed on 16/03/15 a 4-year
Consignment-Based Conformity (CBCA) contract with a French global company,
Bureau Veritas. This contract provides the pre-shipment services."

우리 YAML `zimbabwe.yaml`: `psi_required: [VID_Inspection]` 만 있어 도착 후
검사만 반영. 선적 전 Bureau Veritas CBCA 누락.

수정: `psi_required: [Bureau_Veritas_CBCA, VID_Inspection]` 2단계 + required_documents
에 `bureau_veritas_cbca_certificate` 추가.

---

## 🟡 #011 — 남아공 returning resident 예외 (notes 추가)

**발견일:** 2026-05-10
**검증 자료:** `docs/samples/south_africa/SOUTH_AFRICA_Import_FIDI_Customs_Guide_2024-09.pdf`
**상태:** 🟡 noted (PoC narrative 보존)

FIDI: returning/temp resident 는 DA 304/A + DTI Import Permit + LOA + "in the
owner's use and possession abroad for more than 365 days" 증빙 시 import 가능.

우리 YAML `is_blocked: true` 는 B2B commercial 채널 기준으로는 정확. 단 ZA 는
완전 차단 국가가 아니라 narrowly conditional 채널만 열려있는 국가.

수정: notes 에 명시. is_blocked: true 유지 (B2B 시연 narrative).

---

## 🟢 #010 — 멕시코 8-9년 window + NAFTA 원산지 (FIX 완료)

**발견일:** 2026-05-10
**검증 자료:** `docs/samples/mexico/SNICE_Decreto_Vehiculos_Usados_2024-07-04.pdf`
**상태:** 🟢 fixed in YAML

SNICE Decreto 2024-07-04 (DOF 2011-07-01, 최종 개정 2022-11-18):
- 일반 권역: "vehículos cuyo año modelo sea de **ocho a nueve años** anteriores"
  (8-9년 window, 10% 관세, NAFTA 원산지 필요)
- 국경 권역 (Cananea/Caborca, Sonora): 5-9년 window
- 5년 이내는 별도 import permit 필요 (Secretaría de Economía)

우리 YAML `age_limit_years: 8` 는 "max 8" 의미라 부정확. 9년까지 허용 + 새 차량은
permit 별도.

수정: `age_limit_years: 9` (max 9) + notes 에 8-9 window + NAFTA 원산지 명시.

---

## 🟢 #009 — 케냐 연식 cutoff 날짜 부정확 (FIX 완료)

**발견일:** 2026-05-10
**검증 자료:** `docs/samples/kenya/KEBS_2023-12_notice_to_importers.pdf` (1차)
**상태:** 🟢 fixed in YAML

KEBS 2023-12 공지: "**8 year age limit + RHD only + Year of First Registration
1st January 2017 and later, effective 1st January 2024**".

우리 YAML `kenya.yaml`: `registration_after_date: 2019-01-01` + `age_effective_from: 2026-01-01` 였음.
- 2024.1.1 시점: 2017+ (8년 ←) — 1차 자료 일치
- 2026.1.1 시점: 2018+ (8년 ←) — 우리 2019 잘못됨 (1년 어긋남)

수정: `registration_after_date: 2018-01-01` (8년 룰 직접 적용).

---

## 🟢 #008 — 가나 RHD 허용 (LHD_only 잘못됨, FIX 완료)

**발견일:** 2026-05-10
**검증 자료:** `docs/samples/ghana/GHANA_Import_FIDI_Customs_Guide_2023-09.pdf`
**상태:** 🟢 fixed in YAML

FIDI Ghana 2023-09: "**Right-hand drive vehicles are permitted, BUT a steering
wheel removal fee is charged at the port prior to the release of the vehicle.**"

우리 YAML `ghana.yaml`: `steering_required: LHD_only` (잘못됨 — 우리가 처음 작성 시
top20 doc 기준으로 LHD 만 허용으로 잘못 추정).

수정: `steering_required: any` + 노트에 "RHD 시 항구에서 핸들 제거 수수료 필요".

---

## 🟢 #007 — 요르단 디젤 승용차 금지 (FIX 완료)

**발견일:** 2026-05-10
**검증 자료:** `docs/samples/jordan/JORDAN_Import_FIDI_Customs_Guide.pdf`
**상태:** 🟢 fixed in YAML

FIDI Jordan: "**Not allowed: ... Passenger cars operating on diesel.**"
우리 YAML `jordan.yaml` 5년 룰은 ✓ 일치. RHD 금지 ✓ 일치. 단 디젤 승용차 금지 누락.

수정: `blocked_conditions[fuel_type in [Diesel] AND body_type=passenger]` 추가.

---

## 🟡 #006 — 카자흐스탄 Euro 5 표준 필요 + RHD 차단 (LHD 는 정상 일치)

**발견일:** 2026-05-10
**검증 자료:** `docs/samples/kazakhstan/KAZAKHSTAN_Import_FIDI_Customs_Guide.pdf`
**상태:** 🟡 noted (Euro 5 enforcement 는 PoC 스코프 외)

FIDI Kazakhstan:
- "**They must conform to Euro 5 standard.**" (배기가스 표준)
- "**Right-side vehicles are prohibited for import to Kazakhstan since January 1, 2007.**"
- "**Excise-duty for the car with the engine volume more than 3000 cm**" (≠ 우리 2000cc 한국 전략물자 룰)

우리 YAML `kazakhstan.yaml` 의 `LHD_only` ✓, Russia-proxy 조건 (engine>2000cc, HEV/EV,
price>$50k) 은 한국 전략물자 수출 차단 룰 (KG/KZ 동일) — 카자흐 자국 수입 룰과는 다른
관점 (둘 다 의미 있음). Euro 5 는 노트에만 추가.

---

## ✅ #001 — 도미니카공화국 연식 룰 불일치 (RESOLVED 2026-05-10)

**발견일:** 2026-05-09 / **해소일:** 2026-05-10
**검증 자료:** `docs/samples/dominican_republic/DOMINICAN_REPUBLIC_Import_FIDI_Customs_Guide_2024-10.pdf`

FIDI Dominican Republic 2024-10 명시:
> "**The year of fabrication of the car cannot be older than 5 years; otherwise,
> customs forbid its importation.**"

→ U.S. Department of Commerce + Contadores Dominicanos 의 5년 룰이 정확.
   우리 YAML `dominican_republic.yaml` 의 10년은 잘못됨.
수정 적용: `passenger.age_limit_years: 10 → 5`. 트럭 10년·버스 7년은 차종 범주
차이로 그대로 유지 (FIDI 는 통합 5년 명시).

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
