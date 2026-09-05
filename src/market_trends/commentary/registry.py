"""Commentary datasets grouped by article, with references to shared trends.

Each dataset has one owning catalogue. A shared trend is named in an article's
metadata, but is still built and emitted by the ordinary trend commands.
"""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date

from ..schema import DateWindow, Series, ValidationError
from . import analyzing_the_effects_of_tariffs_on_prices_and_inflation as tariffs
from . import uncle_sam_has_competition as treasury_article
from .why_the_buffett_indicator_keeps_rising import (
    corporate_profit_share,
    federal_deficit_share,
    market_value_per_dollar_of_profit,
)


@dataclass(frozen=True)
class Article:
    title: str
    builders: dict[str, Callable[[DateWindow], Series]]
    default_window: DateWindow
    trend_series: tuple[str, ...] = ()


ARTICLES: dict[str, Article] = {
    "analyzing-the-effects-of-tariffs-on-prices-and-inflation": Article(
        title="Analyzing the Effects of Tariffs on Prices and Inflation",
        builders={tariffs.ID: tariffs.build},
        default_window=DateWindow(date(1992, 1, 1), date(2026, 4, 1)),
    ),
    "uncle-sam-has-competition": Article(
        title="Uncle Sam Has Competition",
        builders={
            treasury_article.ID_10_YEAR: treasury_article.build_10_year,
            treasury_article.ID_30_YEAR: treasury_article.build_30_year,
        },
        default_window=DateWindow(date(2026, 1, 2), date(2026, 9, 3)),
    ),
    "why-the-buffett-indicator-keeps-rising": Article(
        title="Why the Buffett Indicator Keeps Rising",
        builders={
            corporate_profit_share.ID: corporate_profit_share.build,
            federal_deficit_share.ID: federal_deficit_share.build,
            market_value_per_dollar_of_profit.ID: market_value_per_dollar_of_profit.build,
        },
        trend_series=("buffett-indicator",),
        default_window=DateWindow(date(1947, 1, 1), date(2026, 4, 1)),
    ),
}

BUILDERS: dict[str, Callable[[DateWindow], Series]] = {
    series_id: builder
    for article in ARTICLES.values()
    for series_id, builder in article.builders.items()
}


def windows_for(
    series_ids: list[str], *, start: date | None = None, end: date | None = None,
) -> dict[str, DateWindow]:
    """Resolve every selected series' article defaults before any data is fetched.

    An override replaces only its bound; omitted bounds retain each article's
    configured dates. The defaults themselves are never changed by a run.
    """
    selected = set(series_ids)
    windows = {}
    for article_id, article in ARTICLES.items():
        owned = selected.intersection(article.builders)
        if not owned:
            continue
        try:
            window = DateWindow(
                start or article.default_window.start, end or article.default_window.end,
            )
        except ValidationError as error:
            raise ValidationError(f"{article_id}: {error}") from error
        windows.update({series_id: window for series_id in owned})
    return windows


def groups_for(series_ids: list[str]) -> list[dict]:
    """Describe only groups and owned series included in this build's output."""
    selected = set(series_ids)
    return [
        {
            "id": article_id,
            "title": article.title,
            "series": sorted(selected.intersection(article.builders)),
            "trendSeries": list(article.trend_series),
        }
        for article_id, article in sorted(ARTICLES.items())
        if selected.intersection(article.builders)
    ]
