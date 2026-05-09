from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_db

router = APIRouter()


@router.get("")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/db")
def healthcheck_db(db: Annotated[Session, Depends(get_db)]) -> dict[str, str]:
    """DB 연결 ping. Neon 깨어남 (auto-suspend 후 재시작) 트리거 용도."""
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:  # noqa: BLE001
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            f"DB unreachable: {type(e).__name__}",
        ) from e
    return {"status": "ok", "database": "connected"}
