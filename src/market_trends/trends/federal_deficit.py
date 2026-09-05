"""US federal budget deficits, monthly and annual, in dollars and annual GDP.

OMB's FRED series FYFSD records budget surpluses as positive and deficits as
negative, in millions of current dollars. Negate and divide by 1,000 for
deficits in billions, preserving million-dollar detail in the stored values.
FYFSDFYGDP uses fiscal-year GDP; negate its published percentage directly.
Do not substitute FYFSGDA188S, which uses calendar-year GDP.

Treasury's MTSDS133FMS records the actual monthly budget balance, also in
millions of dollars with deficits negative. Negate and divide by 1,000 for
billions, storing six decimals. Preserve first-of-month labels and source
coverage without filling gaps, annualizing, or seasonal adjustment. Completed
months in an incomplete fiscal year are valid. Monthly sums can differ from
OMB's annual totals because source vintages and accounting adjustments differ;
do not force a reconciliation between independently published series.

The trailing-12-month series sums twelve consecutive signed monthly balances
through each reference month. It smooths the repeating calendar cycle but is
not an official seasonally adjusted monthly estimate. Compute against full
source history before any display filtering; omit initial or gap-crossing
windows without twelve consecutive months. A trailing total can lag turning
points, and exceptional payment shifts can remain visible.

These historical actuals are distinct from BEA's quarterly national-accounts
current expenditure/receipt gap in commentary's federal-deficit-share. They
measure budget flows, not outstanding federal debt. Dollar values are
nominal, without inflation adjustment.

Preserve upstream fiscal-year-end dates: June 30 through FY1976 and September
30 from FY1977. The separate July–September 1976 transition quarter is absent
from these annual inputs. Do not fill it, extend the history of the GDP share
before 1930, or append estimates, projections, or a partial current year.
"""

from __future__ import annotations

from math import fsum

from ..schema import Observation, Series
from ..sources import fred

ID = "federal-deficit"
GDP_ID = "federal-deficit-gdp"
MONTHLY_ID = "federal-deficit-monthly"
TTM_ID = "federal-deficit-ttm"


def build() -> Series:
    balance, source = fred.series("FYFSD")
    return Series(
        id=ID,
        title="US federal deficit",
        unit="billions of dollars",
        precision=1,
        frequency="annual",
        date_basis="fiscal-year",
        description=(
            "The annual US federal budget deficit in billions of current dollars, from "
            "OMB via FRED. Deficits are positive and surpluses are negative. Historical "
            "fiscal-year actuals only, without inflation adjustment; this is the annual "
            "budget balance, not outstanding federal debt. Dates retain the source's "
            "fiscal-year ends. The separate 1976 transition quarter is excluded."
        ),
        sources=[source],
        observations=[
            Observation(date=o.date, value=round(-o.value / 1_000, 3)) for o in balance
        ],
    )


def build_gdp() -> Series:
    balance, source = fred.series("FYFSDFYGDP")
    return Series(
        id=GDP_ID,
        title="US federal deficit as a share of GDP",
        unit="percent of GDP",
        precision=1,
        frequency="annual",
        date_basis="fiscal-year",
        description=(
            "The annual US federal budget deficit as a percentage of fiscal-year GDP, "
            "from OMB via FRED. Deficits are positive and surpluses are negative. "
            "Historical fiscal-year actuals only, beginning in 1930. Dates retain the "
            "source's fiscal-year ends. The separate 1976 transition quarter is excluded."
        ),
        sources=[source],
        observations=[Observation(date=o.date, value=-o.value) for o in balance],
    )


def build_monthly() -> Series:
    balance, source = fred.series("MTSDS133FMS")
    return Series(
        id=MONTHLY_ID,
        title="US monthly federal deficit",
        unit="billions of dollars",
        precision=1,
        frequency="monthly",
        description=(
            "The US federal budget deficit for each month in billions of current dollars, "
            "from the Treasury's Monthly Treasury Statement via FRED. Deficits are "
            "positive and surpluses are negative. Actual monthly cash budget balances, "
            "not seasonally adjusted or annualized; dates label the reference month. "
            "Completed months in an incomplete fiscal year are included. Monthly sums "
            "can differ from OMB's annual totals because source vintages and accounting "
            "adjustments differ. No months are interpolated or filled."
        ),
        sources=[source],
        observations=[
            Observation(date=o.date, value=round(-o.value / 1_000, 6)) for o in balance
        ],
    )


def build_ttm() -> Series:
    monthly = build_monthly()
    observations: list[Observation] = []
    for end in range(11, len(monthly.observations)):
        window = monthly.observations[end - 11:end + 1]
        months = [o.date.year * 12 + o.date.month for o in window]
        if any(current != previous + 1 for previous, current in zip(months, months[1:])):
            continue
        observations.append(
            Observation(date=window[-1].date, value=round(fsum(o.value for o in window), 6))
        )

    return Series(
        id=TTM_ID,
        title="US federal deficit, trailing 12 months",
        unit="billions of dollars",
        precision=1,
        frequency="monthly",
        description=(
            "The US federal budget deficit over the twelve consecutive months ending in "
            "each reference month, in billions of current dollars. Sum of Treasury's "
            "actual monthly balances via FRED; deficits are positive and surpluses are "
            "negative. The trailing-year total smooths the repeating calendar cycle; it "
            "is not an official seasonally adjusted monthly estimate. It can lag turning "
            "points, and exceptional payment shifts can remain visible. Incomplete "
            "windows and windows crossing missing months are omitted. Monthly Treasury "
            "sums can differ from OMB's annual totals because source vintages and "
            "accounting adjustments differ."
        ),
        sources=monthly.sources,
        observations=observations,
    )
