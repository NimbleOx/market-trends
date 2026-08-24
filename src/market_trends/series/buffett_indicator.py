"""The Buffett indicator: US corporate equities as a share of GDP.

Both inputs are US federal statistics and so are public domain, which is why
this construction is used rather than one built on a proprietary index. The
tradeoff is stated in the description below and should stay there: Z.1 measures
all corporate equity issued by nonfinancial corporate business, listed or not,
so the level runs above charts built on a total-market index. At the 2021 peak
this reads about 219% where a Wilshire 5000 construction reads about 200%. The
shape over time, which is what the chart is for, is the same.

GDP is quarterly, so the series is quarterly. Interpolating it up to monthly
would invent detail the source does not have.
"""

from __future__ import annotations

from ..schema import Observation, Series
from ..sources import fred

ID = "buffett-indicator"


def build() -> Series:
    equities, equities_source = fred.series("NCBEILQ027S")
    gdp, gdp_source = fred.series("GDP")

    # Z.1 reports millions of dollars; GDP reports billions.
    equities_by_date = {o.date: o.value / 1000.0 for o in equities}

    observations = [
        Observation(date=o.date, value=round(equities_by_date[o.date] / o.value * 100.0, 4))
        for o in gdp
        if o.date in equities_by_date and o.value > 0
    ]

    return Series(
        id=ID,
        title="The Buffett indicator",
        unit="percent of GDP",
        precision=1,
        frequency="quarterly",
        description=(
            "The market value of US corporate equities as a percentage of GDP. Built from the "
            "Federal Reserve's Financial Accounts (Z.1), which counts all equity issued by "
            "nonfinancial corporate business whether or not it is publicly listed, so the level "
            "runs above charts built on a total-market index. The shape over time is the same."
        ),
        sources=[equities_source, gdp_source],
        observations=observations,
    )
