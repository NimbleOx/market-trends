"""The S&P 500 measured in ounces of gold rather than dollars.

Dividing one price by another strips out the unit both are quoted in, which is
the point: the line moves only when equities and gold move relative to each
other, not when the dollar does. The 1980 low and the 2000 high are the two
readings the chart exists to show.

Gold is monthly and so is Shiller's price series, so no resampling is needed.
Both reach back further than the other; the ratio starts in 1871, where Shiller's
prices begin.
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
            "The S&P Composite index divided by the price of one troy ounce of gold. Pricing one "
            "asset in another removes the currency both are quoted in, so the line represents "
            "movement relative to each other."
        ),
        sources=[equities_source, gold_source],
        observations=observations,
    )
