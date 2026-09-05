"""Bitcoin measured in troy ounces of gold.

Both adapters return monthly averages; their ratio measures the gold equivalent
of one bitcoin. The Bitcoin average requires at least 20 positive readings,
which can include an unfinished calendar month. Only matching dates survive.

The ratio spans several orders of magnitude, so a logarithmic display is
requested. Six stored decimal places preserve small early values even though
the display metadata requests two decimal places.
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
            "monthly averages; Bitcoin months require at least 20 positive price readings, "
            "which can include an unfinished month. The ratio spans several orders of "
            "magnitude and uses a logarithmic display scale."
        ),
        sources=[bitcoin_source, gold_source],
        observations=observations,
    )
