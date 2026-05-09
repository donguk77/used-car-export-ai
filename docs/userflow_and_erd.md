# 중고차 수출 AI 에이전트 — User Flow & ERD 설계

> **목적:** 빌드 시작 전, 사용자 흐름과 데이터 모델 동시 정의
> **작성일:** 2026.05.09
> **선행 자료:** 시장 v2, 20개국 가이드, 경쟁사 분석
> **다음 단계:** 백엔드 API 설계 → Figma 디자인 → 구현

---

## Part 1. User Flow

### 1.1 페르소나 — 누가 쓰는가

#### 🧑 Primary 페르소나: 김수출 사장님
- **나이/배경:** 40대 후반, 인천 송도 중고차 수출업체 대표 (1인 + 직원 1~2명)
- **사업 규모:** 월 30~50대 수출, 연 매출 30~50억
- **현재 사용 도구:** 오토위니(매물 등록), WhatsApp(영업), 엑셀(재고 관리), 카카오톡(국내 매입)
- **고통 (Pain Point):**
  - 영어는 서툴고 아랍어/스페인어/러시아어는 전혀 못 함 → **번역기 돌려가며 응대**
  - 케냐 룰 바뀐 거 한참 뒤에 알아서 컨테이너 묶인 적 있음 → **규제 추적 안 됨**
  - 인보이스/패킹리스트 매번 양식 복붙해서 작성 → **시간 잡아먹음**
  - 키르기스스탄 바이어가 위장한 러시아 우회수출 권유 받았는데 **기준이 모호**
  - 결제 후 도착 전까지 바이어가 매일 "내 차 어디 있어?" 카톡 → **지치고 시차 때문에 새벽까지**
- **목표:** 같은 시간에 더 많은 거래, 분쟁 없이, 안 잡혀가게

#### 👨 Secondary 페르소나: 박바이어 (해외 바이어, AI에이전트는 직접 안 쓰지만 응대 받음)
- **나이/배경:** 도미니카공화국 산토도밍고, 30대 자동차 딜러
- **사용 채널:** WhatsApp 위주, 가끔 이메일
- **언어:** 스페인어, 영어 일부
- **고통:**
  - 한국 셀러 영어 답변이 어색하고 자정 넘어 답옴
  - "내 차 도착 언제?" 같은 단순 질문에도 며칠 걸림
  - 차량이 도미니카 통관에 맞는지 미리 확인하기 어려움

#### 👤 Tertiary 페르소나: 이대표 (하이쓰리디·산학캡스톤 멘토 측)
- 캡스톤 결과물을 평가/사업화 검토
- "이게 진짜 영세업체에 도움이 되는가" + "이게 기존 오토위니랑 뭐가 다른가" 두 질문에 답을 원함

### 1.2 페르소나가 답해야 할 질문 (= 우리 앱이 해결하는 문제)

김수출 사장님이 자주 하는 질문 5가지:

1. **"이 차, 그 나라에 보낼 수 있나?"** → 통관 가능성 즉시 판정
2. **"이 바이어 메일, 뭐라고 답해야 하지?"** → 다국어 격식 메일 자동 생성
3. **"인보이스/패킹리스트 또 만들어야 하네"** → 자동 PDF 생성
4. **"이 거래 위험한 거 아닌가?"** → 컴플라이언스 자동 검사
5. **"바이어가 내 차 어디 있냐고 또 물어보네"** → 선적/도착 자동 알림

### 1.3 핵심 시나리오 5개

각 시나리오 = 앱의 핵심 모듈 1개. 이 5개로 MVP가 구성됨.

#### 📍 시나리오 1: 차량 등록 + 통관 가능국 자동 판정

```
[김수출 사장님이 새 매물 1대를 매입함]
  └ 차량등록증 사진 찍음 → 앱에 업로드
       └ AI: VIN(차대번호) OCR → NHTSA vPIC API 자동 디코딩
            └ 자동 채움: Make=Hyundai, Model=Sonata, Year=2018, Engine=2.0L, Fuel=Gasoline, Steering=LHD
       └ 사장님: 주행거리·색상·옵션·가격만 추가 입력
            └ 시스템: 룰 엔진 실행 (PoC 5개국)
                 ├ ✅ 도미니카공화국 통관 가능 (10년 이내, LHD, 6기통 이하)
                 ├ ✅ 리비아 통관 가능
                 ├ ❌ 케냐 통관 불가 (RHD만 허용)
                 ├ ⚠️ 키르기스스탄: 가능하나 러시아 우회 위험 모니터링 필요
                 └ ⚠️ 시리아: OFAC 사전 조회 필요
```

**기대 효과:** 사장님이 "이 차 어디로 보낼까?" 고민하는 시간 → 5초로 단축.

#### 📍 시나리오 2: 바이어 등록 + 컴플라이언스 자동 검사

```
[새 바이어가 WhatsApp으로 문의 들어옴]
  └ 사장님이 바이어 정보 앱에 등록
       └ 회사명, 국가, Tax ID, WhatsApp 번호
       └ 시스템: 자동 검증 실행
            ├ Yestrade 우려거래자 조회 (수동 input + DB 매칭)
            ├ OFAC SDN 자동 조회 (오픈 API)
            ├ 국가 기반 위험도 점수 산정
            │   └ 키르기스스탄·카자흐스탄·타지키스탄·아르메니아 = 자동 HIGH
            └ 결과: 🟢 SAFE / 🟡 MONITOR / 🔴 BLOCKED

[BLOCKED 케이스]
  └ 시스템: 대시보드에 빨간 경고 + "이 바이어와 거래 시 형사 처벌 가능" 메시지
  └ 사장님: 단념 또는 산업통상자원부 상황허가 절차 안내 받음
```

**기대 효과:** 2025.10 부산경찰청 적발 사례 같은 위험을 사전 차단.

#### 📍 시나리오 3: 다국어 견적 메일 자동 생성

```
[바이어가 가격·연식 문의 메일 보냄]
  └ 사장님: 앱에서 차량 1대 + 바이어 1명 선택 + "견적 요청 응대" 시나리오 클릭
       └ AI: 바이어 언어 자동 감지 (Mr. Rodríguez @ Dominican Republic → 스페인어)
       └ AI: 차량 정보 + 도미니카 CIF 운임 + 통관 정보 + 결제 조건 자동 조립
       └ 출력: 스페인어 격식 메일 (영문 옵션 동시 제공)
            ├ 인사말 (스페인어 격식)
            ├ 차량 사양 (스페인어로 사양 단위 변환)
            ├ CIF Santo Domingo 가격 견적
            ├ 도미니카 통관 가이드 (10년 이내, LHD, 6기통 이하 충족 표기)
            ├ 결제 조건 (T/T 100% 사전송금)
            └ 다음 단계 안내
       └ 사장님: 한 번 검토 → 보내기

[5개 언어 × 5개 시나리오 = 25개 템플릿 매트릭스]
  ├ 인사·신규 문의 응대
  ├ 견적 요청 응대
  ├ 가격 협상 응대
  ├ 선적 안내
  └ 분쟁·클레임 응대
```

**기대 효과:** 사장님이 영어로 30분, 아랍어로 2시간 걸리던 메일 → 1분.

#### 📍 시나리오 4: 수출 서류 자동 생성 (PDF)

```
[거래 성사 → 서류 작성 단계]
  └ 사장님: "서류 자동 생성" 클릭
       └ 시스템: 차량 + 바이어 정보 통합
       └ AI: 5종 서류 PDF 동시 생성
            ├ Commercial Invoice (영문 + 도미니카는 스페인어 병기)
            ├ Packing List (VIN 표기 필수)
            ├ Shipping Instruction (선사 제출용)
            ├ Certificate of Origin 신청 양식 (대한상공회의소 제출용)
            └ 수출신고 데이터 패키지 (관세사 EDI 송부용)
       └ 운송 방식 분기
            ├ 컨테이너 → 보세구역 반입계 자동 첨부
            └ RoRo → 보세구역 면제 안내

[국가별 추가 자동화]
  ├ 도미니카·칠레·페루: 영사관 인증 신청 가이드 자동 첨부
  ├ 리비아: ACI 사전 등록 가이드 + 아랍어 번역 첨부
  ├ 알제리: ECTN 발급 안내
  └ 케냐·탄자니아: JEVIC 검사 예약 가이드
```

**기대 효과:** 매번 양식 복붙하던 1시간 → 10초. 빠뜨리는 서류 0.

#### 📍 시나리오 5: 선적 후 자동 추적·다국어 알림

```
[B/L 발급 시점부터]
  └ 사장님: B/L 번호 입력
       └ 시스템: 선사 API 또는 수동 추적 등록
       └ AI: 마일스톤마다 자동 알림 (셀러 + 바이어 양쪽)
            ├ 인천항 출항 → 셀러: 한국어 / 바이어: 스페인어
            ├ 환적 (Singapore 등) → 양쪽 자동 알림
            ├ 도착항 도착 (Rio Haina) → 통관 가이드 첨부
            ├ 통관 완료 → "차량 인수 안내"
            └ 등록 완료 → 거래 종료, 후기 요청

[바이어가 "내 차 어디?" 질문 안 보내게 됨]
  └ 사장님은 자정에 깨워서 답할 일 없음
  └ 바이어는 자기 언어로 알림 받아 신뢰도 ↑
```

**기대 효과:** BeForward 트러스트파일럿 1번 불만 ("결제 후 사라진다") 정면 해결.

### 1.4 화면 와이어프레임 (ASCII 러프)

본격 Figma 디자인은 나중. 지금은 "어떤 화면에 뭐가 있는지"만.

#### 화면 1: 대시보드 (홈)

```
┌─────────────────────────────────────────────────────────────┐
│ [로고] AutoExport AI    🌐 한국어 ▾    🔔 3   👤 김수출      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  📊 오늘의 활동                                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │ 매물 12  │ │ 진행 5   │ │ 선적중 3 │ │ 알림 2   │       │
│  │ +2 신규  │ │ 협상중   │ │ 도착예정 │ │ 미응답   │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
│                                                              │
│  🚨 컴플라이언스 경고 (1)                                     │
│  ┌────────────────────────────────────────────────────┐     │
│  │ ⚠️ 키르기스스탄 바이어 "ABC Auto" - 러시아 우회 의심 │     │
│  │ 차량: Genesis G80 (3.3L) - 상황허가 미보유          │     │
│  │ [상세 보기]                          [차단 확정]    │     │
│  └────────────────────────────────────────────────────┘     │
│                                                              │
│  📋 진행 중인 거래                                           │
│  ┌────────────────────────────────────────────────────┐     │
│  │ Sonata 2018 → Mr.Rodríguez (DO)  견적 발송  3시간전 │     │
│  │ Tucson 2019 → Ahmed (LY)         선적 대기  1일전   │     │
│  │ K5 2020 → ..., ...                                  │     │
│  └────────────────────────────────────────────────────┘     │
│                                                              │
│  [+ 새 매물 등록]    [+ 새 바이어 등록]                       │
└─────────────────────────────────────────────────────────────┘
```

#### 화면 2: 매물 등록 + 통관 가능국 판정

```
┌─────────────────────────────────────────────────────────────┐
│  ← 매물 등록                                                 │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  📷 차량등록증 사진                                          │
│  ┌────────────────┐  ☑️ VIN 자동 인식: KMHE...A123456       │
│  │   [업로드]     │  ☑️ 디코딩 완료                         │
│  └────────────────┘                                          │
│                                                              │
│  자동 채움 (NHTSA vPIC):                                    │
│  ├ 제조사: Hyundai     ├ 모델: Sonata                       │
│  ├ 연식: 2018          ├ 배기량: 2.0L                       │
│  ├ 연료: Gasoline      └ 핸들: LHD                          │
│                                                              │
│  추가 입력:                                                  │
│  주행거리: [_____] km   색상: [_____]   가격: [_____] USD   │
│  최초등록일: [____-__-__]                                   │
│  옵션: ☐ 선루프 ☐ 가죽시트 ☐ 후방카메라 ...                │
│                                                              │
│  [통관 가능국 자동 판정 →]                                    │
│                                                              │
│  ╔═══════════════════════════════════════════════════════╗  │
│  ║ 통관 가능국 (PoC 5개국)                               ║  │
│  ╠═══════════════════════════════════════════════════════╣  │
│  ║ 🇩🇴 도미니카공화국  ✅  10년 이내, LHD, 6기통 OK      ║  │
│  ║ 🇱🇾 리비아          ✅  10년 이내, LHD OK             ║  │
│  ║ 🇰🇪 케냐            ❌  RHD만 허용 (LHD 차량)          ║  │
│  ║ 🇰🇬 키르기스스탄    ⚠️  가능, 러시아 우회 모니터 필요  ║  │
│  ║ 🇸🇾 시리아          ⚠️  가능, OFAC 사전 조회 필요      ║  │
│  ╚═══════════════════════════════════════════════════════╝  │
│                                                              │
│                              [매물 저장]   [바이어 매칭 →]   │
└─────────────────────────────────────────────────────────────┘
```

#### 화면 3: 바이어 등록 + 위험도 자동 검사

```
┌─────────────────────────────────────────────────────────────┐
│  ← 바이어 등록                                               │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  기본 정보:                                                  │
│  회사명: [____________]   담당자: [____________]            │
│  국가: [Dominican Republic ▾]   도시: [Santo Domingo]       │
│  WhatsApp: [+1 809 ...]   Email: [...]                      │
│  Tax ID: [____________]                                      │
│  사업자등록증: [📎 첨부]                                     │
│                                                              │
│  [컴플라이언스 자동 검사 →]                                   │
│                                                              │
│  ╔═══════════════════════════════════════════════════════╗  │
│  ║ 검사 결과                                              ║  │
│  ╠═══════════════════════════════════════════════════════╣  │
│  ║ Yestrade 우려거래자       ☑️ 정상                     ║  │
│  ║ OFAC SDN List             ☑️ 매치 없음                ║  │
│  ║ EU 제재 명단              ☑️ 매치 없음                ║  │
│  ║ 국가 기반 위험도          🟢 LOW (도미니카공화국)     ║  │
│  ║ 러시아 우회 위험          🟢 LOW                      ║  │
│  ║ 종합 점수                 92/100 (SAFE)               ║  │
│  ╚═══════════════════════════════════════════════════════╝  │
│                                                              │
│  바이어 선호 정보:                                           │
│  선호 언어: [Spanish ▾]    선호 통화: [USD ▾]              │
│  선호 인코텀즈: [CIF ▾]    선호 항구: [Rio Haina ▾]         │
│                                                              │
│                                            [바이어 저장]      │
└─────────────────────────────────────────────────────────────┘
```

#### 화면 4: 다국어 메일 자동 생성

```
┌─────────────────────────────────────────────────────────────┐
│  ← 메일 작성                                                 │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  차량: [Sonata 2018 KMHE...A123456 ▾]                       │
│  바이어: [Mr.Rodríguez (DO) ▾]                              │
│  시나리오: ●견적 요청  ○가격 협상  ○선적 안내  ○분쟁 응대  │
│  언어: ●스페인어  ○영어  ○병기                              │
│                                                              │
│  [AI로 메일 생성하기]                                         │
│                                                              │
│  ╔═══════════════════════════════════════════════════════╗  │
│  ║ 생성된 메일 (스페인어)               [복사] [영어 보기] ║  │
│  ╠═══════════════════════════════════════════════════════╣  │
│  ║ Estimado Sr. Rodríguez,                                ║  │
│  ║                                                        ║  │
│  ║ Gracias por su interés en nuestro Hyundai Sonata     ║  │
│  ║ 2018 (Ref: SN-2018-001).                              ║  │
│  ║                                                        ║  │
│  ║ Adjunto los detalles del vehículo:                    ║  │
│  ║ - Año: 2018 (cumple límite de 10 años)                ║  │
│  ║ - Cilindrada: 2.0L gasolina (≤6 cilindros ✅)         ║  │
│  ║ - Volante: Izquierda (LHD ✅)                          ║  │
│  ║ - Kilometraje: 65,000 km                              ║  │
│  ║                                                        ║  │
│  ║ Precio CIF Santo Domingo: USD 12,500                  ║  │
│  ║ Forma de pago: T/T 100% por adelantado                ║  │
│  ║ Tiempo de envío: 28-35 días                           ║  │
│  ║                                                        ║  │
│  ║ ...                                                    ║  │
│  ╚═══════════════════════════════════════════════════════╝  │
│                                                              │
│        [수정]  [Gmail로 보내기]  [WhatsApp으로 보내기]        │
└─────────────────────────────────────────────────────────────┘
```

#### 화면 5: 서류 자동 생성

```
┌─────────────────────────────────────────────────────────────┐
│  ← 수출 서류 자동 생성                                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  거래: Sonata 2018 → Mr.Rodríguez (Dominican Republic)      │
│  운송 방식: ●컨테이너  ○RoRo                                 │
│                                                              │
│  생성할 서류 선택:                                           │
│  ☑️ Commercial Invoice (영문 + 스페인어 병기)               │
│  ☑️ Packing List (VIN 표기)                                 │
│  ☑️ Shipping Instruction (선사 제출용)                      │
│  ☑️ Certificate of Origin 신청 양식 (대한상공회의소)        │
│  ☑️ 수출신고 데이터 패키지 (관세사 EDI)                     │
│                                                              │
│  도미니카 추가 안내:                                         │
│  ⚠️ 영사관 인증 필요 — 주한 도미니카 영사관 신청 가이드     │
│  ☑️ DGA 사전 등록 가이드 자동 첨부                          │
│                                                              │
│                              [모두 생성 →]                    │
│                                                              │
│  ╔═══════════════════════════════════════════════════════╗  │
│  ║ 생성 완료 (5/5)                                        ║  │
│  ╠═══════════════════════════════════════════════════════╣  │
│  ║ 📄 Invoice_SN-2018-001.pdf            [👁️ 미리보기]   ║  │
│  ║ 📄 PackingList_SN-2018-001.pdf        [👁️ 미리보기]   ║  │
│  ║ 📄 SI_SN-2018-001.pdf                 [👁️ 미리보기]   ║  │
│  ║ 📄 CO_Application.pdf                 [👁️ 미리보기]   ║  │
│  ║ 📦 Customs_Package.zip                [📥 다운로드]    ║  │
│  ╚═══════════════════════════════════════════════════════╝  │
│                                                              │
│                  [모두 다운로드]  [관세사에게 이메일 송부]    │
└─────────────────────────────────────────────────────────────┘
```

### 1.5 사용자 흐름 다이어그램 (전체)

```
[로그인]
    ↓
[대시보드] ──────────────────────────────────────────┐
    ↓                                                │
    ├──→ [매물 등록] ──→ [통관 판정]                   │
    │         ↓                                       │
    │    [바이어 매칭]                                │
    │                                                  │
    ├──→ [바이어 등록] ──→ [컴플라이언스 검사] ──→ ⚠️ │
    │                              ↓                  │
    │                          [위험도 점수]          │
    │                                                  │
    ├──→ [메일 작성] ──→ [AI 다국어 생성] ──→ [발송]   │
    │                                                  │
    ├──→ [거래 진행] ──→ [서류 자동 생성] ──→ [PDF] ─┤
    │                                                  │
    ├──→ [선적 등록] ──→ [B/L 추적] ──→ [자동 알림]   │
    │                                                  │
    └──→ [거래 종료] ──→ [후기·통계] ────────────────┘
```

---

## Part 2. ERD (Entity-Relationship Design)

User Flow에서 본 화면들이 받쳐줄 데이터 구조.

### 2.1 핵심 엔티티 (테이블) 9개

```
[사용자 측]
├── User (셀러 = 한국 수출업체)
└── UserPreferences (사용자 설정)

[차량 측]
├── Vehicle (매물)
├── VehicleImage (사진·영상)
└── VehicleHistoryRecord (사고·점검 이력)

[바이어 측]
├── Buyer (해외 바이어)
└── ComplianceCheck (컴플라이언스 검사 이력)

[국가·룰 측]
├── Country (국가 메타데이터)
└── ImportRule (국가별 수입 규제 룰)

[거래 측]
├── Listing (매물-바이어 매칭, 거래 단위)
├── Document (자동 생성 서류)
├── Message (AI 메일·WhatsApp 메시지 로그)
└── Shipment (선적 추적)
```

### 2.2 ERD 다이어그램 (텍스트)

```
┌──────────────┐       ┌─────────────────┐
│    User      │1     *│ UserPreferences │
│  (셀러)      ├───────┤                 │
└──────┬───────┘       └─────────────────┘
       │1
       │
       │*
┌──────▼───────┐       ┌─────────────────┐
│   Vehicle    │1     *│ VehicleImage    │
│  (매물)      ├───────┤                 │
│              │       └─────────────────┘
│              │1     *┌─────────────────┐
│              ├───────┤VehicleHistoryRec│
└──────┬───────┘       └─────────────────┘
       │1
       │
       │*
┌──────▼───────┐       ┌─────────────────┐
│   Listing    │*    1 │     Buyer       │
│ (거래 단위)  ├───────┤  (바이어)       │
│              │       └────────┬────────┘
│              │                │1
│              │                │
│              │                │*
│              │       ┌────────▼────────┐
│              │       │ComplianceCheck  │
│              │       └─────────────────┘
│              │
│              │1     *┌─────────────────┐
│              ├───────┤   Document      │
│              │       └─────────────────┘
│              │
│              │1     *┌─────────────────┐
│              ├───────┤    Message      │
│              │       └─────────────────┘
│              │
│              │1     1┌─────────────────┐
│              ├───────┤   Shipment      │
└──────┬───────┘       └─────────────────┘
       │*
       │
       │*
┌──────▼───────┐       ┌─────────────────┐
│   Country    │1     *│   ImportRule    │
│ (메타데이터) ├───────┤  (룰 엔진 연료) │
└──────────────┘       └─────────────────┘

Listing × Country = "이 매물이 이 나라에 갈 수 있는가" 매칭
```

### 2.3 테이블별 핵심 필드

#### 1. User (셀러)

```sql
users:
  id                UUID PRIMARY KEY
  email             VARCHAR  UNIQUE
  password_hash     VARCHAR
  company_name      VARCHAR  -- "동강그린모터스"
  business_no       VARCHAR  -- 사업자번호
  phone             VARCHAR
  address           TEXT
  port_of_loading   VARCHAR  -- "Incheon"
  default_language  VARCHAR  -- 기본 "ko"
  default_currency  VARCHAR  -- 기본 "USD"
  created_at        TIMESTAMP
  last_login        TIMESTAMP
```

#### 2. Vehicle (매물)

```sql
vehicles:
  id                  UUID PRIMARY KEY
  user_id             UUID REFERENCES users
  
  -- 식별
  vin                 VARCHAR(17) UNIQUE
  registration_no     VARCHAR
  registration_date   DATE
  manufacture_date    DATE
  
  -- 사양 (NHTSA vPIC 자동 디코딩)
  make                VARCHAR  -- "Hyundai"
  model               VARCHAR  -- "Sonata"
  year                INTEGER
  trim                VARCHAR
  body_type           VARCHAR  -- Sedan/SUV/Pickup/Van/Bus/Truck
  fuel_type           VARCHAR  -- Gasoline/Diesel/LPG/Hybrid/EV
  engine_cc           INTEGER
  transmission        VARCHAR  -- A/T, M/T
  drivetrain          VARCHAR  -- FWD/RWD/AWD/4WD
  steering            VARCHAR  -- LHD/RHD
  seats               INTEGER
  color_exterior      VARCHAR
  color_interior      VARCHAR
  mileage_km          INTEGER
  
  -- 상태
  options_json        JSONB    -- 선루프, 가죽시트 등
  panel_status_json   JSONB    -- 외판 부위별 상태
  has_accident        BOOLEAN
  accident_history    TEXT
  inspection_grade    VARCHAR  -- "3.5" 또는 "Clean"
  
  -- 가격·재고
  purchase_price_krw  BIGINT
  list_price_usd      DECIMAL(10,2)
  status              VARCHAR  -- available/reserved/sold/shipping/delivered
  port_of_loading     VARCHAR
  
  -- HS Code (자동 분류)
  hs_code             VARCHAR  -- "8703.23"
  
  -- 메타
  created_at          TIMESTAMP
  updated_at          TIMESTAMP
```

#### 3. VehicleImage

```sql
vehicle_images:
  id            UUID PRIMARY KEY
  vehicle_id    UUID REFERENCES vehicles
  url           VARCHAR
  type          VARCHAR  -- exterior_front/exterior_rear/interior/engine/...
  order_index   INTEGER
  uploaded_at   TIMESTAMP
```

#### 4. VehicleHistoryRecord (사고·점검 이력)

```sql
vehicle_history_records:
  id              UUID PRIMARY KEY
  vehicle_id      UUID REFERENCES vehicles
  source          VARCHAR  -- "carhistory" / "car365" / "manual"
  record_type     VARCHAR  -- "accident" / "inspection" / "repair" / "recall"
  record_date     DATE
  details_json    JSONB
  pdf_url         VARCHAR
  created_at      TIMESTAMP
```

#### 5. Buyer

```sql
buyers:
  id                          UUID PRIMARY KEY
  user_id                     UUID REFERENCES users  -- 어느 셀러의 바이어인지
  
  -- 기본
  buyer_type                  VARCHAR  -- Dealer/Importer/Individual/Re-exporter
  company_name                VARCHAR
  contact_person              VARCHAR
  country_code                CHAR(2)  -- ISO 3166-1 (KE, NG, DO, ...)
  city                        VARCHAR
  address                     TEXT
  
  -- 연락
  phone                       VARCHAR
  whatsapp                    VARCHAR
  email                       VARCHAR
  wechat                      VARCHAR
  
  -- 신원
  business_license            VARCHAR
  tax_id                      VARCHAR
  
  -- 선호도
  preferred_language          VARCHAR  -- en/ar/es/ru/fr
  preferred_currency          VARCHAR
  preferred_payment           VARCHAR
  preferred_port              VARCHAR
  preferred_incoterm          VARCHAR
  target_models_json          JSONB
  target_year_min             INTEGER
  target_price_max_usd        DECIMAL(10,2)
  target_mileage_max_km       INTEGER
  volume_per_month            VARCHAR
  
  -- 거래 통계 (집계 필드)
  total_orders                INTEGER  DEFAULT 0
  total_value_usd             DECIMAL(12,2)  DEFAULT 0
  last_order_date             DATE
  payment_reliability_score   INTEGER  -- 0~100
  dispute_count               INTEGER  DEFAULT 0
  
  -- 컴플라이언스 (요약)
  kyc_verified                BOOLEAN  DEFAULT FALSE
  sanctions_status            VARCHAR  -- clean/flagged/blocked
  russia_proxy_risk_score     INTEGER  -- 0~100
  final_destination_declared  VARCHAR
  
  created_at                  TIMESTAMP
  updated_at                  TIMESTAMP
```

#### 6. ComplianceCheck (컴플라이언스 이력)

```sql
compliance_checks:
  id              UUID PRIMARY KEY
  buyer_id        UUID REFERENCES buyers
  vehicle_id      UUID REFERENCES vehicles  NULLABLE  -- 거래 단위 검사
  
  check_type      VARCHAR  -- "yestrade"/"ofac"/"eu_sanctions"/"russia_proxy"
  result          VARCHAR  -- "clean"/"flagged"/"blocked"
  flags_json      JSONB    -- 플래그 상세
  raw_response    JSONB    -- API 원본 응답
  
  checked_at      TIMESTAMP
  checked_by      UUID REFERENCES users  -- 어느 사용자가 트리거
```

#### 7. Country (국가 메타데이터 — 마스터 데이터)

```sql
countries:
  code            CHAR(2) PRIMARY KEY  -- ISO 3166-1 (DO, KE, LY, ...)
  name_en         VARCHAR
  name_ko         VARCHAR
  name_local      VARCHAR
  region          VARCHAR  -- africa/middle_east/central_asia/latin_america/southeast_asia
  
  -- 비즈니스 메타
  primary_language    VARCHAR  -- ar/en/es/ru/fr
  business_language   VARCHAR  -- 실무 사용 언어 (요르단=en이지만 공식=ar)
  steering            VARCHAR  -- LHD/RHD/MIXED
  
  -- 통상
  is_high_risk          BOOLEAN  -- 키르기스스탄·시리아 등
  is_russia_proxy_risk  BOOLEAN  -- KG/KZ/TJ/AM/AZ
  is_sanctioned         BOOLEAN  -- 미·EU 제재
  is_blocked            BOOLEAN  -- 우리 시스템 자동 차단
  
  -- 항구·통관
  main_ports_json       JSONB    -- ["Rio Haina", "Caucedo"]
  pre_registration_system  VARCHAR  -- "DGA"/"ACI"/"Nafeza"/"ECTN"/...
  consular_legalization    BOOLEAN
  
  updated_at      TIMESTAMP
```

#### 8. ImportRule (국가별 수입 규제 룰)

```sql
import_rules:
  id                      UUID PRIMARY KEY
  country_code            CHAR(2) REFERENCES countries
  
  -- 차종별 (NULL이면 전체)
  body_type_filter        VARCHAR  NULLABLE  -- "passenger"/"truck"/"bus"
  
  -- 연식 룰
  age_limit_years         INTEGER  NULLABLE
  age_basis               VARCHAR  -- "manufacture_year"/"first_registration"
  age_effective_from      DATE     NULLABLE  -- 케냐 2026.1.1
  registration_after_date DATE     NULLABLE  -- 케냐: 2019.1.1 이후 등록
  
  -- 기본 룰
  steering_required       VARCHAR  -- LHD_only/RHD_only/MIXED
  max_engine_cc           INTEGER  NULLABLE
  max_cylinders           INTEGER  NULLABLE
  fuel_blocked_json       JSONB    -- ["EV"] 등
  
  -- 검사·서류
  psi_required            VARCHAR[]  -- ["JEVIC", "QISJ"]
  doc_translation_lang    VARCHAR    -- "ar" 등
  consular_required       BOOLEAN
  pre_registration        VARCHAR    -- "DGA"
  
  -- 컴플라이언스
  blocked_conditions_json JSONB    -- 키르기스스탄: 2000cc+ 차단 룰 등
  required_documents_json JSONB
  
  -- 메타
  effective_from          DATE
  effective_to            DATE  NULLABLE
  source_url              VARCHAR
  last_verified_at        DATE
  created_at              TIMESTAMP
```

> 💡 **`countries` ÷ `import_rules` 분리 이유:** 국가 1개당 룰이 여러 개 있을 수 있어서 (차종별, 시기별 효력). 케냐는 2026.1.1 이전 룰과 이후 룰이 다름.

#### 9. Listing (거래 단위 — 핵심 테이블)

```sql
listings:
  id                  UUID PRIMARY KEY
  user_id             UUID REFERENCES users
  vehicle_id          UUID REFERENCES vehicles
  buyer_id            UUID REFERENCES buyers       NULLABLE  -- 매칭 전엔 NULL
  destination_country CHAR(2) REFERENCES countries NULLABLE
  
  -- 룰 엔진 결과
  can_import          BOOLEAN
  import_check_json   JSONB    -- 차단/허용 사유 상세
  
  -- 가격·조건
  agreed_price_usd    DECIMAL(10,2)
  incoterm            VARCHAR  -- CIF/FOB/CFR/EXW
  port_of_loading     VARCHAR  -- "Incheon"
  port_of_discharge   VARCHAR  -- "Rio Haina"
  payment_terms       VARCHAR  -- T/T 100% / L/C 등
  shipping_method     VARCHAR  -- container/roro/bulk
  
  -- 상태 (FSM)
  status              VARCHAR  -- inquiry/quoted/negotiating/agreed/documenting/
                               -- shipping/in_transit/arrived/cleared/delivered/disputed/closed
  
  -- 타임라인
  inquiry_at          TIMESTAMP
  quoted_at           TIMESTAMP
  agreed_at           TIMESTAMP
  shipped_at          TIMESTAMP
  delivered_at        TIMESTAMP
  
  -- 메모
  notes               TEXT
  
  created_at          TIMESTAMP
  updated_at          TIMESTAMP
```

#### 10. Document (자동 생성 서류)

```sql
documents:
  id              UUID PRIMARY KEY
  listing_id      UUID REFERENCES listings
  
  doc_type        VARCHAR  -- invoice/packing_list/si/co_application/customs_package
  language        VARCHAR  -- "en" 또는 "en+es"
  data_json       JSONB    -- 생성에 사용된 데이터 스냅샷
  pdf_url         VARCHAR  -- S3 또는 로컬 경로
  
  generated_by    VARCHAR  -- "ai" / "manual"
  version         INTEGER  -- 수정 시 +1
  
  generated_at    TIMESTAMP
```

#### 11. Message (AI 메일·WhatsApp 메시지 로그)

```sql
messages:
  id              UUID PRIMARY KEY
  listing_id      UUID REFERENCES listings  NULLABLE
  buyer_id        UUID REFERENCES buyers    NULLABLE
  
  channel         VARCHAR  -- email/whatsapp/sms
  direction       VARCHAR  -- outbound/inbound
  scenario        VARCHAR  -- inquiry/quote/negotiate/shipping/dispute
  language        VARCHAR
  content_text    TEXT
  
  ai_generated    BOOLEAN  -- AI 자동 생성 여부
  ai_model        VARCHAR  -- "claude-sonnet-4-7"
  ai_prompt_id    VARCHAR  -- 사용한 템플릿 ID
  
  sent_at         TIMESTAMP
  read_at         TIMESTAMP NULLABLE
```

#### 12. Shipment (선적 추적)

```sql
shipments:
  id                  UUID PRIMARY KEY
  listing_id          UUID REFERENCES listings UNIQUE  -- 1:1
  
  bl_number           VARCHAR
  vessel_name         VARCHAR
  voyage_no           VARCHAR
  container_no        VARCHAR  NULLABLE  -- RoRo면 NULL
  seal_no             VARCHAR  NULLABLE
  
  port_of_loading     VARCHAR
  port_of_discharge   VARCHAR
  etd                 TIMESTAMP  -- 출항예정
  eta                 TIMESTAMP  -- 도착예정
  ata                 TIMESTAMP  -- 실제도착
  
  -- 마일스톤 추적
  milestones_json     JSONB
  -- [
  --   {event: "loaded", at: "2026-05-10T08:00", location: "Incheon"},
  --   {event: "departed", at: "2026-05-10T18:00", ...},
  --   {event: "transshipment", at: "2026-05-15", location: "Singapore"},
  --   {event: "arrived", at: "2026-06-08", location: "Rio Haina"},
  --   {event: "cleared", at: "2026-06-15", ...},
  --   {event: "delivered", at: "2026-06-18"}
  -- ]
  
  -- 알림
  last_notified_at        TIMESTAMP
  next_notification_at    TIMESTAMP
  
  created_at              TIMESTAMP
  updated_at              TIMESTAMP
```

### 2.4 핵심 관계 다시 정리

```
User 1───* Vehicle      (셀러는 매물 여러 개 보유)
User 1───* Buyer        (셀러별 바이어 풀 별도 관리)
User 1───* Listing      (셀러별 거래 이력)

Vehicle 1───* Listing   (한 매물이 여러 거래 후보 (재제안))
Vehicle 1───* VehicleImage
Vehicle 1───* VehicleHistoryRecord

Buyer 1───* ComplianceCheck
Buyer 1───* Listing

Country 1───* ImportRule
Country 1───* Listing (destination)

Listing 1───1 Shipment
Listing 1───* Document
Listing 1───* Message
```

### 2.5 인덱스 권장

성능 최적화 위해:

```sql
CREATE INDEX idx_vehicles_user      ON vehicles(user_id);
CREATE INDEX idx_vehicles_status    ON vehicles(status);
CREATE INDEX idx_vehicles_vin       ON vehicles(vin);

CREATE INDEX idx_buyers_user        ON buyers(user_id);
CREATE INDEX idx_buyers_country     ON buyers(country_code);
CREATE INDEX idx_buyers_sanctions   ON buyers(sanctions_status);

CREATE INDEX idx_listings_user      ON listings(user_id);
CREATE INDEX idx_listings_status    ON listings(status);
CREATE INDEX idx_listings_country   ON listings(destination_country);
CREATE INDEX idx_listings_vehicle   ON listings(vehicle_id);

CREATE INDEX idx_messages_listing   ON messages(listing_id);
CREATE INDEX idx_messages_buyer     ON messages(buyer_id);

CREATE INDEX idx_shipments_listing  ON shipments(listing_id);
CREATE INDEX idx_shipments_eta      ON shipments(eta);
```

### 2.6 핵심 데이터 흐름 (시나리오 → ERD 매핑)

| 사용자 행위 | 작성/수정되는 테이블 |
|------------|-------------------|
| 매물 등록 | `Vehicle`, `VehicleImage` |
| 통관 가능국 판정 | `Country` × `ImportRule` 조회 → 결과는 화면에만 (DB 저장 X) |
| 바이어 등록 | `Buyer`, `ComplianceCheck` (자동 트리거) |
| 매물-바이어 매칭 | `Listing` 신규 생성 (status=inquiry) |
| 견적 메일 작성 | `Message` (ai_generated=true), `Listing` (status=quoted) |
| 거래 합의 | `Listing` (status=agreed, agreed_price_usd 채움) |
| 서류 자동 생성 | `Document` × 5건 신규 |
| B/L 입력 | `Shipment` 신규, `Listing` (status=shipping) |
| 마일스톤 업데이트 | `Shipment.milestones_json` append |
| 도착 알림 발송 | `Message` (ai_generated=true) × 2건 (셀러+바이어) |
| 거래 종료 | `Listing` (status=closed), `Buyer.total_orders++` 등 집계 갱신 |

---

## Part 3. 다음 단계 권장

이번 작업으로 **사용자 흐름 + 데이터 구조** 두 축이 잡혔어요.

### 즉시 다음으로 가야 할 작업

다음 4개 중 1개 선택하시면 됩니다. **(c) 또는 (d)** 추천드려요.

- **(a) Figma 본격 디자인** — 와이어프레임을 픽셀 단위로. 시간 많이 소요.
- **(b) 백엔드 API 명세** — REST endpoints 정의. ERD 끝났으니 자연스러운 다음 단계.
- **(c) 5개국 룰 엔진 YAML 작성** — `ImportRule` 테이블에 시드 데이터로 들어갈 핵심. 이게 있어야 통관 판정 시연 가능. **PoC용 가장 임팩트 큼.**
- **(d) 다국어 메일 템플릿 시드** — `Message` 자동 생성의 핵심. 영어/아랍어/스페인어 × 5시나리오 = 15개. **AI 차별화 시연 핵심.**

룰 엔진(c)과 메일 템플릿(d)은 둘 다 **데모 시연에 직결**되는 자료라서 캡스톤 관점에선 우선순위 가장 높아요.

### 권장 순서

```
[지금] User Flow + ERD ✅
   ↓
[다음] (c) 룰 엔진 YAML 5개국 ── 통관 판정 시연용
   ↓
[그다음] (d) 메일 템플릿 15개 ── AI 차별화 시연용
   ↓
[그다음] (b) 백엔드 API 명세
   ↓
[그다음] (a) Figma 본격 디자인
   ↓
[마지막] 구현
```

룰 엔진 → 메일 → API → 디자인 → 구현 순서가 가장 효율적이에요.

---

*User Flow + ERD 설계 끝.*
