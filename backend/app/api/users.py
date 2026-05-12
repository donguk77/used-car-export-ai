"""/api/users/me — 현재 로그인 사용자 (PoC: 단일 사용자) 조회·수정.

GET  /api/users/me  — 프로필 조회 (Settings 페이지)
PATCH /api/users/me — 프로필 수정 (회사명·항구·언어 등)
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id
from app.db import get_db
from app.models import User

router = APIRouter(prefix="/users", tags=["users"])


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    company_name: str
    business_no: str | None
    phone: str | None
    address: str | None
    port_of_loading: str
    default_language: str
    default_currency: str


class UserUpdate(BaseModel):
    """프로필 수정 — email/password_hash 는 Phase 2 (auth)."""
    company_name: str | None = Field(default=None, min_length=1, max_length=255)
    business_no: str | None = Field(default=None, max_length=32)
    phone: str | None = Field(default=None, max_length=32)
    address: str | None = None
    port_of_loading: str | None = Field(default=None, max_length=64)
    default_language: str | None = Field(default=None, pattern=r"^[a-z]{2}$")
    default_currency: str | None = Field(default=None, pattern=r"^[A-Z]{3}$")


@router.get("/me", response_model=UserOut)
def get_me(
    db: Annotated[Session, Depends(get_db)],
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "user not found")
    return user


@router.patch("/me", response_model=UserOut)
def update_me(
    payload: UserUpdate,
    db: Annotated[Session, Depends(get_db)],
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "user not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return user
