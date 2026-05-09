from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api import health, listings
from app.config import get_settings

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="중고차 수출 AI 에이전트 API",
    description="한국 영세 중고차 수출업체용 AI 자동화 SaaS — backend",
    version=__version__,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.app_env == "development" else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(listings.router, prefix="/api", tags=["listings"])


@app.get("/")
def root() -> dict[str, str]:
    return {
        "name": "used-car-export-ai",
        "version": __version__,
        "docs": "/docs",
    }
