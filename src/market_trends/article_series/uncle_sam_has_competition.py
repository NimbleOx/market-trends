"""Daily Treasury par yields used in 'Uncle Sam Has Competition'.

Keep January 2 through September 3, 2026, inclusive, from the Treasury's
10 Yr and 30 Yr CSV columns. Values already express percent: 4.77 means
4.77%, so there is no division by 100, averaging, or interpolation. Preserve
observed dates, excluding later releases even when the annual feed grows.

These are par yield-curve observations, not auction yields, total returns,
or Treasury real yields. The fixed window does not prevent upstream revisions;
review regenerated observations before replacing a published article snapshot.

Reproduction details belong here, alongside this article's fixed definition:

* Source: sources/treasury.py, using CSV_URL and PAGE_URL with year=2026.
  Its raw input is cached as cache/open/treasury-par-yields-2026.csv.
* The September 4, 2026 reference snapshot has 170 observations per series.
* The 10-year readings are 4.19% on January 2, 4.75% on July 31, and 4.77%
  on September 3. The 30-year readings are 4.86%, 5.27%, and 5.25% respectively.
* Emit daily data in percent, with two display decimals and a linear scale.
  Missing days are not filled, and observations after END are excluded.
* tests/test_article_series.py checks the reference values and window rules.

Run ``trends articles build --only treasury-10-year-yield-2026
treasury-30-year-yield-2026 --out /tmp/treasury-article-preview`` to reproduce
this pair without replacing other article output. Generated JSON/CSV is under
that directory's series/ folder, with a separate index.json.
See docs/article-series.md for the general build and consumption workflow.
"""

from datetime import date

from ..schema import Series, ValidationError
from ..sources import treasury

START = date(2026, 1, 2)
END = date(2026, 9, 3)
ID_10_YEAR = "treasury-10-year-yield-2026"
ID_30_YEAR = "treasury-30-year-yield-2026"


def _build(maturity: int, series_id: str) -> Series:
    rows, source = treasury.par_yields(year=2026, maturity=maturity)
    observations = [row for row in rows if START <= row.date <= END]
    if not observations or observations[0].date != START or observations[-1].date != END:
        raise ValidationError(f"{series_id}: source must cover {START} through {END}")
    return Series(
        id=series_id,
        title=f"{maturity}-year Treasury yield",
        unit="percent",
        precision=2,
        frequency="daily",
        scale="linear",
        description=(
            f"Daily {maturity}-year Treasury par yield, January 2–September 3, 2026. "
            "Observed dates only; a fixed snapshot for the article."
        ),
        sources=[source],
        observations=observations,
    )


def build_10_year() -> Series:
    return _build(10, ID_10_YEAR)


def build_30_year() -> Series:
    return _build(30, ID_30_YEAR)
