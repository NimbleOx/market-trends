"""Daily par yield curves from the US Treasury's annual CSV export.

Read exact maturity headers, not column positions; new tenors can be inserted
upstream. Treasury supplies newest dates first, so sort into ascending order.
Missing maturity readings are omitted without filling gaps. Raw CSV stays in
the ordinary git-ignored open cache; generated article output is separate.
"""

import csv
import io
from datetime import date, datetime

from ..schema import Observation, Source, ValidationError
from .cache import fetch

CSV_URL = (
    "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/"
    "daily-treasury-rates.csv/{year}/all?type=daily_treasury_yield_curve"
    "&field_tdr_date_value={year}&page&_format=csv"
)
PAGE_URL = (
    "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/"
    "TextView?field_tdr_date_value={year}&type=daily_treasury_yield_curve"
)


def _parse(text: str, maturity: int) -> list[Observation]:
    column = f"{maturity} Yr"
    reader = csv.DictReader(io.StringIO(text.lstrip("\ufeff")))
    headers = reader.fieldnames or []
    if headers.count("Date") != 1 or headers.count(column) != 1:
        raise ValidationError(f"Treasury CSV needs unique Date and {column} columns")
    observations = []
    for row in reader:
        raw = (row.get(column) or "").strip()
        if raw.upper() in ("", "N/A", "NA", "."):
            continue
        observations.append(Observation(
            date=datetime.strptime(row["Date"].strip(), "%m/%d/%Y").date(),
            value=float(raw),
        ))
    return sorted(observations, key=lambda row: row.date)


def par_yields(*, year: int, maturity: int) -> tuple[list[Observation], Source]:
    """Return nominal 10- or 30-year par yields in percent, with provenance.

    As with existing adapters, retrieved_at is the local build date, including
    cache hits; it is not a claim about the vintage of the original response.
    """
    if maturity not in (10, 30):
        raise ValueError("Treasury adapter supports 10- and 30-year maturities")
    text = fetch(
        CSV_URL.format(year=year),
        name=f"treasury-par-yields-{year}.csv",
        redistributable=True,
    )
    observations = _parse(text, maturity)
    if any(row.date.year != year for row in observations):
        raise ValidationError(f"Treasury {year} CSV contains dates from another year")
    return observations, Source(
        name="US Treasury",
        url=PAGE_URL.format(year=year),
        licence="Public domain (US federal government work)",
        retrieved_at=date.today(),
    )
