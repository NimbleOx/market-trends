"""After-tax corporate profits as a share of GDP.

The first of the two terms the Buffett indicator multiplies together. Market
value over GDP is profits over GDP times market value over profits, so charting
this alongside `market-value-per-dollar-of-profit` splits the headline ratio
into the part that is corporations earning more of the economy and the part that
is investors paying more for those earnings.

After tax rather than before, because the money that accrues to a shareholder is
what a valuation multiple is applied to. Both inputs are BEA, quarterly, and
public domain.
"""

from __future__ import annotations

from ..schema import Observation, Series
from ..sources import fred

ID = "corporate-profit-share"


def build() -> Series:
    profits, profits_source = fred.series("CP")
    gdp, gdp_source = fred.series("GDP")

    # Both are billions of dollars at annual rates, so the ratio needs no
    # unit conversion the way the Z.1 equities series does.
    profits_by_date = {o.date: o.value for o in profits}

    observations = [
        Observation(date=o.date, value=round(profits_by_date[o.date] / o.value * 100.0, 4))
        for o in gdp
        if o.date in profits_by_date and o.value > 0
    ]

    return Series(
        id=ID,
        title="Corporate profits as a share of GDP",
        unit="percent of GDP",
        precision=1,
        frequency="quarterly",
        description=(
            "US after-tax corporate profits as a percentage of GDP. This is the profit half of "
            "the Buffett indicator: the share of national output that ends up as corporate "
            "earnings, before any question of what investors will pay for those earnings."
        ),
        sources=[profits_source, gdp_source],
        observations=observations,
    )
