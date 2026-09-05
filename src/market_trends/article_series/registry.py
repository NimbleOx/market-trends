"""Article builders are deliberately absent from the ordinary trend registry."""

from collections.abc import Callable

from ..schema import Series
from . import uncle_sam_has_competition as treasury_article

BUILDERS: dict[str, Callable[[], Series]] = {
    treasury_article.ID_10_YEAR: treasury_article.build_10_year,
    treasury_article.ID_30_YEAR: treasury_article.build_30_year,
}
