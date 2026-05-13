"""pytest fixtures — 순수 unit test 위주 (DB 불필요).

신규 4 features 중 DB 의존 부분은 라이브 backend (smoke_test) 로 검증.
여기서는 pure-Python 로직 (pricing baseline, schema validation, regex pattern)
unit test 만.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest


@pytest.fixture
def mock_vehicle():
    """Vehicle 객체 mock — SQLAlchemy 모델 불필요, attribute access 만 필요."""
    def _make(**overrides):
        defaults = dict(
            id="00000000-0000-0000-0000-000000000001",
            user_id="00000000-0000-0000-0000-000000000099",
            make="Hyundai",
            model="Sonata",
            year=2018,
            body_type="Sedan",
            fuel_type="Gasoline",
            engine_cc=2000,
            mileage_km=80_000,
            steering="LHD",
            has_accident=False,
            list_price_usd=9000,
        )
        defaults.update(overrides)
        return SimpleNamespace(**defaults)
    return _make
