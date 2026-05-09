# 중고차 수출 AI 에이전트 — 필수 데이터 필드 리서치 리포트

> **목적:** 산학캡스톤 "LLM Wiki 기반 수출특화 AI 에이전트" 프로젝트의 데이터 모델 설계 기반 자료
> **타겟 시장:** 동남아 · 아프리카
> **작성일:** 2026.05.09
> **작성자:** 조우진 (한양대 ERICA 수리데이터사이언스)

---

## 0. 요약 (TL;DR)

이 리포트는 중고차 수출 AI 에이전트가 다뤄야 할 **세 종류의 데이터**를 정리한 자료다.

1. **차량 정보 (Vehicle Data)** — 매물을 등록하고 시세 산정/매칭에 쓰이는 속성
2. **수출 서류 정보 (Export Document Data)** — 인보이스/B/L/패킹리스트/수출신고 자동 생성에 필요한 필드
3. **바이어 정보 (Buyer Data)** — 매칭과 다국어 커뮤니케이션에 필요한 속성

부록으로 **타겟국(동남아·아프리카) 수입규제 매트릭스**, **벤치마킹 5분 정리**, **법적 제약 체크리스트**를 붙였다.

핵심 발견:

- 동남아·아프리카는 **연식 제한 + RHD/LHD 제한 + 환경규제**가 핵심 변수. 단일 표준이 없어 **국가별 룰 엔진** 구조가 필수.
- 한국은 **자동차관리법 제13조 말소등록 → 보세구역 반입 → 세관 수출신고**가 법적 프로세스. 이 흐름을 그대로 워크플로우에 박으면 됨.
- BeForward · SBT Japan이 사실상 글로벌 표준. **연식·주행거리·등급·RHD/LHD·소속 항구**가 1차 검색 필터의 코어.

---

## 1. 시장 컨텍스트 (왜 동남아·아프리카인가)

리서치 들어가기 전에 이 시장이 왜 매력적인지부터 짧게.

- **2024년 한국 중고 승용차 수출량 53.3만대 / 47.4억 달러** — 이미 글로벌 메이저. 주요 수출국은 중동·아프리카·중앙아시아.
- 2025년 1~10월 누적 중고차 수출은 **전년 대비 +78%** 성장으로 자동차 수출 전체의 하방 경직성을 지지 (한국자동차산업협동조합).
- 거래 구조가 **브로커 단발성 → 디지털 경매·온라인 플랫폼 반복거래**로 전환 중. "가격보다 신뢰와 데이터가 성패를 가른다"는 업계 평가.
- **2024년 아프리카 수입 1위는 나이지리아 (171,248대 / 27억 달러)**. 그 뒤로 리비아, 케냐, 에티오피아, 가나, 탄자니아, 세네갈, 베냉, 기니, 카메룬 (ScienceDirect 2021).
- 동남아 중고차 시장 규모는 **2024년 181억 달러 → 2034년 277억 달러 (CAGR 4.5%)** 추정 (GMI). 단 동남아는 자국 내 거래 비중이 크고, 한국→동남아 수출은 **베트남·필리핀의 점진적 자유화 흐름**을 노리는 방향.
- **영세 수출업체 비중이 높음** — 산업연구원 분석: "업체 상당수가 영세해 정보 접근성이 낮은 만큼, 글로벌 규제 변화 대응을 위한 정보 체계화가 시급". → AI 에이전트의 정확한 페인포인트.

---

## 2. 차량 정보 (Vehicle Data) 필수 필드

엔카·KCar 같은 한국 플랫폼과 BeForward·SBT 같은 글로벌 수출 플랫폼이 공통적으로 보유한 필드를 통합한 결과.

### 2.1 식별 정보 (Identification)

| 필드 | 한글명 | 필수 | 비고 |
|------|--------|------|------|
| `vin` | 차대번호 (VIN) | ★★★ | 17자리. 한국차는 "K"로 시작. 수출신고 시 필수, 도난·말소 여부 검증 키. |
| `vehicle_id` | 내부 매물 ID | ★★★ | 자체 발번 |
| `registration_no` | 차량등록번호 | ★★ | 말소등록 시 사용 |
| `registration_date` | 최초등록일 | ★★★ | 케냐·탄자니아 등은 "**최초등록일** 기준 8년"으로 연식 제한 (제조연도 X) |
| `manufacture_date` | 제조연월 | ★★★ | 일부 국가는 제조연도 기준 (나이지리아 등) |

### 2.2 차량 기본 사양 (Specifications)

| 필드 | 한글명 | 비고 |
|------|--------|------|
| `make` | 제조사 | Hyundai, Kia, Genesis, Ssangyong 등 |
| `model` | 모델명 | Sonata, Sportage, Mohave 등 |
| `trim` / `grade` | 트림/등급 | "2.0 Premium" 같이 옵션 패키지명 |
| `year` | 연식 (모델이어) | 검색 필터의 1차 축 |
| `body_type` | 차종 | Sedan, SUV, Pickup, Van, Bus, Truck — SUV·픽업이 신흥국에서 강세 |
| `fuel_type` | 연료 | Gasoline, Diesel, LPG, Hybrid, EV — 아프리카는 디젤 수요 큼, 러시아 수출은 EV 금지 |
| `engine_displacement` | 배기량 (cc) | **러시아: 2,000cc 초과 내연기관 수출금지** / **카자흐스탄·키르기스스탄 우회**도 모니터링 대상 |
| `transmission` | 변속기 | A/T, M/T |
| `drivetrain` | 구동방식 | FWD, RWD, AWD, 4WD |
| `steering` | 핸들 위치 | **LHD / RHD** — 케냐·탄자니아·우간다·남아공·인도네시아·태국 등은 RHD만 허용. 가나·세네갈·나이지리아·코트디부아르는 LHD만. |
| `seats` | 좌석 수 | 5/7/9/15… 화물승합 분류에 영향 |
| `color_exterior` / `color_interior` | 외장/내장색 | |
| `mileage_km` | 주행거리 | 검색 필터 핵심. UN/UNEP는 "5,000km 초과 = 중고" 기준. |
| `vin_decoded` | VIN 디코딩 결과 | NHTSA vPIC API로 자동 채움 가능 (무료, 1981년 이후 차량) |

### 2.3 상태 정보 (Condition)

| 필드 | 한글명 | 비고 |
|------|--------|------|
| `accident_history` | 사고이력 | 한국은 **자동차관리법 제58조**상 매매업자 고지의무. 보험개발원 카히스토리 연동 가능. |
| `insurance_history` | 보험처리이력 | 카히스토리 (https://www.carhistory.or.kr) |
| `inspection_record` | 성능·상태점검기록부 | 자동차365 (https://www.car365.go.kr) — 국토부·교통안전공단이 통합 관리 |
| `auction_grade` | 경매 등급 | 일본식 4.5 / 4 / 3.5 / R / RA — SBT/BeForward 표준. 한국 옥션 등급도 매핑 필요 |
| `repair_history` | 수리이력 | 외판 교환·판금·용접·손상·부식 부위별 |
| `panel_status_json` | 외판 상태 (JSON) | 후드/펜더/도어/트렁크 등 부위별 상태 코드 |
| `tire_condition` | 타이어 상태 | Front/Rear 마모도 |
| `interior_condition` | 실내 상태 | 시트 손상, 냄새, 스마트키 유무 |
| `option_list` | 옵션 (JSON) | 선루프, 가죽시트, 내비, 후방카메라, ADAS 등 |
| `recall_status` | 리콜 대상 여부 | 자동차365 리콜대상확인 연동 |

### 2.4 가격·재고 정보 (Pricing & Inventory)

| 필드 | 한글명 | 비고 |
|------|--------|------|
| `purchase_price_krw` | 매입가 (원) | 내부 마진 계산용 |
| `list_price_usd` | 표시가 (USD) | 글로벌 표준은 USD. CIF/FOB 구분 필요 |
| `incoterm` | 인코텀즈 | FOB / CIF / CFR / EXW. 동남아·아프리카는 **CIF가 주류** |
| `currency` | 통화 | USD 디폴트, 일부 EUR/GBP 옵션 |
| `negotiable` | 가격협상 여부 | |
| `stock_status` | 재고상태 | available / reserved / sold / shipping / delivered |
| `location` | 차량 보관지 | 인천 송도, 평택 등 — 보세구역 반입 추적 |
| `port_of_loading` | 선적항 | 인천(IIN), 평택(KPT), 부산(KPS) — 인천이 1위, 부산이 2위 |

### 2.5 이미지·미디어

| 필드 | 비고 |
|------|------|
| `images[]` | 외관 4면 / 실내 / 엔진룸 / 트렁크 / 계기판 / 옵션 디테일 — **최소 20장 권장** (BeForward 평균 30~50장) |
| `video_url` | 워크어라운드 영상 — 엔진 시동, 주행 — 최근 신뢰성 향상 핵심 수단 |
| `inspection_pdf` | 성능점검기록부 PDF |
| `auction_sheet_pdf` | 경매 시트 PDF |

---

## 3. 수출 서류 정보 (Export Documents)

한국 자동차관리법 + 관세법 + 일반 무역실무 기준. **AI 에이전트가 자동 생성해야 할 서류 5종**으로 정리.

### 3.1 한국 측 수출 프로세스 (법적 흐름)

```
① 차량 매입 (개인/딜러)
   ↓
② 자동차 등록 말소
   - 자동차관리법 제13조
   - 시·도지사(차량등록사업소)에 신청
   - 자동차등록증, 등록번호판, 봉인 반납
   - "수출예정말소"는 6개월 이내 신청 (경과 시 과태료 30만원)
   ↓
③ 상품화 (수리/세차/광택/판금)
   ↓
④ 보세구역 반입
   - 관세법 제243조 4항 + 관세청 고시
   - 2017년 4월부터 컨테이너 적입 중고차는 보세구역 반입 후 신고 의무
   ↓
⑤ 세관 수출신고 (관세사 EDI)
   - 필수서류: 인보이스, 패킹리스트(차대번호 표기), 자동차말소등록사실증명서,
              차대번호 및 쇼링 전후 전자이미지, 보세구역 반입계
   ↓
⑥ 통관 심사 (도난·말소 여부 전산 검증)
   ↓
⑦ 수출신고 수리 → 수출신고필증 교부
   ↓
⑧ 30일 이내 선적 (최대 1년 연장 가능)
   ↓
⑨ B/L 발급 → 도착지 통관 → 등록
```

### 3.2 자동 생성 대상 서류 5종

#### (1) Commercial Invoice (상업송장)

| 필드 | 비고 |
|------|------|
| Invoice No. | 자동 발번 |
| Invoice Date | |
| Seller (Shipper) | 회사명, 주소, 사업자번호, 연락처 |
| Buyer (Consignee) | 회사명/개인명, 주소, 연락처, **Tax ID** (현지국 요구 시) |
| Notify Party | 통관/배송 알림 대상 |
| Vessel / Voyage No. | |
| Port of Loading / Discharge | |
| Final Destination | |
| Incoterms | FOB / CIF / CFR |
| Payment Terms | T/T, L/C, D/P, D/A |
| Currency | |
| Vehicle Description | Make, Model, Year, VIN, Color, Mileage, Engine cc |
| Unit Price | |
| Total Amount | 숫자 + 영문 표기 ("USD ELEVEN THOUSAND…") |
| HS Code | **8703.xx** (승용차) / **8704.xx** (화물자동차) |
| Country of Origin | "Republic of Korea" |
| Bank Info | 송금 계좌 (수취인 명의, SWIFT, IBAN) |
| Signature | 발행자 서명/도장 이미지 |

#### (2) Packing List (포장명세서)

| 필드 | 비고 |
|------|------|
| Same header as Invoice | |
| Container No. | RoRo는 N/A, 컨테이너 운송은 필수 |
| Seal No. | 컨테이너 봉인번호 |
| Marks & Numbers | 컨테이너 마킹 |
| **VIN (차대번호)** | 차량별 1행 — 세관 핵심 검증 키 |
| Net Weight (kg) | 차량 공차중량 |
| Gross Weight (kg) | 적재 후 총중량 |
| Measurement (CBM) | 컨테이너 적용 시 |
| No. of Packages | 차량 대수 |

#### (3) Bill of Lading (B/L, 선하증권)

선사가 발행. AI 에이전트는 직접 발행은 못 하지만 **선사 제출용 SI(Shipping Instruction)을 자동 생성**할 수 있음.

| 필드 | 비고 |
|------|------|
| Shipper | 수출자 |
| Consignee | "TO ORDER" / 지정 / "TO ORDER OF [BANK]" (L/C 거래 시) |
| Notify Party | |
| Vessel / Voyage | |
| Port of Loading / Discharge / Destination | |
| Description of Goods | "USED MOTOR VEHICLE - HYUNDAI SONATA 2018 VIN: KMHE...A123456" |
| Gross Weight, Measurement | |
| Freight | "Prepaid" / "Collect" |
| B/L No. | 선사 발번 |

#### (4) Certificate of Origin (원산지증명서)

- **상공회의소** 발급 (대한상공회의소 무역인증서비스 https://cert.korcham.net)
- 일반 C/O와 FTA C/O로 구분. **한-아세안 FTA**, **한-인도 CEPA** 등 활용 가능.
- 동남아·아프리카에서 관세 우대 받으려면 FTA C/O 필수.

#### (5) Export Declaration / 수출신고필증 (KCS 발급)

- 관세사가 EDI로 신고하고, 수리되면 PDF로 발급.
- AI는 직접 발급 불가하지만 **신고 항목 데이터를 관세사에게 자동 송부하는 패키지** 생성 가능.

### 3.3 (선택) 추가 서류

| 서류 | 언제 필요? |
|------|----------|
| Cancellation of Registration / 자동차말소등록사실증명서 | **항상 필요** — 수출신고 필수 첨부 |
| Inspection Certificate (JEVIC/Intertek) | 케냐·우간다·탄자니아·모잠비크 등은 **선적 전 검사** 필수 |
| Roadworthiness Certificate | 일부 국가 |
| Emission Compliance Certificate | UN/UNEP 환경기준 강화 흐름 — 향후 필수화 가능성 큼 |
| Marine Insurance Policy | CIF 거래 시 |
| Letter of Credit | L/C 결제 시 — 은행 발급 |

---

## 4. 바이어 정보 (Buyer Data)

해외 바이어 매칭과 다국어 커뮤니케이션을 위한 데이터 모델.

### 4.1 바이어 프로필 필드

| 필드 | 한글명 | 비고 |
|------|--------|------|
| `buyer_id` | 내부 ID | |
| `buyer_type` | 유형 | Dealer / Importer / Individual / Re-exporter |
| `company_name` | 회사명 | |
| `contact_person` | 담당자명 | |
| `country_code` | 국가코드 | ISO 3166-1 (KE, NG, TZ, VN…) |
| `country_name_local` | 현지어 국가명 | 다국어 메일 발송용 |
| `city` | 도시 | |
| `address` | 주소 | 영문 표기 + 현지어 표기 |
| `phone` | 전화 | 국가코드 포함 |
| `whatsapp` | WhatsApp | **아프리카·동남아 1순위 채널** |
| `email` | 이메일 | |
| `wechat` | WeChat ID | 중국계 바이어 (재수출 거점) |
| `business_license` | 사업자등록번호 | 현지 형식 |
| `tax_id` | TIN (세금번호) | 현지 통관 시 필요 |
| `preferred_language` | 선호 언어 | en, ru, ar, fr, vi, sw, am … |
| `preferred_currency` | 선호 통화 | USD 디폴트 |
| `preferred_payment` | 결제방식 | T/T, L/C, D/P, Western Union, 가상자산 (일부 아프리카) |
| `preferred_port` | 선호 도착항 | Mombasa, Dar es Salaam, Lagos, Tema, Cotonou, Haiphong… |
| `preferred_incoterm` | 선호 인코텀즈 | 보통 CIF |
| `target_models[]` | 관심 모델 | "현대 그랜드 스타렉스", "기아 봉고3" 등 |
| `target_year_range` | 희망 연식 | 케냐는 2019↑ 강제 |
| `target_price_range_usd` | 희망 가격대 | |
| `target_mileage_max_km` | 희망 주행거리 상한 | |
| `volume_per_month` | 월 거래량 | 1대 / 5~10대 / 컨테이너 단위 / 벌크 |

### 4.2 거래 이력 필드

| 필드 | 비고 |
|------|------|
| `total_orders` | 누적 주문 |
| `total_value_usd` | 누적 거래액 |
| `last_order_date` | |
| `payment_reliability_score` | 결제 신뢰도 (0~100) — T/T 100% 선결제는 100, L/C 정상결제는 90… 분쟁 발생 시 감점 |
| `dispute_count` | 분쟁 이력 수 |
| `kyc_verified` | KYC 인증 여부 |
| `sanctions_check_date` | **제재 대상 여부 확인일** — Yestrade(전략물자관리시스템) 우려거래자 조회 |

### 4.3 신뢰성·법적 검증 (Compliance)

이게 중요. 단순 CRM이 아니라 **수출통제 컴플라이언스 모듈**이 들어가야 함.

- **Yestrade 우려거래자 조회** (전략물자관리원) — 거래 전 필수 체크
- **상황허가 대상 여부** — 「전략물자 수출입고시」 별표 2의2
- **러시아·벨라루스 우회 모니터링** — 키르기스스탄·카자흐스탄·아르메니아 바이어가 의심정황 있을 시 자동 플래그
- **OFAC SDN List** — 미국 제재 명단 크로스체크 (한국 기업도 영향받음)

---

## 5. 타겟국 수입규제 매트릭스 (동남아·아프리카)

AI 에이전트의 **국가별 룰 엔진** 베이스라인. 여기 적힌 건 자주 바뀌므로 **분기마다 갱신**해야 함.

### 5.1 아프리카

| 국가 | 연식 제한 | 핸들 | 항구 | 기타 |
|------|----------|------|------|------|
| **케냐** 🇰🇪 | **8년 (2026.1.1~ 2019년식 이후만 허용)** | RHD only | Mombasa | KEBS 인증, **선적 전 JEVIC/QISJ 검사 필수**. 관세 25% + 소비세 20% + VAT 16% (총 60%↑) |
| **탄자니아** 🇹🇿 | 8년 (개인차) | RHD | Dar es Salaam | 8년 초과 시 추가 소비세 |
| **우간다** 🇺🇬 | **연식 제한 없음** (15년 제안 중) | RHD | Mombasa/Dar 경유 | 5년 초과 환경부담금. 관세 비교적 낮음 |
| **나이지리아** 🇳🇬 | **15년 (사실상 10년 권장)**, 정부 권장 2015년식 이후 | LHD | Lagos (Apapa, Tin Can) | 관세+부가세+레비 35~70%. SON 인증 면제 (전기전자만 의무) |
| **가나** 🇬🇭 | 10년 초과 시 추징금 | LHD | Tema | 선적 전 검사 필수 |
| **리비아** 🇱🇾 | 완화적 | LHD | Misrata, Benghazi | 북아프리카 재수출 거점. 저가 위주. **2024년 한국 수출 1위 (12.1만대)** |
| **세네갈** 🇸🇳 | 8년 | LHD | Dakar | |
| **에티오피아** 🇪🇹 | 까다로움 (사실상 5년) | LHD | Djibouti 경유 | 관세·세금 매우 높음 |
| **남아공** 🇿🇦 | 신차만 허용 (중고 수입 사실상 금지) | RHD | Durban | 환승/재수출 허브로 활용 |
| **모잠비크** 🇲🇿 | 5년 (개인) | LHD | Maputo, Beira | INTERTEK 검사 필수 |
| **DR콩고** 🇨🇩 | 완화적 | LHD | Matadi | 컨테이너 운송, 운임 비쌈 |

> 📌 **ECOWAS 15개국**(서아프리카경제공동체)은 2021년부터 공동 차량·연료 기준 도입 합의 — 환경기준 점진 강화 흐름. 동남아·아프리카 통틀어 **EU 기준 추종**이 일반적.

### 5.2 동남아

| 국가 | 연식 제한 | 핸들 | 비고 |
|------|----------|------|------|
| **베트남** 🇻🇳 | 5년 | RHD/LHD 혼재 (일부 LHD) | 점진 자유화. 한국·일본산 인바운드 증가. |
| **필리핀** 🇵🇭 | 사실상 수입 어려움 (수빅경제특구 제외) | LHD | 일반 통관 매우 까다로움 |
| **인도네시아** 🇮🇩 | 신차 위주 | RHD | 자국 산업 보호. 중고 수입 제한 강함 |
| **태국** 🇹🇭 | 사실상 금지 | RHD | 자국 신차 산업 보호. RHD 허브로 재수출 가능성 |
| **말레이시아** 🇲🇾 | AP 라이선스 필요 | RHD | 진입장벽 매우 높음 |
| **캄보디아** 🇰🇭 | 완화적 | RHD/LHD | 관세 높지만 진입 자유. 일본 중고차 강세 시장 |
| **미얀마** 🇲🇲 | 정치불안 | RHD (최근 LHD 전환 중) | 거래 리스크 큼 |
| **싱가포르** 🇸🇬 | 3년 (사실상 시장성 없음) | RHD | COE 입찰제로 비현실적 |

### 5.3 룰 엔진 설계 시 핵심 규칙 5가지

1. **연식 계산 기준이 국가마다 다름** — "최초등록일" 기준 / "제조연도" 기준 / "선적일" 기준이 섞여있음. 반드시 국가별 메타데이터로 분리.
2. **RHD/LHD는 단일 필터** — 차량 핸들 위치 vs 국가 요구사항 불일치 시 자동 차단.
3. **배기량 상한** — 러시아·EU 일부는 배기량 제한. EV 수출은 러시아 금지 등 별도 룰.
4. **HS Code 분기** — 8703 (승용) / 8704 (화물) / 8702 (10인 이상 승합) / 8711 (이륜) — 관세율 완전히 다름.
5. **선적 전 검사 의무국가** — 케냐(JEVIC/QISJ), 탄자니아(JEVIC), 우간다(JEVIC), 모잠비크(Intertek), 나이지리아(SONCAP), 케냐(KEBS). 자동 알림 필수.

---

## 6. 벤치마킹 5분 정리

### 6.1 BeForward (일본)

- 글로벌 1위. **재고 40만+대** 상시 노출. 200개국 수출.
- 핵심 강점: 검색 필터의 정밀도(연료/배기량/연식/주행/등급/색/가격), **30개 언어 지원**, 사진 30~50장 + 동영상.
- "BF Points" 마일리지 (1pt = 1 USD).
- **WhatsApp 영업** 중심.

### 6.2 SBT Japan

- 옥션 등급 표시 강함 (3.5↑ 권장). 검사시트 PDF 공개.
- VIN/사고이력 검증 강조.
- 다국가 결제 옵션 (각 도착국 현지은행 연동).

### 6.3 차별화 포인트 (우리 에이전트가 가야 할 방향)

BeForward·SBT가 못 하는 것:

1. **수출 서류 자동 생성** — 그들은 마켓플레이스. 우리는 **에이전트**. 인보이스/패킹리스트/SI를 LLM이 자동 작성.
2. **다국어 메일 자동 작성·발송** — 영어 단일 채널이 아니라 스와힐리어, 암하라어, 베트남어, 프랑스어(서아프리카)까지.
3. **국가별 룰 자동 적용** — 검색 결과를 바이어 국가에 맞춰 사전 필터링 ("이 차는 케냐 통관 불가, 우간다는 OK").
4. **시세 자동 산정** — 엔카·카히스토리·옥션 데이터 + 도착지 평균가 매핑.
5. **컴플라이언스 모듈** — Yestrade·OFAC 자동 조회.

---

## 7. 법적 제약 체크리스트

캡스톤 결과물로 발표하려면 반드시 통과해야 하는 항목들.

### 7.1 한국 측 (수출자 입장)

- [x] **자동차관리법 제13조** — 말소등록 후 수출
- [x] **관세법 제241조 / 제243조** — 수출신고 + 보세구역 반입 (컨테이너의 경우)
- [x] **대외무역법** — 전략물자 자가판정 (배기량 2000cc 초과 + 우려거래자)
- [x] **「전략물자 수출입고시」 별표 2의2** — 상황허가 대상품목
- [x] **부가가치세법** — 수출 영세율, 의제매입세액공제
- [x] **개인정보보호법** — 한국 매도인의 이름/주민번호 등 보호. 차대번호는 차량 정보지만 등록자와 결합 시 개인정보 가능성

### 7.2 데이터·플랫폼 측 (이게 톡방에서 논란된 부분)

- [ ] **저작권법** — 타 플랫폼 HTML/CSS/이미지/카피라이팅 무단 복제 금지
- [ ] **정보통신망법 제48조** — 정당한 접근권한 없는 정보통신망 침입 금지 (**IP 우회 접속 리스크**)
- [ ] **부정경쟁방지법 제2조 제1호** — 타인의 상당한 투자·노력으로 만들어진 성과물 무단 사용 금지 ("성과물 도용" 조항, 2018 신설)
- [ ] **이용약관 위반** — 대부분 플랫폼이 자동수집·역공학 금지 명시

> ⚠️ **결론:** 오토벨 글로벌·롯데 플랫폼의 **UI/UX 분석은 공개 자료(보도, 캡처, 인터뷰) 범위 내에서만**. 직접 접속·다운로드·복제 금지.

### 7.3 도착국 측 (수입국 컴플라이언스)

- [ ] 연식 제한
- [ ] 핸들 위치
- [ ] 배기가스 기준
- [ ] 선적 전 검사 (JEVIC, Intertek, SONCAP, KEBS 등)
- [ ] HS Code 정확성
- [ ] 원산지증명 (FTA 활용 시)
- [ ] 제재 대상 우회 여부

---

## 8. 데이터 소스 추천 (LLM Wiki 시드 데이터)

캡스톤 초기 LLM Wiki 구축에 쓸 1차 자료 후보.

### 8.1 한국 측

| 소스 | URL | 용도 |
|------|-----|------|
| 한국무역협회 K-stat | https://stat.kita.net | 수출통계 (HS코드, 국가별) |
| 관세청 UNI-PASS | https://unipass.customs.go.kr | 수출신고 가이드 |
| 자동차365 | https://www.car365.go.kr | 차량 통합이력 |
| 보험개발원 카히스토리 | https://www.carhistory.or.kr | 사고이력 |
| 산업연구원 (KIET) Issue Paper 2024-13 | (이미 인용) | 수출시장 정책 시사점 |
| KOTRA 해외시장뉴스 | https://dream.kotra.or.kr | 국가별 시장동향 |
| 한국중고차수출조합 (KUCEA) | http://kucea.or.kr | 업계 통계 |
| 한국자동차산업협동조합 | https://www.kaica.or.kr | 산업 전망 |
| 산업통상자원부 무역안보정책관 | | 전략물자 / 상황허가 |
| Yestrade (전략물자관리원) | https://www.yestrade.go.kr | 우려거래자 조회 |

### 8.2 글로벌

| 소스 | URL | 용도 |
|------|-----|------|
| NHTSA vPIC API | https://vpic.nhtsa.dot.gov/api | VIN 디코딩 (무료) |
| UNEP Used Vehicle Report | (UN Environment) | 글로벌 규제 흐름 |
| BeForward | https://www.beforward.jp | 벤치마킹 (UI 패턴, 필터 구조) |
| SBT Japan | https://www.sbtjapan.com | 벤치마킹 (등급 시스템) |
| CardealPage 국가별 규제 | https://www.cardealpage.com/regulation.html | 국가별 연식·핸들·항구 |
| OFAC SDN List | https://sanctionssearch.ofac.treas.gov | 제재 대상 조회 |

---

## 9. 다음 단계 권장 사항

1. **데이터 모델 ERD 설계** — 본 리포트의 §2/3/4 필드를 기반으로 ER 다이어그램 작성. PostgreSQL + JSON 컬럼 추천.
2. **국가별 룰 엔진 YAML 작성** — §5의 표를 룰 파일로 (예: `kenya.yaml: { age_limit: 8, age_basis: "first_registration", steering: "RHD", required_inspection: "JEVIC" }`).
3. **MVP 범위 정의** — 처음부터 13개국 다 하지 말고 **케냐 1개국**으로 좁혀 PoC. 케냐가 RHD·연식제한·검사의무 다 있어서 룰 엔진 검증에 좋음.
4. **샘플 서류 5종 구하기** — 하이쓰리디 측에 인보이스/패킹리스트/SI/C/O/수출신고필증 실제 샘플 5세트 요청. LLM 파인튜닝/few-shot 기반 자료.
5. **VIN 디코딩 우선 통합** — NHTSA vPIC API로 차량 사양 자동 채움 → 데이터 입력 부담 즉시 절감. 첫 번째 quick win.
6. **다국어 메일 템플릿 시드** — 영어 / 프랑스어(서아프리카) / 러시아어(중앙아시아) / 아랍어(북아프리카) / 베트남어 / 스와힐리어 우선. 각 5개 시나리오(인사/견적/협상/선적안내/분쟁대응).
7. **컴플라이언스 모듈 사전 설계** — Yestrade 조회 자동화는 산업체 멘토 통해 API 가능 여부 확인.

---

## 부록 A. HS Code 빠른 참조

| HS Code | 분류 |
|---------|------|
| 8703.21 | 승용차 1,000cc 이하 가솔린 |
| 8703.22 | 승용차 1,000~1,500cc 가솔린 |
| 8703.23 | 승용차 1,500~3,000cc 가솔린 (**한국 수출 주력**) |
| 8703.24 | 승용차 3,000cc 초과 가솔린 |
| 8703.31 | 승용차 1,500cc 이하 디젤 |
| 8703.32 | 승용차 1,500~2,500cc 디젤 (**아프리카 수요 큼**) |
| 8703.33 | 승용차 2,500cc 초과 디젤 |
| 8703.80 | 전기차 (EV) |
| 8704.21 | 화물차 5톤 이하 디젤 |
| 8704.31 | 화물차 5톤 이하 가솔린 |
| 8702.10 | 승합차 10인 이상 디젤 |
| 8711.x  | 이륜자동차 |

---

## 부록 B. 약어 사전

- **B/L** Bill of Lading (선하증권)
- **C/O** Certificate of Origin (원산지증명)
- **CIF** Cost, Insurance and Freight
- **FOB** Free on Board
- **HS Code** Harmonized System Code (관세품목분류)
- **JEVIC** Japan Export Vehicle Inspection Center (선적 전 검사 인증기관)
- **KEBS** Kenya Bureau of Standards
- **KCS** Korea Customs Service (관세청)
- **L/C** Letter of Credit (신용장)
- **LHD/RHD** Left/Right Hand Drive
- **PSI** Pre-Shipment Inspection
- **RoRo** Roll-on/Roll-off (자동차 전용 선박)
- **SI** Shipping Instruction
- **SONCAP** Standards Organisation of Nigeria Conformity Assessment Programme
- **T/T** Telegraphic Transfer (전신환 송금)
- **VIN** Vehicle Identification Number (차대번호)

---

*리포트 끝.*
