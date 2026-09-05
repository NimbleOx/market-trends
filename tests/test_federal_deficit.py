from datetime import date
from decimal import Decimal

import pytest

from market_trends.schema import Observation, Series, Source, to_dict, validate
from market_trends.trends import federal_deficit


def test_dollars_reverse_the_budget_sign_and_preserve_million_dollar_detail(monkeypatch):
    source = Source("OMB via FRED", "https://fred.stlouisfed.org/series/FYFSD",
                    "Public domain (US federal government work)", date(2026, 9, 5))
    inputs = [
        Observation(date(1901, 6, 30), 63),
        Observation(date(1976, 6, 30), -73732),
        Observation(date(1977, 9, 30), -53659),
        Observation(date(2000, 9, 30), 236241),
        Observation(date(2025, 9, 30), -1774684),
    ]

    def fred_series(series_id):
        assert series_id == "FYFSD"
        return inputs, source

    monkeypatch.setattr(federal_deficit.fred, "series", fred_series)
    series = federal_deficit.build()
    validate(series)
    assert [o.date for o in series.observations] == [o.date for o in inputs]
    assert [o.value for o in series.observations] == [
        -0.063, 73.732, 53.659, -236.241, 1774.684,
    ]
    assert series.sources == [source]
    assert series.unit == "billions of dollars"
    assert series.precision == 1
    assert series.date_basis == "fiscal-year"
    assert series.scale == "linear"


def test_gdp_share_uses_fiscal_year_denominator_and_its_own_source_boundaries(monkeypatch):
    source = Source("OMB via FRED", "https://fred.stlouisfed.org/series/FYFSDFYGDP",
                    "Public domain (US federal government work)", date(2026, 9, 5))
    inputs = [
        Observation(date(1930, 6, 30), 0.75000),
        Observation(date(2000, 9, 30), 2.33507),
        Observation(date(2025, 9, 30), -5.85263),
    ]

    def fred_series(series_id):
        # The similar FYFSGDA188S ID uses calendar-year GDP instead.
        assert series_id == "FYFSDFYGDP"
        return inputs, source

    monkeypatch.setattr(federal_deficit.fred, "series", fred_series)
    series = federal_deficit.build_gdp()
    validate(series)
    assert [o.date for o in series.observations] == [o.date for o in inputs]
    assert [o.value for o in series.observations] == [-0.75, -2.33507, 5.85263]
    assert series.sources == [source]
    assert series.unit == "percent of GDP"
    assert series.precision == 1
    assert series.date_basis == "fiscal-year"
    assert series.scale == "linear"


def test_monthly_budget_sign_scaling_and_dates_preserve_source_coverage(monkeypatch):
    source = Source("Treasury via FRED", "https://fred.stlouisfed.org/series/MTSDS133FMS",
                    "Public domain (US federal government work)", date(2026, 9, 5))
    inputs = [
        Observation(date(1980, 10, 1), -13008),
        Observation(date(2026, 4, 1), 21500.123456789),
        Observation(date(2026, 7, 1), -200000.123456789),
    ]

    def fred_series(series_id):
        assert series_id == "MTSDS133FMS"
        return inputs, source

    monkeypatch.setattr(federal_deficit.fred, "series", fred_series)
    series = federal_deficit.build_monthly()
    validate(series)
    # Source labels and gaps survive unchanged; an incomplete FY2026 must not
    # hide its completed months. Values are actual months, not annualized rates.
    assert [o.date for o in series.observations] == [o.date for o in inputs]
    assert [o.value for o in series.observations] == [13.008, -21.500123, 200.000123]
    assert series.sources == [source]
    assert series.unit == "billions of dollars"
    assert series.precision == 1
    assert series.frequency == "monthly"
    assert series.date_basis is None
    assert "dateBasis" not in to_dict(series)
    assert series.scale == "linear"


def monthly_fixture(values):
    return Series(
        id=federal_deficit.MONTHLY_ID,
        title="Monthly fixture",
        unit="billions of dollars",
        precision=1,
        frequency="monthly",
        description="Synthetic monthly balances for calculation checks.",
        sources=[Source("Treasury via FRED", "https://fred.stlouisfed.org/series/MTSDS133FMS",
                        "Public domain (US federal government work)", date(2026, 9, 5))],
        observations=[
            Observation(date(2024 + i // 12, i % 12 + 1, 1), value)
            for i, value in enumerate(values)
        ],
    )


def test_trailing_year_cancels_a_repeating_zero_sum_seasonal_cycle(monkeypatch):
    cycle = [-6, -5, -4, -3, -2, -1, 1, 2, 3, 4, 5, 6]
    monthly = monthly_fixture([10 + seasonal for seasonal in cycle * 2])
    monkeypatch.setattr(federal_deficit, "build_monthly", lambda: monthly)
    series = federal_deficit.build_ttm()
    validate(series)
    assert len(series.observations) == 13
    assert series.first_date == date(2024, 12, 1)
    assert all(o.value == 120 for o in series.observations)
    assert series.sources == monthly.sources
    assert series.frequency == "monthly"
    assert series.precision == 1
    assert series.date_basis is None
    assert "dateBasis" not in to_dict(series)


def test_trailing_year_includes_current_month_without_looking_forward(monkeypatch):
    monthly = monthly_fixture([1] * 12 + [100])
    monkeypatch.setattr(federal_deficit, "build_monthly", lambda: monthly)
    series = federal_deficit.build_ttm()
    assert series.observations == [
        Observation(date(2024, 12, 1), 12),
        Observation(date(2025, 1, 1), 111),
    ]


def test_trailing_year_preserves_surpluses_and_rounds_after_accurate_summing(monkeypatch):
    monthly = monthly_fixture([-1.234567] * 13)
    monkeypatch.setattr(federal_deficit, "build_monthly", lambda: monthly)
    series = federal_deficit.build_ttm()
    assert [o.value for o in series.observations] == [-14.814804, -14.814804]
    assert series.scale == "linear"


def test_trailing_year_omits_incomplete_windows(monkeypatch):
    monkeypatch.setattr(federal_deficit, "build_monthly", lambda: monthly_fixture([1] * 11))
    assert federal_deficit.build_ttm().observations == []


def test_trailing_year_skips_windows_crossing_a_missing_month_then_recovers(monkeypatch):
    monthly = monthly_fixture([1] * 25)
    # Omit June 2024. Twelve rows ending in January 2025 would cover thirteen
    # calendar months and must not be mistaken for a trailing year.
    monthly.observations.pop(5)
    monkeypatch.setattr(federal_deficit, "build_monthly", lambda: monthly)
    series = federal_deficit.build_ttm()
    assert series.first_date == date(2025, 6, 1)
    assert len(series.observations) == 8
    assert all(o.value == 12 for o in series.observations)


@pytest.mark.network
def test_trailing_year_recent_value_matches_twelve_published_months():
    monthly = federal_deficit.build_monthly()
    trailing = federal_deficit.build_ttm()
    months = [o for o in monthly.observations if date(2025, 8, 1) <= o.date <= date(2026, 7, 1)]
    assert len(months) == 12
    expected = sum(Decimal(str(o.value)) for o in months)
    actual = next(o.value for o in trailing.observations if o.date == date(2026, 7, 1))
    assert Decimal(str(actual)) == expected
    assert trailing.first_date == date(1981, 9, 1)


@pytest.mark.network
def test_monthly_budget_actuals_cover_tax_season_and_the_pandemic():
    series = federal_deficit.build_monthly()
    by_month = {o.date: o.value for o in series.observations}
    assert series.first_date == date(1980, 10, 1)
    assert series.last_date >= date(2026, 7, 1)
    assert all(o.date.day == 1 for o in series.observations)
    assert 5 < by_month[date(1980, 10, 1)] < 20
    assert -170 < by_month[date(2019, 4, 1)] < -150
    assert 800 < by_month[date(2020, 6, 1)] < 900
    assert by_month[date(2026, 7, 1)] > 0


@pytest.mark.network
def test_federal_budget_actuals_cover_surplus_pandemic_and_fiscal_year_change():
    dollars = federal_deficit.build()
    share = federal_deficit.build_gdp()
    by_year = {o.date.year: o for o in dollars.observations}
    gdp_by_year = {o.date.year: o.value for o in share.observations}

    assert dollars.first_date == date(1901, 6, 30)
    assert share.first_date == date(1930, 6, 30)
    assert by_year[1976].date == date(1976, 6, 30)
    assert by_year[1977].date == date(1977, 9, 30)
    assert len(by_year) == len(dollars.observations)  # no extra 1976 transition quarter
    assert by_year[2000].value == pytest.approx(-236.241)
    assert 3000 < by_year[2020].value < 3200
    assert by_year[2025].value == pytest.approx(1774.684)
    assert -2.4 < gdp_by_year[2000] < -2.2
    assert 14 < gdp_by_year[2020] < 16
    assert gdp_by_year[2025] == pytest.approx(5.85263)
