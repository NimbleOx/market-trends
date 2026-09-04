"""Nonfinancial corporate equity value as a percentage of annualised GDP.

The Federal Reserve's Z.1 input includes publicly traded and closely held
nonfinancial corporations. Its sector coverage differs from a total-market
stock index, so neither levels nor movements are interchangeable with every
other construction of the Buffett indicator.

The numerator is a quarter-end stock in millions of dollars; GDP is a quarterly
flow in billions at a seasonally adjusted annual rate. Convert the numerator
to billions and join using the upstream quarter labels. Do not interpolate GDP
to a finer frequency.
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
            "The quarter-end value of US nonfinancial corporate equities as a percentage of "
            "annualised GDP. The Federal Reserve's Financial Accounts (Z.1) include publicly "
            "traded and closely held nonfinancial corporations. This coverage differs from "
            "a total-market stock index, so levels and movements can differ between constructions."
        ),
        sources=[equities_source, gdp_source],
        observations=observations,
    )
