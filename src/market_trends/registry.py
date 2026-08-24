"""Every series the build publishes.

A series is added here and nowhere else: the CLI, the tests and the emitted
index all read from this list, so there is one place to forget.
"""

from __future__ import annotations

from collections.abc import Callable

from .schema import Series
from .series import btc_in_gold, buffett_indicator, sp500_in_gold

BUILDERS: dict[str, Callable[[], Series]] = {
    btc_in_gold.ID: btc_in_gold.build,
    buffett_indicator.ID: buffett_indicator.build,
    sp500_in_gold.ID: sp500_in_gold.build,
}
