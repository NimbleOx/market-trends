"""Bitcoin measured in ounces of gold.

The same question sp500-in-gold asks, of an asset whose entire history fits
inside the last sixteen years of that chart. Both sides are monthly averages, so
neither is favoured by the sampling.

The range is the difficulty here: the ratio starts near four ten-thousandths of
an ounce and reaches the high teens, which is four orders of magnitude. It is a
chart that wants a log scale.
"""

from __future__ import annotations

from ..schema import Observation, Series
from ..sources import blockchain, datahub

ID = "btc-in-gold"


def build() -> Series:
    bitcoin, bitcoin_source = blockchain.monthly_prices()
    gold, gold_source = datahub.gold_prices()

    gold_by_date = {o.date: o.value for o in gold if o.value > 0}

    observations = [
        Observation(date=o.date, value=round(o.value / gold_by_date[o.date], 6))
        for o in bitcoin
        if o.date in gold_by_date
    ]

    return Series(
        id=ID,
        title="Bitcoin priced in gold",
        unit="ounces of gold",
        precision=2,
        frequency="monthly",
        scale="log",
        description=(
            "The price of one bitcoin divided by the price of one troy ounce of gold. Both are "
            "monthly averages. The ratio spans four orders of magnitude, from well under a "
            "thousandth of an ounce in 2010 to the high teens today."
        ),
        sources=[bitcoin_source, gold_source],
        observations=observations,
    )
