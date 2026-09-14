from datetime import date

import pytest

from market_trends.schema import Observation, Source, validate
from market_trends.trends import capital_share_gdi


def test_adjusted_profits_share_joins_quarters_and_excludes_nonpositive_denominators(monkeypatch):
    # Mismatched coverage catches positional joins and filling missing quarters.
    # The distinct CPROFIT key prevents replacing adjusted before-tax profits
    # with the CP after-tax series used in the commentary catalogue.
    inputs = {
        "CPROFIT": [
            Observation(date(1947, 1, 1), 27.0),
            Observation(date(1947, 7, 1), 40.0),
            Observation(date(1947, 10, 1), 45.0),
            Observation(date(1948, 1, 1), 45.0),
            Observation(date(1948, 4, 1), 46.0),
        ],
        "GDI": [
            Observation(date(1947, 1, 1), 240.0),
            Observation(date(1947, 4, 1), 250.0),
            Observation(date(1947, 7, 1), 300.0),
            Observation(date(1948, 1, 1), 0.0),
            Observation(date(1948, 4, 1), -300.0),
            Observation(date(1948, 7, 1), 310.0),
        ],
    }
    sources = {
        key: Source(
            name=key, url=f"https://fred.stlouisfed.org/series/{key}",
            licence="Public domain (US federal government work)", retrieved_at=date(2026, 9, 14),
        )
        for key in inputs
    }
    monkeypatch.setattr(capital_share_gdi.fred, "series", lambda key: (inputs[key], sources[key]))

    series = capital_share_gdi.build()

    validate(series)
    assert series.observations == [
        Observation(date(1947, 1, 1), 11.25),
        Observation(date(1947, 7, 1), 13.3333),
    ]
    assert series.sources == [sources["CPROFIT"], sources["GDI"]]
    assert series.unit == "percent of GDI"
    assert series.frequency == "quarterly"
    assert series.precision == 1


@pytest.mark.network
def test_capital_share_preserves_long_history_and_adjusted_profits_levels():
    # Broad bounds accommodate revisions but catch after-tax numerator or
    # unit substitutions and preserve the contrast around the financial crisis.
    series = capital_share_gdi.build()
    by_quarter = {o.date: o.value for o in series.observations}

    assert series.first_date == date(1947, 1, 1)
    assert 8.0 < by_quarter[date(1947, 1, 1)] < 10.0
    assert 5.0 < by_quarter[date(2008, 10, 1)] < 9.0
    assert 10.0 < by_quarter[date(2022, 4, 1)] < 14.0
    assert by_quarter[date(2022, 4, 1)] - by_quarter[date(2008, 10, 1)] > 3.0
