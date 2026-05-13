import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api import buyers, countries, dashboard, health, listings, mcp_server, users, vehicles
from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

# Dev 모드 CORS — Vite·Next.js·CRA 기본 포트.
# 프로덕션은 .env 에서 명시적으로 추가하거나 별도 환경변수로 주입.
DEV_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 시작 시 demo 사용자 보장 (FK 충돌 방지). DB 못 닿으면 경고만."""
    from app.api.deps import ensure_demo_user
    from app.db import SessionLocal

    try:
        with SessionLocal() as session:
            ensure_demo_user(session)
            session.commit()
            logger.info("demo user ensured on startup")
    except Exception as e:  # noqa: BLE001
        logger.warning("could not ensure demo user on startup: %s", e)
    yield


app = FastAPI(
    title="중고차 수출 AI 에이전트 API",
    description="한국 영세 중고차 수출업체용 AI 자동화 SaaS — backend",
    version=__version__,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=DEV_ORIGINS if settings.app_env == "development" else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(listings.router, prefix="/api", tags=["listings"])
app.include_router(vehicles.router, prefix="/api")
app.include_router(buyers.router, prefix="/api")
app.include_router(countries.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(mcp_server.router, prefix="/api")


@app.get("/")
def root() -> dict[str, str]:
    return {
        "name": "used-car-export-ai",
        "version": __version__,
        "docs": "/docs",
    }
