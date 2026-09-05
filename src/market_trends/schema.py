"""Data objects, validation rules, and the serialized JSON shape.

The CLI and emitter validate every selected series before writing output.
Validation checks structure and values; it does not establish data freshness,
formula correctness, or permission to reuse a source. See docs/output.md for
the contract and its limits.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field, replace
from datetime import date, datetime, timezone

SCHEMA_VERSION = 1

FREQUENCIES = ("daily", "monthly", "quarterly", "annual")
SCALES = ("linear", "log")


class ValidationError(Exception):
    """A series failed a check and must not be published."""


@dataclass(frozen=True)
class Source:
    """Where numbers came from, and under what terms."""

    name: str
    url: str
    #: Licence identifier or statement of source terms. Validation rejects
    #: empty strings and "unknown"; it does not verify the recorded terms.
    licence: str
    retrieved_at: date


@dataclass(frozen=True)
class Observation:
    date: date
    value: float


@dataclass(frozen=True)
class DateWindow:
    """Inclusive observation-date bounds selected for a data run."""

    start: date
    end: date

    def __post_init__(self) -> None:
        if self.start > self.end:
            raise ValidationError("window start must be on or before its end")

    def to_dict(self) -> dict[str, str]:
        return {"from": self.start.isoformat(), "to": self.end.isoformat()}


@dataclass
class Series:
    id: str
    title: str
    unit: str
    #: Decimal places the site should render. Lives with the data because the
    #: sensible precision is a property of the series, not of the chart.
    precision: int
    frequency: str
    description: str
    sources: list[Source]
    #: How the chart should space its axis. A series covering several orders of
    #: magnitude is unreadable on a linear one.
    scale: str = "linear"
    observations: list[Observation] = field(default_factory=list)
    window: DateWindow | None = None
    #: Optional period-label convention. Fiscal years retain their source
    #: year-end dates and should be displayed as FY YYYY by consumers.
    date_basis: str | None = None

    @property
    def first_date(self) -> date:
        return self.observations[0].date

    @property
    def last_date(self) -> date:
        return self.observations[-1].date


def validate(series: Series) -> None:
    """Raise ``ValidationError`` if the series is not fit to publish."""

    def fail(message: str) -> None:
        raise ValidationError(f"{series.id}: {message}")

    if not series.id or series.id != series.id.lower().strip():
        fail("id must be lowercase and unpadded")
    if " " in series.id:
        fail("id must be URL-safe; use hyphens")
    if series.frequency not in FREQUENCIES:
        fail(f"frequency {series.frequency!r} is not one of {FREQUENCIES}")
    if series.date_basis not in (None, "fiscal-year"):
        fail("date_basis must be omitted or 'fiscal-year'")
    if series.date_basis == "fiscal-year" and series.frequency != "annual":
        fail("fiscal-year date_basis requires annual frequency")
    if series.scale not in SCALES:
        fail(f"scale {series.scale!r} is not one of {SCALES}")
    if series.scale == "log" and any(o.value <= 0 for o in series.observations):
        fail("a log scale cannot carry a zero or negative value")
    if not series.title or not series.unit or not series.description:
        fail("title, unit and description are all required")
    if not series.sources:
        fail("at least one source is required")

    for source in series.sources:
        if not source.licence or source.licence.lower() == "unknown":
            fail(f"source {source.name!r} has no licence recorded")

    if len(series.observations) < 2:
        fail("a series needs at least two observations to be a line")

    seen: set[date] = set()
    previous: date | None = None
    for observation in series.observations:
        if series.window and not series.window.start <= observation.date <= series.window.end:
            fail(f"observation {observation.date.isoformat()} is outside the requested window")
        if observation.date in seen:
            fail(f"duplicate date {observation.date.isoformat()}")
        seen.add(observation.date)

        if previous is not None and observation.date <= previous:
            fail(
                "dates must ascend strictly: "
                f"{observation.date.isoformat()} follows {previous.isoformat()}"
            )
        previous = observation.date

        if observation.value is None or not math.isfinite(observation.value):
            fail(f"non-finite value at {observation.date.isoformat()}")


def windowed(series: Series, window: DateWindow) -> Series:
    """Keep recorded observations within a window, without filling boundary gaps."""
    validate(series)
    observations = [o for o in series.observations if window.start <= o.date <= window.end]
    if len(observations) < 2:
        raise ValidationError(
            f"{series.id}: window {window.start} through {window.end} contains "
            f"{len(observations)} observations; at least two are required"
        )
    return replace(series, observations=observations, window=window)


def to_dict(series: Series) -> dict:
    """Validate and serialize a series, including a new UTC generation timestamp.

    JSON keys are independent of the dataclass field names. Changing the wire
    format requires coordinating with consumers and reviewing SCHEMA_VERSION.
    """
    validate(series)

    payload = {
        "schemaVersion": SCHEMA_VERSION,
        "id": series.id,
        "title": series.title,
        "unit": series.unit,
        "precision": series.precision,
        "frequency": series.frequency,
        "scale": series.scale,
        "description": series.description,
        "sources": [
            {
                "name": source.name,
                "url": source.url,
                "licence": source.licence,
                "retrievedAt": source.retrieved_at.isoformat(),
            }
            for source in series.sources
        ],
        "generatedAt": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "firstDate": series.first_date.isoformat(),
        "lastDate": series.last_date.isoformat(),
        "observationCount": len(series.observations),
        "observations": [
            {"date": observation.date.isoformat(), "value": observation.value}
            for observation in series.observations
        ],
    }
    if series.window is not None:
        payload["window"] = series.window.to_dict()
    if series.date_basis is not None:
        payload["dateBasis"] = series.date_basis
    return payload
