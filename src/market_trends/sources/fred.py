"""FRED observations from the no-key graph CSV endpoint.

Each accepted ID must be listed in ``LICENCES`` with source attribution,
licence text, and a cache-routing decision. Unlisted IDs raise before fetching.
The mapping records this project's decisions; it does not verify the terms
of the data or hosting service. Review ``docs/sources.md`` when adding an ID
or changing how this endpoint is used.

The adapter preserves upstream dates and values, discarding blank or dotted
missing values. It does not infer missing periods or convert units.
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
#: "redistributable" selects cache/open or cache/restricted; it does not filter
#: emitted output. These entries record the project's current source decisions.
#: Data classification and the hosting service's access terms are separate.
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
    "FYFSD": (
        "US Office of Management and Budget, Federal Surplus or Deficit, via FRED",
        "Public domain (US federal government work)",
        True,
    ),
    "FYFSDFYGDP": (
        "US Office of Management and Budget, Federal Surplus or Deficit as Percent of "
        "Gross Domestic Product, via FRED",
        "Public domain (US federal government work)",
        True,
    ),
    "MTSDS133FMS": (
        "US Department of the Treasury, Monthly Treasury Statement, "
        "Federal Surplus or Deficit, via FRED",
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
    """Fetch an allowlisted FRED ID and return observations with source metadata.

    ``retrieved_at`` records the local build date, including cache hits.
    """
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
