"""Long-run series published by the datasets org.

Monthly back to 1871. Shiller publishes the original himself, but states no
licence for it and serves it from a site-builder blob URL that changes whenever
he re-uploads. The datasets org redistributes the same numbers under an explicit
Open Data Commons Public Domain Dedication, from a stable URL, as CSV rather
than a legacy .xls. That is three problems solved by changing where we fetch
from, which is the whole reason sources are separated from series.

Fetched from the GitHub repository rather than the datahub.io mirror. The bytes
are identical, but the repo declares the licence in datapackage.json, carries a
visible history of monthly automated commits so a revision can be read as a
diff, and can be pinned to a commit if that is ever needed.

One caveat worth keeping in view: DataHub extends the series past mid-2023 with
FRED's SP500, which is S&P Dow Jones Indices data and not itself freely
redistributable. The dedication covers the compilation; this repo publishes a
derived ratio rather than the levels either way.
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
    """S&P Composite, monthly. Shiller averages the daily closes within a month."""
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
    """Gold, monthly, back to 1833.

    The World Bank's Pink Sheet from 1960, spliced onto the Timothy Green
    historical table before that. Fetching it here rather than from the World
    Bank directly buys 127 years of history and a link that does not carry a
    release year in its path -- the Pink Sheet URL is versioned, so a hardcoded
    one quietly keeps serving last year's file instead of 404ing.

    The tradeoff is that revisions arrive here later: the datasets copy still
    carries the pre-revision figures for a few dozen Bretton Woods era months,
    where gold was pegged and the difference is cents.
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
        name="Gold price, monthly since 1833 (World Bank and National Mining Association, via datasets/gold-prices)",
        url=GOLD_PAGE,
        licence=LICENCE,
        retrieved_at=date.today(),
    )
