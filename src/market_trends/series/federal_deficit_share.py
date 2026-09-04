"""Federal current expenditures minus receipts as a percentage of GDP.

Receipts, expenditures, and GDP use the National Income and Product Accounts
basis and are billions of dollars at seasonally adjusted annual rates. This
supports a comparison with the profit share, but not a one-for-one causal
claim about deficits and corporate profits.

The result measures the current-account deficit on this basis, not the unified
budget balance or a fiscal-year total. A single quarter's annualised ratio
can differ substantially from a whole fiscal year. Expenditures minus receipts
makes a deficit positive and a surplus negative.
"""

from __future__ import annotations

from ..schema import Observation, Series
from ..sources import fred

ID = "federal-deficit-share"


def build() -> Series:
    receipts, receipts_source = fred.series("FGRECPT")
    expenditures, expenditures_source = fred.series("FGEXPND")
    gdp, gdp_source = fred.series("GDP")

    receipts_by_date = {o.date: o.value for o in receipts}
    expenditures_by_date = {o.date: o.value for o in expenditures}

    observations = [
        Observation(
            date=o.date,
            value=round(
                (expenditures_by_date[o.date] - receipts_by_date[o.date]) / o.value * 100.0, 4
            ),
        )
        for o in gdp
        if o.date in receipts_by_date and o.date in expenditures_by_date and o.value > 0
    ]

    return Series(
        id=ID,
        title="The federal deficit as a share of GDP",
        unit="percent of GDP",
        precision=1,
        frequency="quarterly",
        description=(
            "Federal current expenditures less current receipts, as a percentage of GDP, on the "
            "national accounts basis. All inputs are quarterly figures at seasonally adjusted "
            "annual rates. This differs from the unified budget balance and from a fiscal-year "
            "total. A deficit is positive; a surplus is negative."
        ),
        sources=[receipts_source, expenditures_source, gdp_source],
        observations=observations,
    )
