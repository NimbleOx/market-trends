"""The federal deficit as a share of GDP, on the same basis as the profit share.

Charted against `corporate-profit-share` because one sector's deficit is another
sector's surplus: government spending in excess of receipts becomes income
elsewhere, and some of it lands as corporate profit. Reading the two lines
together is the point of the series existing.

Built from NIPA receipts and expenditures rather than the unified budget balance
so it sits on the same accounting basis and the same quarterly frequency as the
profit share it is drawn beside. That basis matters: these are quarterly figures
at annual rates, so a single extraordinary quarter reads far higher than the
fiscal-year deficit for the same period. The second quarter of 2020 shows about
27% of GDP where fiscal 2020 as a whole was 14.9%.

Sign is flipped so a deficit reads positive, which is the direction the chart is
about. Surpluses, of which there are few, cross below zero.
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
            "national accounts basis rather than the unified budget. Quarterly figures at annual "
            "rates, so an extraordinary quarter reads well above the fiscal-year deficit for the "
            "same period. A deficit is positive here; the few surpluses cross below zero."
        ),
        sources=[receipts_source, expenditures_source, gdp_source],
        observations=observations,
    )
