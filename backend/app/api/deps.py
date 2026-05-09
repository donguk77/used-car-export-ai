"""FastAPI 의존성 (Dependencies).

PoC 단계 — auth 없이 단일 사용자 모드. Phase 2 에서 JWT/OAuth 추가 시
get_current_user_id() 시그니처를 그대로 두고 내부 구현만 교체한다.
"""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.models import User

# PoC 모드: 모든 요청이 이 사용자로 처리됨
DEFAULT_USER_ID: uuid.UUID = uuid.UUID("00000000-0000-0000-0000-000000000001")


def get_current_user_id() -> uuid.UUID:
    """현재 로그인한 사용자 ID. PoC 는 fixed UUID."""
    return DEFAULT_USER_ID


def ensure_demo_user(session: Session) -> uuid.UUID:
    """DEFAULT_USER_ID 의 사용자가 DB 에 존재함을 보장 (idempotent upsert)."""
    user = session.get(User, DEFAULT_USER_ID)
    if user is None:
        user = User(
            id=DEFAULT_USER_ID,
            email="demo@used-car-export-ai.local",
            password_hash="!auth_disabled_poc_mode",
            company_name="동강그린모터스 (Demo)",
            business_no="123-45-67890",
            phone="+82-32-555-1234",
            address="123-4 Songdo-dong, Yeonsu-gu, Incheon 21984",
            port_of_loading="Incheon",
            default_language="ko",
            default_currency="USD",
        )
        session.add(user)
        session.flush()
    return user.id
