from datetime import date

import pytest

from market_trends.schema import Observation, Source, validate
from market_trends.trends import labor_share_gdi


def test_employee_compensation_share_joins_matching_quarters_without_filling_gaps(monkeypatch):
    # Unequal date coverage catches positional joins and carrying a missing
    # quarter forward. Different growth in each input catches inverted ratios.
    inputs = {
        "COE": [
            Observation(date(1947, 1, 1), 120.0),
            Observation(date(1947, 7, 1), 135.0),
            Observation(date(1947, 10, 1), 140.0),
        ],
        "GDI": [
            Observation(date(1947, 1, 1), 240.0),
            Observation(date(1947, 4, 1), 250.0),
            Observation(date(1947, 7, 1), 300.0),
            Observation(date(1948, 1, 1), 300.0),
        ],
    }
    sources = {
        key: Source(
            name=key, url=f"https://fred.stlouisfed.org/series/{key}",
            licence="Public domain (US federal government work)", retrieved_at=date(2026, 9, 14),
        )
        for key in inputs
    }
    monkeypatch.setattr(labor_share_gdi.fred, "series", lambda key: (inputs[key], sources[key]))

    series = labor_share_gdi.build()

    validate(series)
    assert series.observations == [
        Observation(date(1947, 1, 1), 50.0),
        Observation(date(1947, 7, 1), 45.0),
    ]
    assert series.sources == [sources["COE"], sources["GDI"]]
    assert series.unit == "percent of GDI"
    assert series.frequency == "quarterly"


@pytest.mark.network
def test_labor_share_matches_historical_high_and_post_pandemic_low():
    # Broad bounds accommodate BEA revisions while catching unit, denominator,
    # and numerator substitutions that distort the historical measure.
    series = labor_share_gdi.build()
    by_quarter = {o.date: o.value for o in series.observations}

    assert series.first_date == date(1947, 1, 1)
    assert 58.0 < by_quarter[date(1970, 1, 1)] < 60.0
    assert 50.0 < by_quarter[date(2022, 4, 1)] < 53.0
    assert by_quarter[date(1970, 1, 1)] - by_quarter[date(2022, 4, 1)] > 5.0
