# Backend — 중고차 수출 AI 에이전트

FastAPI + PostgreSQL + Claude API. PoC 5개국 룰엔진 + 다국어 메일 + 서류 자동생성 + 컴플라이언스.

## 빠른 시작

```bash
cd backend

# 가상환경
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
# macOS/Linux
source .venv/bin/activate

# 의존성 설치 (uv 권장)
uv pip install -e ".[dev]"
# 또는
pip install -e ".[dev]"

# .env 준비 (루트의 .env.example 복사)
cp ../.env.example ../.env

# 개발 서버
uvicorn app.main:app --reload --port 8000
```

## 폴더

```
backend/
├── pyproject.toml
└── app/
    ├── main.py           # FastAPI 진입점
    ├── config.py         # 환경변수 (Pydantic Settings)
    ├── db.py             # SQLAlchemy 엔진/세션
    ├── api/              # REST 라우트
    ├── core/             # 룰엔진·컴플라이언스 (예정)
    ├── models/           # SQLAlchemy ORM 모델 (ERD 기반 12 테이블)
    ├── seed/             # configs/rules/*.yaml → ImportRule 시더
    └── services/         # Claude·NHTSA·OFAC 어댑터 (예정)
```

## 룰엔진 시드

```bash
python -m app.seed.import_rules
```

`../configs/rules/*.yaml` 5개국을 읽어 `countries` + `import_rules` 테이블에 upsert.
