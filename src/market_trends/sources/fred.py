"""FRED, via its no-key CSV endpoint.

FRED redistributes other people's data under their terms, so a licence is a
property of the individual series rather than of FRED. Every series fetched here
has to be named in ``LICENCES`` with a decision already made — an unknown id
raises rather than quietly publishing something that may not be republishable.

The graph CSV endpoint is used instead of the API because it needs no key, which
keeps a clone buildable without secrets.
"""

from __future__ import annotations

import csv
import io
from datetime import date, datetime

from ..schema import Observation, Source
from .cache import fetch

CSV_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
PAGE_URL = "https://fred.stlouisfed.org/series/{series_id}"

#: series id -> (human name, licence, redistributable)
#:
#: "redistributable" decides whether the raw response is committed to cache/open
#: or kept in the ignored cache/restricted. US federal statistics are public
#: domain; index levels generally are not.
LICENCES: dict[str, tuple[str, str, bool]] = {
    "GDP": (
        "US Bureau of Economic Analysis, Gross Domestic Product",
        "Public domain (US federal government work)",
        True,
    ),
    "NCBEILQ027S": (
        "Federal Reserve Board, Financial Accounts of the United States (Z.1)",
        "Public domain (US federal government work)",
        True,
    ),
    "CP": (
        "US Bureau of Economic Analysis, Corporate Profits After Tax",
        "Public domain (US federal government work)",
        True,
    ),
    "FGRECPT": (
        "US Bureau of Economic Analysis, Federal Government Current Receipts",
        "Public domain (US federal government work)",
        True,
    ),
    "FGEXPND": (
        "US Bureau of Economic Analysis, Federal Government Current Expenditures",
        "Public domain (US federal government work)",
        True,
    ),
    "B235RC1Q027SBEA": (
        "US Bureau of Economic Analysis, Federal Government Current Tax Receipts: Customs Duties",
        "Public domain (US federal government work)",
        True,
    ),
    "BOPGIMP": (
        "US Census Bureau, Imports of Goods, Balance of Payments Basis",
        "Public domain (US federal government work)",
        True,
    ),
}


def _parse(text: str, series_id: str) -> list[Observation]:
    reader = csv.DictReader(io.StringIO(text))
    observations: list[Observation] = []

    for row in reader:
        raw = (row.get(series_id) or "").strip()
        # FRED writes "." for a missing observation, and leaves the cell empty
        # in the periods where a quarterly series only carries annual data.
        if raw in ("", "."):
            continue

        stamp = (row.get("observation_date") or row.get("DATE") or "").strip()
        observations.append(
            Observation(
                date=datetime.strptime(stamp, "%Y-%m-%d").date(),
                value=float(raw),
            )
        )

    return observations


def series(series_id: str) -> tuple[list[Observation], Source]:
    """Fetch one FRED series, returning its observations and its provenance."""
    if series_id not in LICENCES:
        raise KeyError(
            f"FRED series {series_id!r} has no licence decision recorded. "
            "Add it to LICENCES in sources/fred.py before using it."
        )

    name, licence, redistributable = LICENCES[series_id]
    text = fetch(
        CSV_URL.format(series_id=series_id),
        name=f"fred-{series_id.lower()}.csv",
        redistributable=redistributable,
    )

    return _parse(text, series_id), Source(
        name=name,
        url=PAGE_URL.format(series_id=series_id),
        licence=licence,
        retrieved_at=date.today(),
    )
