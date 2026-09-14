"""Nominal employee compensation as a percentage of gross domestic income.

Divide BEA employee compensation (FRED COE, account A033RC) by GDI and
multiply by 100. Both inputs are quarterly current-dollar flows in billions
at seasonally adjusted annual rates, so no further unit conversion is needed.
Join their upstream quarter-start dates and keep all shared observations;
chart consumers can select a shorter display window without truncating the data.

This is the employee-compensation measure of labor's share. It includes wages,
salaries, and employer supplements, but does not impute labor income for the
self-employed. COE matches the requested national-income compensation numerator;
it differs from domestic compensation paid (FRED GDICOMP, account A4002C).
"""

from __future__ import annotations

from ..schema import Observation, Series
from ..sources import fred

ID = "labor-share-gdi"


def build() -> Series:
    compensation, compensation_source = fred.series("COE")
    gdi, gdi_source = fred.series("GDI")
    compensation_by_date = {o.date: o.value for o in compensation}

    observations = [
        Observation(date=o.date, value=round(compensation_by_date[o.date] / o.value * 100.0, 4))
        for o in gdi
        if o.date in compensation_by_date and o.value > 0
    ]

    return Series(
        id=ID,
        title="Labor’s share of gross domestic income",
        unit="percent of GDI",
        precision=1,
        frequency="quarterly",
        description=(
            "US nominal employee compensation divided by nominal gross domestic income, "
            "multiplied by 100. Both BEA inputs are quarterly, seasonally adjusted annual "
            "rates in current dollars. Employee compensation includes wages, salaries, "
            "and employer supplements; this measure does not impute labor income for the "
            "self-employed. Dates label the start of each quarter."
        ),
        sources=[compensation_source, gdi_source],
        observations=observations,
    )
