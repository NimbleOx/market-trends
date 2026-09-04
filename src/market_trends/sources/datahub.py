"""Long-run equity and gold prices from the datasets GitHub repositories.

The packages supply CSV files, machine-readable licence declarations, and
visible processing history. Requests use the live ``main`` branch, so an
uncached build or refresh can receive revised observations.

The equity package extends Shiller's history after June 2023 using FRED's
SP500. Its PDDL declaration does not resolve restrictions on that underlying
S&P Dow Jones Indices data. The current adapter records the package declaration
and routes both responses to ``cache/open``; neither routing nor deriving a
ratio establishes redistribution rights. See ``docs/sources.md``.

The gold package has monthly prices from 1960 onward and repeats annual
historical averages into monthly rows before 1960. A monthly date alone does
not establish the frequency of the original observation.
"""

from __future__ import annotations

import csv
import io
from datetime import date, datetime

from ..schema import Observation, Source
from .cache import fetch

LICENCE = "ODC-PDDL-1.0"

SP500_URL = "https://raw.githubusercontent.com/datasets/s-and-p-500/main/data/data.csv"
SP500_PAGE = "https://github.com/datasets/s-and-p-500"

GOLD_URL = "https://raw.githubusercontent.com/datasets/gold-prices/main/data/monthly.csv"
GOLD_PAGE = "https://github.com/datasets/gold-prices"


def monthly_prices() -> tuple[list[Observation], Source]:
    """Read positive monthly SP500 values from the Shiller/FRED data package."""
    text = fetch(SP500_URL, name="datahub-sp500.csv", redistributable=True)

    observations: list[Observation] = []
    for row in csv.DictReader(io.StringIO(text)):
        raw = (row.get("SP500") or "").strip()
        if not raw:
            continue

        value = float(raw)
        # The tail of the file carries zeroes in the columns DataHub does not
        # extend; a zero price is padding rather than an observation.
        if value <= 0:
            continue

        observations.append(
            Observation(
                date=datetime.strptime(row["Date"].strip(), "%Y-%m-%d").date(),
                value=value,
            )
        )

    return observations, Source(
        name="Robert J. Shiller, US Stock Markets 1871-Present (via datasets/s-and-p-500)",
        url=SP500_PAGE,
        licence=LICENCE,
        retrieved_at=date.today(),
    )


def gold_prices() -> tuple[list[Observation], Source]:
    """Read gold prices in USD per troy ounce using monthly date labels.

    The package combines World Bank monthly data from 1960 with Timothy Green's
    historical annual averages before 1960, repeated into monthly rows upstream.
    Parsing a YYYY-MM label produces the first day of that month.
    """
    text = fetch(GOLD_URL, name="datahub-gold.csv", redistributable=True)

    observations: list[Observation] = []
    for row in csv.DictReader(io.StringIO(text)):
        raw = (row.get("Price") or "").strip()
        if not raw:
            continue

        value = float(raw)
        if value <= 0:
            continue

        # Dated YYYY-MM rather than a full date.
        observations.append(
            Observation(
                date=datetime.strptime(row["Date"].strip(), "%Y-%m").date(),
                value=value,
            )
        )

    return observations, Source(
        name=(
            "Gold price, monthly since 1833 "
            "(World Bank and National Mining Association, via datasets/gold-prices)"
        ),
        url=GOLD_PAGE,
        licence=LICENCE,
        retrieved_at=date.today(),
    )
