"""Windowed daily Treasury par yields used in 'Uncle Sam Has Competition'.

Read the Treasury's 10 Yr and 30 Yr CSV columns for each year covered by the
requested window. Values already express percent: 4.77 means 4.77%, with no
averaging or interpolation. Preserve recorded dates, including gaps for
weekends, holidays, and missing readings. Bounds need not be trading days.

These are par yield-curve observations, not auction yields, total returns,
or Treasury real yields. A window does not prevent upstream revisions;
review regenerated observations before replacing a published snapshot.

The existing IDs retain their 2026 suffix for compatibility with the article's
chart embeds. The supplied window, not the ID, determines the years fetched.
The article registry defaults to the reference snapshot's 2026-01-02 through
2026-09-03 window; CLI --from and --to options can override either bound.
It has 170 observations per maturity. tests/test_article_series.py checks its
quoted values and exercises arbitrary windows, including across calendar years.
"""

from ..schema import DateWindow, Series, windowed
from ..sources import treasury

ID_10_YEAR = "treasury-10-year-yield-2026"
ID_30_YEAR = "treasury-30-year-yield-2026"


def _build(maturity: int, series_id: str, window: DateWindow) -> Series:
    observations = []
    sources = []
    for year in range(window.start.year, window.end.year + 1):
        rows, source = treasury.par_yields(year=year, maturity=maturity)
        observations.extend(rows)
        sources.append(source)

    series = Series(
        id=series_id,
        title=f"{maturity}-year Treasury yield",
        unit="percent",
        precision=2,
        frequency="daily",
        scale="linear",
        description=(
            f"Daily {maturity}-year Treasury par yield. "
            "Recorded observations within the requested window; missing days are not filled."
        ),
        sources=sources,
        observations=observations,
    )
    return windowed(series, window)


def build_10_year(window: DateWindow) -> Series:
    return _build(10, ID_10_YEAR, window)


def build_30_year(window: DateWindow) -> Series:
    return _build(30, ID_30_YEAR, window)
