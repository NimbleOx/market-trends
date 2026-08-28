"""What importers actually paid, rather than what was announced.

Announced tariff rates overstate collections, and by a lot: there are
exemptions and carve-outs, announced rates that never take effect, importers
switching to suppliers in countries that are not tariffed, and incomplete
enforcement. Dividing duties actually collected by the value of goods actually
imported sidesteps every one of those and yields the rate that was really paid.

The numerator is quarterly at annual rates; the denominator is monthly, so the
three months of each quarter are averaged and annualised onto the same footing
rather than the numerator being interpolated down. A quarter without all three
months is dropped instead of being extrapolated from the months that landed.
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
    # Averaging the months and annualising puts the denominator on the
    # numerator's footing, which is the only way the ratio means anything.
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
            "quarter. This is the rate importers actually paid, which runs well below the rates "
            "announced: exemptions, carve-outs, announced rates that never took effect and "
            "switching to suppliers in untariffed countries all sit between the two."
        ),
        sources=[duties_source, goods_source],
        observations=observations,
    )
