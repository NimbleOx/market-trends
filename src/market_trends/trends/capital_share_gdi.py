"""Adjusted corporate profits as a percentage of gross domestic income.

Divide BEA corporate profits with inventory valuation and capital consumption
adjustments (FRED CPROFIT, account A051RC, before tax) by GDI and multiply by
100. Both inputs are quarterly current-dollar flows in billions at seasonally
adjusted annual rates, so their units cancel. Keep every shared upstream
quarter-start date; chart consumers choose the display window.

This corporate-profits proxy for capital's share does not measure all capital
income or all non-labor income. It excludes other components such as rental
income, net interest, and proprietors' income. It is not the complement of the
employee-compensation measure of labor's share, and the two do not sum to 100.
CPROFIT differs from after-tax profits without these adjustments (FRED CP).
"""

from __future__ import annotations

from ..schema import Observation, Series
from ..sources import fred

ID = "capital-share-gdi"


def build() -> Series:
    profits, profits_source = fred.series("CPROFIT")
    gdi, gdi_source = fred.series("GDI")
    profits_by_date = {o.date: o.value for o in profits}

    observations = [
        Observation(date=o.date, value=round(profits_by_date[o.date] / o.value * 100.0, 4))
        for o in gdi
        if o.date in profits_by_date and o.value > 0
    ]

    return Series(
        id=ID,
        title="Capital’s share of gross domestic income",
        unit="percent of GDI",
        precision=1,
        frequency="quarterly",
        description=(
            "US corporate profits before tax, with inventory valuation and capital "
            "consumption adjustments, divided by nominal gross domestic income and "
            "multiplied by 100. Both BEA inputs are quarterly, seasonally adjusted annual "
            "rates in current dollars. This corporate-profits proxy excludes other "
            "capital and non-labor income; it is not 100 minus labor's share, and the "
            "two measures do not sum to 100. Dates label the start of each quarter."
        ),
        sources=[profits_source, gdi_source],
        observations=observations,
    )
