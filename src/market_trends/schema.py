"""The published contract, and the checks that enforce it on write.

The site vendors whatever lands in ``dist/`` and draws it without inspecting it,
so a malformed series here becomes a broken chart there. Everything is validated
before emit, and a failure aborts the build rather than writing a partial file.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import date, datetime, timezone

SCHEMA_VERSION = 1

FREQUENCIES = ("monthly", "quarterly", "annual")
SCALES = ("linear", "log")


class ValidationError(Exception):
    """A series failed a check and must not be published."""


@dataclass(frozen=True)
class Source:
    """Where numbers came from, and under what terms."""

    name: str
    url: str
    #: Short licence identifier, quoted on the site beside the chart. Every
    #: source has to state one: "unknown" is not an acceptable value, because
    #: the point of recording it is to have decided.
    licence: str
    retrieved_at: date


@dataclass(frozen=True)
class Observation:
    date: date
    value: float


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


def to_dict(series: Series) -> dict:
    """The published shape. Kept separate from the dataclass so the wire format
    can change without the computation caring."""
    validate(series)

    return {
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
