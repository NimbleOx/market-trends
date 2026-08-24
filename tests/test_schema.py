from datetime import date

import pytest

from market_trends.schema import Observation, Series, Source, ValidationError, to_dict, validate


def source(licence: str = "Public domain (US federal government work)") -> Source:
    return Source(name="A source", url="https://example.org/", licence=licence,
                  retrieved_at=date(2026, 1, 1))


def series(**overrides) -> Series:
    defaults = dict(
        id="a-series",
        title="A series",
        unit="percent",
        precision=1,
        frequency="quarterly",
        description="Something measured over time.",
        sources=[source()],
        observations=[
            Observation(date(2020, 1, 1), 1.0),
            Observation(date(2020, 4, 1), 2.0),
        ],
    )
    defaults.update(overrides)
    return Series(**defaults)


def test_a_well_formed_series_validates():
    validate(series())


def test_dates_must_ascend_strictly():
    out_of_order = series(observations=[
        Observation(date(2020, 4, 1), 2.0),
        Observation(date(2020, 1, 1), 1.0),
    ])
    with pytest.raises(ValidationError, match="ascend"):
        validate(out_of_order)


def test_duplicate_dates_are_rejected():
    duplicated = series(observations=[
        Observation(date(2020, 1, 1), 1.0),
        Observation(date(2020, 1, 1), 1.5),
    ])
    with pytest.raises(ValidationError, match="duplicate"):
        validate(duplicated)


def test_non_finite_values_are_rejected():
    # A division by a zero denominator is the realistic way this happens.
    with pytest.raises(ValidationError, match="non-finite"):
        validate(series(observations=[
            Observation(date(2020, 1, 1), 1.0),
            Observation(date(2020, 4, 1), float("inf")),
        ]))


def test_a_source_without_a_licence_decision_is_rejected():
    # The whole point of recording a licence is that somebody decided.
    with pytest.raises(ValidationError, match="licence"):
        validate(series(sources=[source(licence="unknown")]))
    with pytest.raises(ValidationError, match="licence"):
        validate(series(sources=[source(licence="")]))


def test_a_single_point_is_not_a_line():
    with pytest.raises(ValidationError, match="two observations"):
        validate(series(observations=[Observation(date(2020, 1, 1), 1.0)]))


def test_unknown_frequency_is_rejected():
    with pytest.raises(ValidationError, match="frequency"):
        validate(series(frequency="fortnightly"))


def test_to_dict_carries_the_span_and_count():
    payload = to_dict(series())
    assert payload["firstDate"] == "2020-01-01"
    assert payload["lastDate"] == "2020-04-01"
    assert payload["observationCount"] == 2
    assert payload["sources"][0]["licence"]
