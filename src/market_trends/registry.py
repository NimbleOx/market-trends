"""Map public series IDs to their zero-argument builders.

The CLI and generic network tests use this registry. A build's index includes
the selected builders' output. New series also need documentation, meaningful
value checks, and any applicable output exclusions; see docs/development.md.
"""

from __future__ import annotations

from collections.abc import Callable

from .schema import Series
from .series import (
    btc_in_gold,
    buffett_indicator,
    corporate_profit_share,
    effective_tariff_rate,
    federal_deficit_share,
    market_value_per_dollar_of_profit,
    sp500_in_gold,
)

BUILDERS: dict[str, Callable[[], Series]] = {
    btc_in_gold.ID: btc_in_gold.build,
    buffett_indicator.ID: buffett_indicator.build,
    corporate_profit_share.ID: corporate_profit_share.build,
    effective_tariff_rate.ID: effective_tariff_rate.build,
    federal_deficit_share.ID: federal_deficit_share.build,
    market_value_per_dollar_of_profit.ID: market_value_per_dollar_of_profit.build,
    sp500_in_gold.ID: sp500_in_gold.build,
}
