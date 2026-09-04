"""The S&P Composite index level divided by gold's dollar price.

The ratio tracks equity prices relative to gold and excludes reinvested
dividends. It is an index-level comparison, not the value of a purchased share
or fund. Both inputs use monthly date labels and join by exact date.

Gold observations before 1960 are annual averages repeated into monthly rows
by the upstream package. From 1960 onward gold uses monthly averages. The
result begins with the available equity history in 1871; the earlier segment
cannot show within-year gold movements. See ``docs/series.md`` for provenance
and interpretation.
"""

from __future__ import annotations

from ..schema import Observation, Series
from ..sources import datahub

ID = "sp500-in-gold"


def build() -> Series:
    equities, equities_source = datahub.monthly_prices()
    gold, gold_source = datahub.gold_prices()

    gold_by_date = {o.date: o.value for o in gold if o.value > 0}

    observations = [
        Observation(date=o.date, value=round(o.value / gold_by_date[o.date], 4))
        for o in equities
        if o.date in gold_by_date
    ]

    return Series(
        id=ID,
        title="The S&P 500 priced in gold",
        unit="ounces of gold",
        precision=2,
        frequency="monthly",
        description=(
            "The S&P Composite index level divided by the USD price of one troy ounce of gold. "
            "Monthly equity prices are paired with monthly gold averages from 1960 onward; "
            "earlier gold values are annual averages repeated for each month. This measures "
            "relative prices and excludes reinvested dividends."
        ),
        sources=[equities_source, gold_source],
        observations=observations,
    )
