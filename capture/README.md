# 벤치마크 캡쳐 — Autobell Global (현대글로비스 / Autowini)

> URL: https://www.autobellglobal.com/
> 캡쳐일: 2026-05-10
> 비교 대상: 우리 `/marketplace/*` (벤치마크 미러 UI)

이 폴더의 7장은 **Autobell Global** (Hyundai GLOVIS 의 글로벌 중고차 수출 브랜드) 의
B2B 마켓플레이스 화면. 우리 React 마켓플레이스(`frontend/src/pages/marketplace/*`)
의 디자인 결정 검증 및 추가 개선 후크 도출용.

---

## 파일별 화면

### 01 · `01-landing-hero.png` — 랜딩 히어로

- **상단 네비**: GLOVIS 로고 + Autowini 로고 동시 노출 / Used Car · Howto Autowini · About Autobell / 우측 May 10 15:30 KST · Log in · 한국어 · English · Whatsapp
- **히어로 캐러셀**: 좌중간 "Launching Autobell Global Warranty Service" 텍스트 + 큰 백그라운드 이미지 / 우측 작은 "Ready to Ship? Discover Glovis's" 배너 + "View More" CTA
- **카운트 배지 + 검색바**: "**28,194** vehicles Registered" (밑줄·hover 클릭 가능 강조) → 그 아래 단일 검색 입력창 "Search by Brand, Model, Item No"
- **키워드 칩**: Autobell Stock · Warranty Available · SUV+Gasoline · Affordable Price · Sunroof
- **추천 섹션**: "Special used cars **available only at Autobell Global**" + 좌 사이드 탭 (Autobell Stock / Condition Reported / Autobell X-K Car / View Details)

**우리와 비교**: 우리 히어로도 검색바 + 키워드 칩 있음. 차이는 (1) 우리는 vehicle count 배지 강조 약함 (2) 추천 섹션의 **좌측 사이드 탭** 구조가 우리는 없음 (3) "warranty service" 같은 마케팅 메시지 carousel 이 우리는 단일 정적 슬라이드.

### 02 · `02-landing-special-cars-about.png` — 랜딩 스크롤 다운

- 추천 카드 (Tucson Diesel R20 2WD / Bongo Countryman 2.0 SE / Trax 1.4 Turbo) — **국기 + 가격 (FOB Korea)** 표기
- 카드 디자인: 좌측 차종명·연식 / 우측 큰 사진 / 하단 가격 + Add-to-favorite 별
- **About 섹션**: 큰 통계 4개 — `50%` (?) / `1.5 Million` / `2,100+` / `10,000` 와 "The Heart of Used Cars" 카피. 신뢰감 confer.

**우리와 비교**: 우리 추천 카드는 4:3 비율 가운데 사진. **Autobell 카드는 가로 긴 비율 + 좌우 분할 (정보 + 사진)** 으로 정보 밀도 ↑. About 섹션은 우리에 없음 — 추가 후크 (큰 숫자 = 마케팅 신뢰감).

### 03 · `03-nav-megamenu.png` — 메가 네비게이션

- **5 카테고리** 가로 펼침: Used Car / Howto Autowini / Buyer Certification / Used Car Transportation / Payment Service
- 각 카테고리 아래 5~7개 sub-link
- 우측 끝에 **달력 위젯** "Subastas y Festivos / Calendario" (스페인어!) — **글로벌 다언어 인지** 신호
- 메가메뉴 펼침 동안 본문은 **회색 오버레이 + 흐림** 처리

**우리와 비교**: 우리 네비는 단순 horizontal links + dropdown 없음. 글로벌 마켓플레이스 다음다음 sprint 에서 메가메뉴 + 다국어 진짜 구현 가치 있음.

### 04 · `04-vehicle-detail-main.png` — 차량 상세 (메인 이미지)

- 좌상단 breadcrumb: 2015 · CHEVROLET(DAEWOO) · "Captiva Diesel 2.0 2WD"
- **메인 사진** : 큰 이미지 (KB차차차 워터마크 — 거래 중개 표시)
- **하단 썸네일 row** (8장 정도) — 각 다른 각도
- 사진 아래 4 spec 박스: Mileage 188,343 km / Diesel / 1,998 cc / [empty]
- **우측 sticky 패널**:
  - 차량 카드 (사진 + 모델명)
  - Country of Origin: Republic of Korea
  - Buyer: (드롭다운)
  - FOB: (Incoterm 선택)
  - **KB**: (KB차차차 거래 표시)
  - **Price Info**: Vehicle 가격 / Shipping cost / Total Price (FOB)
  - **`Inquiry`** + **`Buy`** 버튼 (파란색 강조)
- 페이지 하단 4 탭: Features / Information / Condition Report / Car History

**우리와 비교**: 우리 `/marketplace/{id}` 도 좌 메인+썸네일 / 우 sticky 패널 구조. 차이:
- 우리는 **`Request Quote` + `WhatsApp`** CTA → Autobell 은 **`Inquiry` + `Buy`** (구매 명시적 — B2B 플로우 다름)
- 우리는 가격 한 줄 → Autobell 은 **Vehicle + Shipping + Total 분리** (CIF 자동 계산 시각화)
- KB차차차 같은 **3rd party 보증 마크** 우리에 없음

### 05 · `05-vehicle-detail-features-tab.png` — Features 탭

- 좌측에 옵션 큰 아이콘 (8개): Power(?) / Fully Automatic / 4 cyl / Wood Trim 등
- **3 카테고리 옵션 체크리스트**: Exterior / Interior / Safety
- 각 ~10~15개 항목 ✓ 표시 (Aluminum Wheel / Roof Rack / Leather Seats / ABS / Airbag 등)

**우리와 비교**: 우리 차량 상세는 spec 표에 다 합쳐서 표시. **카테고리별 체크리스트** 가 Autobell 식. Day 4+ 바이어 카탈로그 모드면 추가 가치 있음.

### 06 · `06-vehicle-detail-information-tab.png` — Information 탭

- 차량 사양 2-column 표:
  - VIN / KLAGN26GMD8(masked)
  - Mileage 188,343 km
  - Year 2015
  - First Registration Date 2015-12-30
  - Make / Model
  - Engine 1,998 cc
  - Fuel Diesel
  - Country of Origin Republic of Korea
  - Auction etc.
- 하단 **Performance Inspection Record** 섹션 — 차량 도식 + "Verified condition across categories" + Transparent for buyer confidence

**우리와 비교**: 우리도 spec 표 있음 — 비슷. **Performance Inspection 차량 도식** 은 우리에 없음 — Autobell 식 신뢰 차별화 포인트.

### 07 · `07-vehicle-detail-history-tab.png` — Car History 탭

- **3 카테고리 신뢰 표시**:
  - Specific Auto Insurance Accident Record: ✓ No Record
  - Special Usage: ✓ No Record
  - **Transfer of Ownership: 1 Record** ⚠️
- 하단 **"Similar vehicles for sale"** carousel — 4 카드 (Captiva 시리즈) — Cross-sell

**우리와 비교**: 우리 차량 상세에 **사고 이력 / 명의 이전** 표시 없음. PoC 백엔드는 카히스토리 stub 만 있고. 이거는 시연 시나리오 자체에 있는 항목 (`docs/used_car_export_research_v2.md` §2.3) — 시간되면 채울 수 있음.

---

## 우리 `/marketplace/*` 와 비교 — 정리

| 영역 | Autobell Global | 우리 `/marketplace` | 차이 / 액션 후보 |
|---|---|---|---|
| 상단 네비 | 가로 + **메가메뉴 dropdown** | 가로 + 모바일 햄버거 placeholder | 메가메뉴 다음 sprint OK |
| 다국어 | 한/영 + 지역 캘린더 (스페인어) | 한/영 비활성 셀렉터 | i18n Phase 2 |
| 히어로 | 캐러셀 + 검색 + 키워드 칩 | 정적 + 검색 + 키워드 칩 | 캐러셀화 가치 낮음 (PoC) |
| Vehicle count 배지 | "28,194 vehicles Registered" 큰 클릭 | (없음) | 추가 가능 (count API 있음) |
| 추천 섹션 | 좌 사이드 탭 + 카드 carousel | 4 카드 grid | 사이드 탭 다음 iteration |
| 카드 디자인 | 좌우 분할 (정보 + 사진) | 위아래 (사진 + 정보) | **현재가 모바일 친화적** — 유지 |
| About 섹션 (통계) | 큰 숫자 4개 신뢰 | (없음) | **추가 가치** ↑↑ — 발표 임팩트 |
| 차량 상세 메인 | 메인 + 썸네일 + sticky 패널 | 메인 + 썸네일 (같은 사진 6번) + sticky | ✅ 비슷 |
| 가격 표시 | Vehicle + Shipping + Total 분리 | "FOB Incheon" 단일 | **분리 표시 추가** — Day 4+ |
| 4 탭 | Features / Info / Condition / History | (탭 없음, 한 화면) | 탭화 가치 ↑ |
| 신뢰 마크 | KB차차차 / Inspection record / 사고 이력 | 112-Point Inspection mock 만 | 사고 이력 stub 추가 가능 |
| CTA | `Inquiry` + `Buy` | `Request Quote` + `WhatsApp` | 우리가 더 PoC 적절 |
| 하단 추천 | "Similar vehicles for sale" carousel | (없음) | 추가 가능 (cross-sell) |

---

## 우리 `/marketplace` 다음 iteration 우선순위 (Autobell 격차 기반)

1. **About 섹션 통계 카드** — 큰 숫자 4개 (28k vehicles · 100+ countries · 5,000 sellers · etc.). 발표 임팩트 큼. ~30분.
2. **차량 상세 4 탭** (Features / Info / Inspection / History) — 정보 밀도 ↑. ~1시간.
3. **차량 상세 가격 분리** (Vehicle + Shipping + Total CIF) — B2B 정보. ~20분.
4. **하단 "Similar vehicles" carousel** — 차량 상세 페이지 cross-sell. ~30분.
5. **Vehicle count 배지** (28,194 같은 trust signal) — 5분.

→ 1+3+5 합치면 ~1시간으로 큰 시각 차이 메울 수 있음.

---

## 사용 (캡쳐 추가/갱신 시)

```
# 새 캡쳐 추가
1. 브라우저로 비교할 화면 캡쳐 (Win+Shift+S)
2. capture/ 폴더에 저장
3. 본 README 에 항목 추가
4. git add capture/ && git commit -m "docs: add benchmark capture <name>"
```
