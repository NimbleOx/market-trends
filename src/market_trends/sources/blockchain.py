"""Bitcoin's dollar price from blockchain.com's charts API.

The request uses the full timespan and disables API sampling. Positive readings
are averaged by UTC calendar month, with a minimum of 20 readings per month.
This threshold can admit a partial month; it does not require a completed
calendar month or verify that each reading represents a distinct day.

The adapter records no open licence and caches the response under
``cache/restricted``. The default derived Bitcoin output files are separately
git-ignored. These choices do not establish permission to distribute a ratio;
see ``docs/sources.md`` for the API terms and publication limitations.
"""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import date, datetime, timezone
from statistics import fmean

from ..schema import Observation, Source
from .cache import fetch

URL = "https://api.blockchain.info/charts/market-price?timespan=all&format=json&sampled=false"
PAGE = "https://www.blockchain.com/explorer/charts/market-price"
LICENCE = "No open licence stated; blockchain.com terms. Used to derive, not republished."

#: Minimum positive readings in a UTC month. This is a coverage threshold,
#: not a check for a completed month or for readings on distinct days.
MIN_DAYS = 20


def monthly_prices() -> tuple[list[Observation], Source]:
    """Average positive USD price readings by UTC month, keeping at least 20.

    Monthly averages align the aggregation with the modern gold series.
    ``retrieved_at`` is the local build date, including when the response is cached.
    """
    payload = json.loads(fetch(URL, name="blockchain-market-price.json", redistributable=False))

    days: dict[tuple[int, int], list[float]] = defaultdict(list)
    for point in payload["values"]:
        price = float(point["y"])
        # Bitcoin has a quoted price only from mid-2010; the series carries
        # zeroes before that rather than starting there.
        if price <= 0:
            continue

        when = datetime.fromtimestamp(point["x"], tz=timezone.utc).date()
        days[(when.year, when.month)].append(price)

    observations = [
        Observation(date=date(year, month, 1), value=round(fmean(prices), 4))
        for (year, month), prices in sorted(days.items())
        if len(prices) >= MIN_DAYS
    ]

    return observations, Source(
        name="Bitcoin market price (blockchain.com)",
        url=PAGE,
        licence=LICENCE,
        retrieved_at=date.today(),
    )
