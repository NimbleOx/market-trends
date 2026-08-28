"""What the market pays for a dollar of corporate profit.

The second of the two terms the Buffett indicator multiplies together, and the
one that carries the valuation story. Market value over GDP is profits over GDP
times this, so a rise here is investors repricing the same earnings rather than
corporations earning more.

Effectively an aggregate price-to-earnings ratio, but built from the same two
sources as the Buffett indicator itself so the decomposition is exact rather
than approximate: dividing this series into `buffett-indicator` returns
`corporate-profit-share` to within rounding.
"""

from __future__ import annotations

from ..schema import Observation, Series
from ..sources import fred

ID = "market-value-per-dollar-of-profit"


def build() -> Series:
    equities, equities_source = fred.series("NCBEILQ027S")
    profits, profits_source = fred.series("CP")

    # Z.1 reports millions of dollars; the BEA profit series reports billions.
    equities_by_date = {o.date: o.value / 1000.0 for o in equities}

    observations = [
        Observation(date=o.date, value=round(equities_by_date[o.date] / o.value, 4))
        for o in profits
        if o.date in equities_by_date and o.value > 0
    ]

    return Series(
        id=ID,
        title="Market value per dollar of corporate profit",
        unit="dollars of market value per dollar of profit",
        precision=1,
        frequency="quarterly",
        description=(
            "The market value of US corporate equities divided by after-tax corporate profits. "
            "This is the valuation half of the Buffett indicator, an aggregate price-to-earnings "
            "ratio: it moves when investors reprice the same earnings rather than when "
            "corporations earn more."
        ),
        sources=[equities_source, profits_source],
        observations=observations,
    )
