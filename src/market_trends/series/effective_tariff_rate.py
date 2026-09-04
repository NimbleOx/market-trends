"""Customs duties as a percentage of goods imports.

This aggregate collections-to-imports ratio can differ from announced tariff
rates because of product mix, exemptions, timing, and sourcing changes. It is
not the tariff rate charged on an individual shipment.

Duties are quarterly billions of dollars at a seasonally adjusted annual rate;
imports are seasonally adjusted monthly millions. Average the three monthly
imports, annualise, and convert to billions before dividing. The implementation
requires exactly three observations in a quarter, assuming one per month;
it does not separately check that those months are distinct.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date

from ..schema import Observation, Series
from ..sources import fred

ID = "effective-tariff-rate"


def build() -> Series:
    duties, duties_source = fred.series("B235RC1Q027SBEA")
    goods, goods_source = fred.series("BOPGIMP")

    # Census reports millions a month; BEA reports billions at an annual rate.
    # Average the three monthly observations, then annualise and convert to
    # billions so numerator and denominator use the same unit and rate basis.
    months: dict[date, list[float]] = defaultdict(list)
    for observation in goods:
        quarter = date(observation.date.year, (observation.date.month - 1) // 3 * 3 + 1, 1)
        months[quarter].append(observation.value)

    imports_by_quarter = {
        quarter: sum(values) / len(values) * 12 / 1000.0
        for quarter, values in months.items()
        if len(values) == 3
    }

    observations = [
        Observation(
            date=o.date, value=round(o.value / imports_by_quarter[o.date] * 100.0, 4)
        )
        for o in duties
        if o.date in imports_by_quarter and imports_by_quarter[o.date] > 0
    ]

    return Series(
        id=ID,
        title="The effective tariff rate on goods imports",
        unit="percent of goods imports",
        precision=1,
        frequency="quarterly",
        description=(
            "Customs duties collected as a percentage of the value of goods imported, by "
            "quarter. Monthly goods imports are aggregated and annualised to match the duties "
            "series. Product mix, exemptions, timing, and sourcing changes can make this "
            "aggregate collections-to-imports ratio differ from announced tariff rates."
        ),
        sources=[duties_source, goods_source],
        observations=observations,
    )
