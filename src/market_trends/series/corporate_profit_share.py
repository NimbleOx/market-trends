"""After-tax corporate profits as a percentage of GDP.

BEA's CP series excludes inventory valuation and capital consumption adjustments.
Both inputs are billions of dollars at seasonally adjusted annual rates.

This is one factor in an algebraic decomposition: equity value / GDP equals
(profits / GDP) times (equity value / profits). The same CP and GDP inputs are
used across builders, so the identity holds on shared dates before rounding.
The broader corporate profit measure does not match the nonfinancial coverage
of the equity numerator exactly.
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
            "US after-tax corporate profits, without inventory valuation and capital consumption "
            "adjustments, as a percentage of GDP. Both inputs use seasonally adjusted annual "
            "rates. This is the profit factor in the algebraic decomposition of the Buffett "
            "indicator; its corporate coverage is broader than the nonfinancial equity numerator."
        ),
        sources=[profits_source, gdp_source],
        observations=observations,
    )
