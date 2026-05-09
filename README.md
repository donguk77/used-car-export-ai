# 중고차 수출 AI 에이전트 — 산학캡스톤 프로젝트

> **프로젝트명:** LLM Wiki 기반 수출특화 AI 에이전트 (Claude Code 활용)
> **산학파트너:** ㈜하이쓰리디 (이정욱 대표)
> **작성자:** 조우진 (한양대 ERICA 수리데이터사이언스, 22학번)
> **시작일:** 2026.05.09

---

## 📂 프로젝트 자료 인덱스

이 폴더의 5개 리포트는 빌드 시작 전 모든 사전 조사·설계의 결과물입니다.

| # | 파일명 | 분량 | 내용 |
|---|--------|------|------|
| 1 | `used_car_export_research.md` | 472줄 | **시장 리서치 v1** (초안). 정정·확장된 v2 사용 권장 |
| 2 | `used_car_export_research_v2.md` | 690줄 | **시장 리서치 v2 (정식판)**. v1의 7가지 정정 + 시리아·남미 추가 |
| 3 | `used_car_export_top20_countries.md` | 514줄 | **상위 20개국 가이드**. 언어/PSI/영사관/사전등록 매트릭스 |
| 4 | `competitor_analysis_and_features.md` | 444줄 | **경쟁사 분석 + 기능 정의**. MVP 10개 + Phase 1·2·3 로드맵 |
| 5 | `userflow_and_erd.md` | 912줄 | **User Flow + ERD**. 페르소나, 시나리오 5개, 와이어프레임, 12개 테이블 |

### 읽기 권장 순서

처음 읽는다면:
1. `used_car_export_research_v2.md` — 시장 전체 그림
2. `used_car_export_top20_countries.md` — 국가별 디테일
3. `competitor_analysis_and_features.md` — 우리가 만들 것의 차별화·범위
4. `userflow_and_erd.md` — 어떻게 만들 것인가

빠르게 핵심만 파악하려면:
- `competitor_analysis_and_features.md`의 "0. 가장 먼저 — 결정적 발견" 섹션
- `userflow_and_erd.md`의 "1.3 핵심 시나리오 5개" 섹션

---

## 🎯 프로젝트 핵심 요약 (캡스톤 발표용 30초 컷)

**문제:**
- 한국 중고차 수출 시장 글로벌 4위 (8% 점유율)
- 인천 송도 영세 수출업체 1,000여 곳, 대부분 1~2인 운영
- 영어/아랍어/스페인어/러시아어 응대 + 국가별 통관 규제 + 컴플라이언스를 사람이 다 처리

**위협:**
- 2025.10 부산경찰청, 키르기스스탄 우회수출 적발 (40대 구속)
- 2026.1.1 케냐 8년 룰 강화, 2024 러시아 상황허가 798→1,159개 품목 확대
- 영세업체는 규제 변화 추적 안 됨

**해결책:**
> 한국 영세 중고차 수출업체용 **AI 자동화 SaaS**
> (오토위니/BeForward 같은 마켓플레이스 위에서 동작하는 도구)

**5대 차별화:**
1. 국가별 통관 사전 검증
2. 다국어 격식 메일 자동 작성 (영/아/스/러/불)
3. 수출 서류 자동 생성 (인보이스/PL/SI/CO)
4. 컴플라이언스 자동 차단 (러시아 우회/OFAC/Yestrade)
5. 선적 후 24/7 추적·알림

**PoC 5개국:**
도미니카공화국 / 케냐 / 리비아 / 키르기스스탄 / 시리아

---

## 🛠️ 기술 스택 (계획)

| 영역 | 기술 |
|------|------|
| **백엔드** | Python 3.11+ / FastAPI |
| **DB** | PostgreSQL 16 + JSONB |
| **LLM** | Claude API (Anthropic) — 메일 작성·번역·문서 생성 |
| **VIN 디코딩** | NHTSA vPIC API (무료) |
| **PDF 생성** | reportlab |
| **프론트엔드** | React 18 + Tailwind CSS |
| **컴플라이언스** | OFAC SDN List API + Yestrade 수동 통합 |
| **번역** | Claude 직접 |
| **메시지** | (Phase 2) WhatsApp Business API |
| **배포** | Vercel (프론트) + Railway 또는 Fly.io (백엔드) |

---

## 📋 다음 작업 체크리스트

빌드 시작 전 마무리할 설계 작업:

- [ ] **(c) 5개국 룰엔진 YAML** — 도미니카·케냐·리비아·키르기스스탄·시리아
- [ ] **(d) 다국어 메일 템플릿 15개** — 영/아/스 × 5시나리오
- [ ] **(b) 백엔드 API 명세** — REST endpoints

빌드 단계:

- [ ] Git 저장소 초기화 + GitHub 연결
- [ ] FastAPI 프로젝트 구조 셋업
- [ ] PostgreSQL 로컬 + Docker
- [ ] ERD → SQLAlchemy 모델 변환
- [ ] 룰엔진 YAML 로더 + 통관 판정 함수
- [ ] Claude API 통합 (메일 자동 작성)
- [ ] PDF 자동 생성 (인보이스부터)
- [ ] React 프론트 5개 화면 (시연용)
- [ ] 시연 데모 데이터 시드
- [ ] 배포

---

## 🚀 VS Code + Claude Code 셋업 가이드

### 1. 사전 준비

```bash
# Node.js 18+ 확인 (Claude Code 요구사항)
node --version

# 없으면 설치
# macOS: brew install node
# Windows: https://nodejs.org에서 LTS 다운로드
```

### 2. Claude Code 설치

```bash
npm install -g @anthropic-ai/claude-code
```

설치 후 인증:

```bash
claude
# 첫 실행 시 Anthropic 계정 로그인 안내됨
```

### 3. 프로젝트 폴더 셋업

```bash
# 작업 폴더 생성 (예시 경로)
mkdir -p ~/projects/used-car-export-ai
cd ~/projects/used-car-export-ai

# Git 초기화
git init

# 다운받은 5개 markdown 파일을 docs/ 폴더에 넣기
mkdir docs
mv ~/Downloads/used_car_export_research_v2.md docs/
mv ~/Downloads/used_car_export_top20_countries.md docs/
mv ~/Downloads/competitor_analysis_and_features.md docs/
mv ~/Downloads/userflow_and_erd.md docs/
mv ~/Downloads/README.md ./

# VS Code로 열기
code .
```

### 4. VS Code 안에서 Claude Code 사용

VS Code 터미널 (Ctrl+\` / Cmd+\`) 열고:

```bash
claude
```

이러면 우진님이 만든 5개 markdown을 Claude Code가 다 읽고 컨텍스트로 잡습니다. 그 다음 부탁할 수 있는 것 예시:

```
"docs/userflow_and_erd.md 읽고 ERD 기반으로
SQLAlchemy 모델 파일들 생성해줘. 
PostgreSQL 16 기준, FastAPI 프로젝트 구조로."
```

```
"docs/competitor_analysis_and_features.md 보고
MVP 10개 기능 중 1, 2, 8번 기능부터 구현하자.
백엔드 FastAPI 라우트 먼저 잡아줘."
```

```
"docs의 5개 리포트를 다 읽고,
프로젝트 폴더 구조와 첫 README.md를 작성해줘.
backend/, frontend/, docs/ 분리하고."
```

### 5. .gitignore 처음부터

루트에 `.gitignore` 만들어 두세요:

```gitignore
# Python
__pycache__/
*.pyc
.venv/
venv/
.env
.env.local

# Node
node_modules/
.next/
dist/
build/

# IDE
.vscode/settings.json
.idea/

# OS
.DS_Store
Thumbs.db

# Project
*.log
*.sqlite
*.db
secrets/
credentials/
```

### 6. 환경변수 (.env.example)

```env
# Anthropic API
ANTHROPIC_API_KEY=sk-ant-...

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/used_car_export

# 외부 API
NHTSA_VPIC_BASE=https://vpic.nhtsa.dot.gov/api
OFAC_SDN_URL=https://www.treasury.gov/ofac/downloads/sdn.xml

# 앱 설정
APP_ENV=development
APP_PORT=8000
```

`.env.example`은 git에 올리고, 실제 키가 든 `.env`는 절대 올리지 말기.

---

## 📞 컨택

- **산학파트너:** ㈜하이쓰리디 이정욱 대표
- **위치:** 안산
- **이메일:** jeong9004@gmail.com
- **연락처:** 010-7366-9867

---

## 📅 주요 마일스톤

(작성 시 업데이트)

- [x] 2026.05.09 — 사전 조사 완료 (5개 리포트)
- [ ] 2026.05.?? — 룰엔진 YAML + 메일 템플릿 + API 명세 완료
- [ ] 2026.0?.?? — VS Code 환경 셋업 + Git 초기화
- [ ] 2026.0?.?? — 백엔드 MVP (시나리오 1, 2 구현)
- [ ] 2026.0?.?? — 프론트엔드 5개 화면 완료
- [ ] 2026.0?.?? — 시연 영상 촬영
- [ ] 2026.??.?? — 캡스톤 발표

---

*프로젝트 인덱스 끝.*
