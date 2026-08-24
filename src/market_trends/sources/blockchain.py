"""Bitcoin's dollar price, from blockchain.com's charts API.

Daily back to 2009, and current, which is why it is here rather than a copy in
the datasets org: no such copy exists, and the alternatives were either three
months stale or carried a NonCommercial clause.

The tradeoff is that blockchain.com states no open licence, only its general
terms. So the response is cached under cache/restricted and never committed,
and what this repo publishes from it is a ratio rather than their prices. That
is the same posture the cache split was built for.
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

#: A month needs this many daily readings to get an average. It drops bitcoin's
#: first part-month and whatever partial month the fetch lands in, so every
#: point on the line is built the same way.
MIN_DAYS = 20


def monthly_prices() -> tuple[list[Observation], Source]:
    """Bitcoin in USD, averaged by month.

    Averaged rather than taken at month end so it matches the gold series, which
    is itself a monthly average. Bitcoin moves enough within a month that the two
    differ noticeably, and a ratio built from one of each would be neither.
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
