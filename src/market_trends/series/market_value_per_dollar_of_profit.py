"""Nonfinancial corporate equity value per dollar of after-tax corporate profit.

This is the valuation factor in the Buffett indicator decomposition. With the
same source observations and shared dates, multiplying it by the percentage
profit share returns the percentage Buffett indicator before rounding.

It is not a conventional P/E for a matched set of companies: the equity input
covers nonfinancial corporations and CP is a broader corporate profit measure.
The multiple can change through changes in equity value, profits, or both.
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
            "US nonfinancial corporate equity value divided by annualised after-tax corporate "
            "profits. This is the valuation factor in the Buffett indicator decomposition. "
            "The profit measure has broader corporate coverage, so this is not a P/E ratio for "
            "a matched set of companies. It can change when equity values, profits, or both change."
        ),
        sources=[equities_source, profits_source],
        observations=observations,
    )
