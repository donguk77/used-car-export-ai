# 데이터 수집·검증 종합 분석 (2026-05-10, v2)

> 수출 룰 엔진(`configs/rules/*.yaml`)을 1차 권위 자료(`docs/samples/`)와
> cross-validate 한 결과. 발표·멘토 미팅용 종합 분석.
>
> 자세한 개별 finding: `docs/validation/findings.md` (#001~#017)
> 검증 도구: `scripts/read_pdf_excerpt.py` (pymupdf 기반)

---

## 1. 전체 현황 (v2 — 28개국 확장 후)

| 카테고리 | 수치 | 비고 |
|---|---|---|
| 시드된 국가 | **28** | 5 → 20 → **28** (ASEAN 6 + 남아 2 추가) |
| ImportRule 행 | **30** | DO 가 차종별 3개 (passenger/bus/truck) |
| 1차 자료 PDF (실제 보유) | **47** | 27/28 국가 + 공통 자료 5종 |
| 1차 자료 URL 인덱스 (REGISTRY) | **89 entries** | 62 pdf + 27 ref |
| Cross-validate 검증 | **22개 PDF** | findings 식별을 위한 실제 텍스트 검토 |
| 발견된 finding | **14개** | #001 + #006~#017 |
| YAML 수정 적용 | **7개국** | DO·KE·JO·GH·MX·ZW + KH (LHD only) |
| YAML notes 추가 | **6개국** | KZ·DZ·ZA + PH·BD·LK |

---

## 2. 자료 출처별 신뢰도 매트릭스

| 출처 카테고리 | 건수 | 신뢰도 | 활용 |
|---|---|---|---|
| **국가 정부 직접** | 14 | ⭐⭐⭐⭐⭐ | KE KEBS, LY ACI, MX SNICE, TZ TBS, CL BCN 의회도서관, ZW ZIMRA, NG SON, AE Dubai Customs |
| **국제 기구** | 4 | ⭐⭐⭐⭐⭐ | OFAC (SD), WCO (AZ), UNECE (AZ), ICC (Incoterms) |
| **FIDI Customs Guide** | 11 | ⭐⭐⭐⭐ | 글로벌 표준 (DO·EG·JO·KZ·CR·AZ·NG·GH·DZ·ZA·UAE) |
| **PSI 인증사** | 2 | ⭐⭐⭐⭐ | SGS PCA Nigeria, SON SONCAP fees |
| **선사 BL 샘플** | 2 | ⭐⭐⭐⭐ | Maersk, CMA CGM |
| **한국 표준** | 6 | ⭐⭐⭐⭐⭐ | 관세청 UNI-PASS, KITA 수출신고필증, 대한상공회의소 C/O |
| **3rd party 가이드** | 3 | ⭐⭐⭐ | USDoC CCG (KG), SGE Kazakhstan, IAM Algeria |
| **이주 협회** | 1 | ⭐⭐⭐ | CBRTA Zimbabwe Handbook |

→ 정부 직접 + 국제 기구 = 18 PDF (47%) — capstone PoC 로는 충분한 grounding.

---

## 3. 발견 (Findings) 분류

### 🔴 Hard error (룰 자체가 틀림) — 3건

| # | 국가 | 이전 YAML | 정정 YAML | 출처 |
|---|---|---|---|---|
| #001 | **DO** | passenger 10년 | passenger **5년** | FIDI 2024-10 명시 |
| #008 | **GH** | LHD_only | **any** (RHD 시 핸들 제거 수수료) | FIDI 2023-09 명시 |
| #014 | **KH** | any (RHD 단속 느슨 추정) | **LHD_only** | FIDI 2024-01 명시 |

→ 이 둘은 **잘못 보내면 통관 거부** 되는 hard error. fix 안 됐으면 데모에서
Sonata 2020 → DO 가 통과됐을 텐데 (실제론 차단), 멘토가 1차 자료 cross-check
하면 즉시 적발됐을 risk.

### 🟡 Soft drift (룰 부분적 부정확 / cutoff 어긋남) — 3건

| # | 국가 | 이전 | 정정 | 출처 |
|---|---|---|---|---|
| #009 | **KE** | registration_after 2019-01-01 | **2018-01-01** (1년 어긋남) | KEBS 2023-12 |
| #010 | **MX** | age_limit 8년 | **9년** (8-9 window) | SNICE Decreto 2024-07-04 |
| #007 | **JO** | (디젤 ban 누락) | **fuel_type=Diesel blocked_condition 추가** | FIDI 2024-01 |

### 🟢 신규 룰 추가 (누락 검사 항목) — 1건

| # | 국가 | 추가 | 출처 |
|---|---|---|---|
| #012 | **ZW** | psi_required 에 Bureau_Veritas_CBCA 추가 (이전 VID_Inspection 만) | CBRTA 2018 Handbook |

### 🟡 Notes 추가 (PoC enforcement 외) — 3건

| # | 국가 | 노트 추가 사유 |
|---|---|---|
| #006 | **KZ** | Euro 5 표준 + 자국 excise duty engine>3000cc (≠ 한국 전략물자 2000cc) |
| #011 | **ZA** | returning/temp resident 예외 (B2B 외 narrowly conditional 채널 존재) |
| #013 | **DZ** | fiscal HP 10 CV 한도 + CIF 3M DZD 한도 (실제 환율 적용 필요) |

---

## 4. 검증 못 한 영역 (남은 risk)

| 항목 | 현황 | risk |
|---|---|---|
| 5개국 PDF 0건 | SY 만 — auto-blocked 카테고리 | 낮음 (시연 narrative 영향 없음) |
| FIDI 가 personal effects 위주 | EG/CR/AZ 등 — commercial vehicle 룰 직접 검증 안됨 | 중간 — 멘토가 깊게 물어보면 답 부정확 가능 |
| 일부 정부 PDF 다운로드 실패 | MX SAT (timeout), NG Pakistan (403), AZ WCO/UNECE (SSL) | 낮음 — REGISTRY 에 ref 로 추적 |
| Korean→Arabic / French 번역 룰 | YAML 의 `doc_translation_lang` 만 명시, 실제 LLM 출력 검증 안됨 | 중간 — Phase 2 |
| 실제 1차 법령 (예: 칠레 Ley 18.483, 알제리 Decree 2014/123) | 검증 PDF 는 BCN/FIDI summary 위주 | 낮음 (요약본도 1차로 인용 가능) |

---

## 5. 재현 가능성 (Reproducibility)

전체 검증 워크플로우는 자동화 — 멘토 미팅 후 추가 발견 시 동일 패턴 반복:

```bash
# 1. 신규 자료 등록
$ vim configs/samples_registry.yaml  # 새 출처 추가
$ py -X utf8 scripts/fetch_public_samples.py  # 자동 다운로드

# 2. 검증
$ py -X utf8 scripts/read_pdf_excerpt.py docs/samples/{country}/file.pdf "year" "vehicle"

# 3. finding 기록
$ vim docs/validation/findings.md  # # NN — ... 항목 추가

# 4. YAML 수정 + 재시드
$ vim configs/rules/{country}.yaml
$ cd backend && py -X utf8 -m app.seed.import_rules

# 5. 라이브 검증
$ curl -X POST http://localhost:8000/api/listings/import-check ...
```

---

## 6. 멘토 발표 시 강조할 점

### 6.1 데이터 grounding 의 정량화

> **"20개국 룰을 자기 작성한 게 아니라 38개 1차 자료와 cross-validate
> 했고, 13개 PDF 를 실제 텍스트로 읽어 9개 discrepancy 를 발견·수정했다."**

→ 단순 "구현했다" 가 아닌 "검증했다" — capstone 차별화 포인트.

### 6.2 트래킹 시스템 자체가 deliverable

- `samples_registry.yaml` — 신뢰 자료 카탈로그 (80 entries)
- `fetch_public_samples.py` — 자동 다운로드 (38/53 pdf 성공)
- `read_pdf_excerpt.py` — 텍스트 검증 (pymupdf)
- `findings.md` — 9 finding 트래킹 (#001~#013)
- `data_audit.md` — 종합 분석 (이 문서)

→ Phase 2 에서 새 국가 추가 / 룰 갱신 시 재사용 가능한 인프라.

### 6.3 정직한 한계 명시

- FIDI 가이드는 personal effects/이주 위주 — commercial vehicle 룰은 부분 검증
- 일부 정부 사이트 robust fetch 안됨 (login/JS/SSL) — 수동 보강 필요
- LLM 번역 정확성 (특히 아랍어/러시아어) 별도 검증 안됨 — Phase 2

---

## 7. 변경 이력

- 2026-05-09: findings #001~#005 (기존 PDF 기반 1차 검증)
- 2026-05-10: findings #006~#013 추가 (WebSearch + 38 PDF cross-validate)

---

## 부록 A — 검증된 13개 PDF 인덱스

| 국가 | 자료 | 페이지 | 발견 |
|---|---|---|---|
| DO | FIDI 2024-10 | 7p | ✅ #001 RESOLVED (5년 확정) |
| JO | FIDI 2024-01 | 8p | ✅ #007 (디젤 금지) + 5년 + RHD 금지 confirm |
| EG | FIDI 2024-01 | 9p | ✓ 사실상 신차 + 디플로마트 위주 confirm |
| KZ | FIDI 2024-07 | 13p | ✅ #006 (Euro 5 + RHD 2007.1 차단) |
| KE | KEBS 2023-12 + 2025-07 | 1p+1p | ✅ #009 (2017 cutoff → 2018-01-01) |
| GH | FIDI 2023-09 | 6p | ✅ #008 RESOLVED (RHD 허용) |
| TZ | TBS PVoC 2025 | 8p | ✓ JEVIC + EAA + QISJ 인증사 confirm |
| ZA | FIDI 2024-09 | 7p | ✅ #011 (returning resident 예외 노트) |
| ZW | CBRTA 2018 + Trade Zimbabwe | 15p+22p | ✅ #012 (Bureau Veritas CBCA 추가) |
| MX | SNICE Decreto 2024-07 | 7p | ✅ #010 (8-9년 window + NAFTA 원산지) |
| CR | FIDI 2024-01 | 8p | ✓ DEKRA 검사 + Total Loss 차단 |
| AZ | FIDI 2022-01 | 7p | ✓ Diplomat 위주 + 임시 2년 한도 confirm |
| DZ | IAM 2024-09 + FIDI 2024-01 | 5p+7p | ✅ #013 (10 CV + CIF 3M DZD 한도) |
| SD | OFAC FACRL-SU-01 | 3p | ✓ E.O. 13412/13067 + 라이선스 의무 confirm |
| KG | USDoC CCG 2020 | 37p | ✓ EAEU dynamics confirm (특정 룰 finding 없음) |
| AE | FIDI 2024-07 | 6p | ✓ LHD only + 5% duty + 5% VAT confirm |
| LY | ACI Manual 2024-07 | 16p | ✓ ACI 시스템 사용법 (룰 변경 없음) |
| CL | BCN 의회도서관 v4 | 3p | ✓ Ley 18.483 일반 금지 + 10% 감가 confirm |
