"""Unit tests — app.services.pricing.

DB 의존성 없는 부분 위주 (baseline 보간, country multiplier, factor 적용).
DB 동급 통계 부분은 mock session 사용.
"""
from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock

import pytest

from app.services.pricing import (
    BASELINE_TABLE,
    COUNTRY_PRICE_MULTIPLIER,
    LUXURY_MAKES,
    PriceFactor,
    _baseline_price,
    _country_reason,
    suggest_price,
)


# ── _baseline_price ────────────────────────────────────────────


class TestBaselinePrice:
    """Body × Fuel × Age baseline 보간 로직."""

    def test_exact_keys_returned(self, mock_vehicle):
        v = mock_vehicle(body_type="Sedan", fuel_type="Gasoline", year=2018)
        # 2018 차량, today=2024 → 6년
        price = _baseline_price(v, date(2024, 1, 1))
        # table: 5y=$9000, 7y=$7000 → 6y 보간 = 8000
        assert price == 8000

    def test_age_below_first_key_uses_floor(self, mock_vehicle):
        """0년 미만 (미래 차량) → 0년 baseline (17000)."""
        v = mock_vehicle(body_type="Sedan", fuel_type="Gasoline", year=2030)
        price = _baseline_price(v, date(2024, 1, 1))
        assert price == 17000

    def test_age_above_last_key_uses_ceil(self, mock_vehicle):
        """15년 초과 → 15년 baseline."""
        v = mock_vehicle(body_type="Sedan", fuel_type="Gasoline", year=2000)
        price = _baseline_price(v, date(2024, 1, 1))
        assert price == 4000  # 15y baseline

    def test_hev_normalization(self, mock_vehicle):
        """HEV/PHEV/BEV/EV → Hybrid 키로 통합."""
        for fuel in ("HEV", "PHEV", "BEV", "EV"):
            v = mock_vehicle(body_type="Sedan", fuel_type=fuel, year=2020)
            price = _baseline_price(v, date(2024, 1, 1))
            # Sedan/Hybrid 3y=16000, 5y=12000 → 4y 보간 = 14000
            assert price == 14000, f"{fuel} 정규화 실패"

    def test_body_type_aliases(self, mock_vehicle):
        """소문자/Hatchback/Coupe → Sedan 매핑."""
        for body in ("sedan", "Hatchback", "Coupe"):
            v = mock_vehicle(body_type=body, fuel_type="Gasoline", year=2018)
            price = _baseline_price(v, date(2024, 1, 1))
            assert price == 8000, f"{body!r} 매핑 실패"

    def test_unknown_body_returns_none(self, mock_vehicle):
        v = mock_vehicle(body_type="UFO", fuel_type="Gasoline", year=2018)
        assert _baseline_price(v, date(2024, 1, 1)) is None

    def test_missing_body_returns_none(self, mock_vehicle):
        v = mock_vehicle(body_type=None, fuel_type="Gasoline")
        assert _baseline_price(v, date(2024, 1, 1)) is None

    def test_missing_year_uses_today(self, mock_vehicle):
        """year=None → age=0 → 0년 baseline."""
        v = mock_vehicle(body_type="Sedan", fuel_type="Gasoline", year=None)
        price = _baseline_price(v, date(2024, 1, 1))
        assert price == 17000  # 0년 baseline


# ── Country multiplier ──────────────────────────────────────────


class TestCountryMultiplier:
    """COUNTRY_PRICE_MULTIPLIER 데이터 정합성."""

    def test_syria_premium(self):
        """시리아 재건 수요 +10%."""
        assert COUNTRY_PRICE_MULTIPLIER["SY"] == 1.10

    def test_russia_proxy_discount(self):
        """중앙아시아 우회수출 할인."""
        for cc in ("KG", "KZ", "AM"):
            assert COUNTRY_PRICE_MULTIPLIER[cc] < 1.0, f"{cc} should discount"

    def test_dominican_premium(self):
        """도미니카 6기통 이하 한정 → 단가 강세."""
        assert COUNTRY_PRICE_MULTIPLIER["DO"] >= 1.0

    def test_chile_premium(self):
        """칠레 SUV·디젤 강세."""
        assert COUNTRY_PRICE_MULTIPLIER["CL"] == 1.10


# ── _country_reason ─────────────────────────────────────────────


class TestCountryReason:
    def test_premium_market(self):
        assert "강세 시장" in _country_reason("SY", 10.0)

    def test_discount_market(self):
        assert "할인 시장" in _country_reason("KG", -5.0)

    def test_neutral(self):
        msg = _country_reason("AE", 0.0)
        assert "AE" in msg


# ── suggest_price (with mock DB) ─────────────────────────────────


class TestSuggestPrice:
    """전체 시세 산출 — DB 호출 mock."""

    def _mock_db_empty(self):
        """DB 동급 차량 0건."""
        db = MagicMock()
        db.execute.return_value.scalars.return_value = []
        return db

    def test_baseline_only_no_db_match(self, mock_vehicle):
        v = mock_vehicle(body_type="Sedan", fuel_type="Gasoline", year=2018, mileage_km=100_000)
        suggestion = suggest_price(self._mock_db_empty(), v, today=date(2024, 1, 1))
        assert suggestion.method == "baseline_table"
        assert suggestion.confidence == "low"
        assert suggestion.n_samples == 0
        # mileage 100,000 = 기준, factor 없거나 0
        mileage_factors = [f for f in suggestion.factors if "주행거리" in f.label]
        # 정확히 100,000 → delta 0 → factor 생략 가능 (abs < 0.5)
        if mileage_factors:
            assert abs(mileage_factors[0].delta_pct) < 0.5
        # 시세 = baseline
        assert suggestion.suggested_fob_usd == suggestion.baseline_usd

    def test_country_multiplier_applied(self, mock_vehicle):
        v = mock_vehicle(body_type="Sedan", fuel_type="Gasoline", year=2018, mileage_km=100_000)
        sy = suggest_price(self._mock_db_empty(), v, destination_country="SY", today=date(2024, 1, 1))
        kg = suggest_price(self._mock_db_empty(), v, destination_country="KG", today=date(2024, 1, 1))
        do = suggest_price(self._mock_db_empty(), v, destination_country="DO", today=date(2024, 1, 1))
        # SY (1.10) > DO (1.05) > KG (0.95)
        assert sy.suggested_fob_usd > do.suggested_fob_usd > kg.suggested_fob_usd

    def test_mileage_factor_discount(self, mock_vehicle):
        """20만km 차량 → -20% mileage factor."""
        v = mock_vehicle(body_type="Sedan", fuel_type="Gasoline", year=2018, mileage_km=200_000)
        suggestion = suggest_price(self._mock_db_empty(), v, today=date(2024, 1, 1))
        mileage = next(f for f in suggestion.factors if "주행거리" in f.label)
        assert mileage.delta_pct == -20.0  # clamp 적용 ((200k-100k)/10k*-2 = -20)

    def test_mileage_factor_premium_clamped(self, mock_vehicle):
        """0km 차량 → +20% (clamp)."""
        v = mock_vehicle(body_type="Sedan", fuel_type="Gasoline", year=2020, mileage_km=0)
        suggestion = suggest_price(self._mock_db_empty(), v, today=date(2024, 1, 1))
        mileage = next(f for f in suggestion.factors if "주행거리" in f.label)
        # (0-100k)/10k*-2 = +20 → clamp +20
        assert mileage.delta_pct == 20.0

    def test_accident_factor(self, mock_vehicle):
        v = mock_vehicle(
            body_type="Sedan", fuel_type="Gasoline", year=2018,
            mileage_km=100_000, has_accident=True,
        )
        suggestion = suggest_price(self._mock_db_empty(), v, today=date(2024, 1, 1))
        accident = next(f for f in suggestion.factors if "사고이력" in f.label)
        assert accident.delta_pct == -15.0
        # 가격 = baseline × 0.85
        assert suggestion.suggested_fob_usd == pytest.approx(suggestion.baseline_usd * 0.85)

    def test_luxury_factor_applied(self, mock_vehicle):
        v = mock_vehicle(
            make="Genesis",
            body_type="Sedan", fuel_type="Gasoline", year=2020,
            mileage_km=100_000,
        )
        suggestion = suggest_price(self._mock_db_empty(), v, today=date(2024, 1, 1))
        luxury = next(f for f in suggestion.factors if "Luxury" in f.label)
        assert luxury.delta_pct == 35.0

    def test_range_15pct(self, mock_vehicle):
        """range_low/high = ±15%."""
        v = mock_vehicle(body_type="Sedan", fuel_type="Gasoline", year=2018, mileage_km=100_000)
        s = suggest_price(self._mock_db_empty(), v, today=date(2024, 1, 1))
        assert s.range_low == pytest.approx(s.suggested_fob_usd * 0.85)
        assert s.range_high == pytest.approx(s.suggested_fob_usd * 1.15)

    def test_missing_fields_fallback_8000(self, mock_vehicle):
        """body_type/fuel_type 미입력 → 기본값 8000 USD."""
        v = mock_vehicle(body_type=None, fuel_type=None, year=2018)
        s = suggest_price(self._mock_db_empty(), v, today=date(2024, 1, 1))
        assert s.baseline_usd == 8000.0
        assert any("baseline 미정의" in n for n in s.notes)

    def test_unknown_country_no_multiplier(self, mock_vehicle):
        """미정의 국가 → multiplier 없음, notes 안내."""
        v = mock_vehicle(body_type="Sedan", fuel_type="Gasoline", year=2018, mileage_km=100_000)
        s = suggest_price(
            self._mock_db_empty(), v,
            destination_country="ZZ",  # 미정의
            today=date(2024, 1, 1),
        )
        country_factors = [f for f in s.factors if "ZZ" in f.label]
        assert not country_factors
        assert any("ZZ" in n and "미정의" in n for n in s.notes)


# ── Data integrity ──────────────────────────────────────────────


class TestBaselineTableIntegrity:
    """BASELINE_TABLE 데이터 일관성."""

    def test_age_keys_sorted(self):
        for key, table in BASELINE_TABLE.items():
            ages = list(table.keys())
            assert ages == sorted(ages), f"{key} ages not sorted"

    def test_prices_decreasing(self):
        """연식 ↑ → 가격 ↓ (단조 감소)."""
        for key, table in BASELINE_TABLE.items():
            ages = sorted(table.keys())
            prices = [table[a] for a in ages]
            assert prices == sorted(prices, reverse=True), f"{key} not monotonic decreasing"

    def test_all_combinations_have_15y_max(self):
        """모든 조합이 15년까지 정의돼야 (보간 fallback)."""
        for key, table in BASELINE_TABLE.items():
            assert 15 in table, f"{key} missing 15-year baseline"

    def test_luxury_makes_nonempty(self):
        assert "Genesis" in LUXURY_MAKES
        assert len(LUXURY_MAKES) >= 3
