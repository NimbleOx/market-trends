# Series

This page documents three maintained trends and four commentary ratios.
Each builder joins upstream observations, computes a ratio, and returns a
`Series` with its source records and display metadata. A build writes
`series/<id>.json` and `series/<id>.csv` under the output directory.
See [Output](output.md) for the file format and
[Sources and licences](sources.md) for reuse terms.

The trend registry contains `sp500-in-gold`, `btc-in-gold`, and
`buffett-indicator`. The other four ratios belong to commentary article groups
and are emitted under `dist-commentary/`. The daily Treasury commentary pair
is documented with its [article group](article-series.md#commentary-groups).

| ID | Measures | Frequency | History starts¹ | Scale | Catalogue |
| --- | --- | --- | --- | --- | --- |
| [`sp500-in-gold`](#sp500-in-gold) | S&P Composite index relative to gold | monthly | 1871-01 | linear | Trends |
| [`btc-in-gold`](#btc-in-gold) | Gold equivalent of one bitcoin | monthly | 2010-09 | log | Trends |
| [`buffett-indicator`](#buffett-indicator) | Nonfinancial corporate equity value / GDP | quarterly | 1947 Q4 | linear | Trends |
| [`corporate-profit-share`](#corporate-profit-share) | After-tax corporate profits / GDP | quarterly | 1947 Q1 | linear | Commentary |
| [`market-value-per-dollar-of-profit`](#market-value-per-dollar-of-profit) | Nonfinancial corporate equity value / after-tax profits | quarterly | 1947 Q4 | linear | Commentary |
| [`federal-deficit-share`](#federal-deficit-share) | Federal current expenditures minus receipts / GDP | quarterly | 1947 Q1 | linear | Commentary |
| [`effective-tariff-rate`](#effective-tariff-rate) | Customs duties / goods imports | quarterly | 1992 Q1 | linear | Commentary |

¹ Start dates reflect the checked-in indexes. Maintained trends use the history
available in their inputs; commentary datasets select observations within their
configured or overridden date windows. Read `firstDate`, `lastDate`, and
`observationCount` from the generated JSON for the actual coverage.

## sp500-in-gold

```text
value = monthly S&P Composite index level / gold price in USD per troy ounce
```

The two inputs come from `datasets/s-and-p-500` and `datasets/gold-prices`.
The ratio shows equities moving relative to gold. It uses the index price
level; dividends are not reinvested, and it does not represent the return of
a purchased share or fund.

The equity package uses Shiller's historical series through June 2023 and
extends it with monthly averages of FRED's daily S&P 500 prices. This repository
reads the package's `SP500` column directly. See the
[upstream source description](https://github.com/datasets/s-and-p-500#data)
and [extension script](https://github.com/datasets/s-and-p-500/blob/main/scripts/update_from_fred.py).

Gold is a monthly average from 1960 onward. For 1833–1959, the upstream
monthly file repeats each year's annual average in all twelve months. The
pre-1960 ratio therefore combines monthly equities with annual gold values;
it does not reveal within-year gold movements. See the
[gold package's construction notes](https://github.com/datasets/gold-prices#notes-from-the-sources).

Only matching dates with positive prices survive. Values are rounded to four
decimal places; `precision: 2` requests two decimal places for display.
The published `unit` is `ounces of gold`, with the index-level interpretation
above.

Implementation: [src/market_trends/trends/sp500_in_gold.py](https://github.com/NimbleOx/market-trends/blob/main/src/market_trends/trends/sp500_in_gold.py).

## btc-in-gold

```text
value = monthly bitcoin price in USD / monthly gold price in USD per troy ounce
```

This measures how many troy ounces of gold have the same quoted value as one
bitcoin. The source adapter groups blockchain.com timestamps by UTC calendar
month, discards nonpositive prices, and takes an arithmetic mean of the
remaining readings. A month needs at least 20 readings to qualify. This is a
coverage threshold: a month can qualify before it has ended, and the adapter
does not check for one reading per distinct day.

Bitcoin monthly averages are rounded to four decimal places before division.
The ratio is rounded to six decimal places and carries `precision: 2` and
`scale: log`. The extra stored decimals preserve small early values even when
fixed two-decimal formatting would show `0.00`; consumers may need more digits
in tooltips. Only months present in both inputs are emitted.

The generated Bitcoin JSON and CSV are git-ignored because the source has no
open licence recorded. A full build still writes them locally. See
[Bitcoin data](sources.md#bitcoin-data) before distributing them.

Implementation: [src/market_trends/trends/btc_in_gold.py](https://github.com/NimbleOx/market-trends/blob/main/src/market_trends/trends/btc_in_gold.py).

## buffett-indicator

```text
value = (NCBEILQ027S / 1,000) / GDP × 100
```

`NCBEILQ027S` is nonfinancial corporate equity value in millions of dollars;
division by 1,000 converts it to the billions used by `GDP`. The numerator is
a quarter-end stock, while GDP is a quarterly flow expressed at a seasonally
adjusted annual rate. The result is a percentage of annualised GDP, not of
spending during that quarter alone. See the FRED definitions for
[`NCBEILQ027S`](https://fred.stlouisfed.org/series/NCBEILQ027S) and
[`GDP`](https://fred.stlouisfed.org/series/GDP).

This construction includes publicly traded and closely held nonfinancial
corporations. It excludes financial corporations, so its coverage differs
from a total-market stock index. Neither the level nor the path should be
assumed identical to another chart labelled “Buffett indicator.” The
[Federal Reserve's series breakdown](https://www.federalreserve.gov/apps/fof/SeriesAnalyzer.aspx?s=FL103164105&t=)
describes the equity components.

Implementation: [src/market_trends/trends/buffett_indicator.py](https://github.com/NimbleOx/market-trends/blob/main/src/market_trends/trends/buffett_indicator.py).

## corporate-profit-share

```text
value = CP / GDP × 100
```

Both inputs are billions of dollars at seasonally adjusted annual rates, so
no conversion is needed. `CP` is after-tax corporate profits **without**
inventory valuation and capital consumption adjustments. Use this exact series
when reproducing the calculation; other BEA profit measures give different
results. See the [FRED definition of CP](https://fred.stlouisfed.org/series/CP).

This is the profit component of the decomposition below. Its corporate profit
coverage is broader than the nonfinancial equity numerator used by the
Buffett indicator; the identity is algebraic, not a claim that their sectors
match exactly.

Implementation: [src/market_trends/commentary/why_the_buffett_indicator_keeps_rising/corporate_profit_share.py](https://github.com/NimbleOx/market-trends/blob/main/src/market_trends/commentary/why_the_buffett_indicator_keeps_rising/corporate_profit_share.py).

## market-value-per-dollar-of-profit

```text
value = (NCBEILQ027S / 1,000) / CP
```

The result is dollars of nonfinancial corporate equity value per dollar of
annualised after-tax corporate profit. It is an aggregate valuation ratio,
not the P/E ratio of an index or a set of companies with matching earnings.
It can change when equity values change, profits change, or both.

On dates shared by all three series, using the same source observations:

```text
buffett-indicator ≈ corporate-profit-share × market-value-per-dollar-of-profit
```

The equality holds before rounding. Both percentage series use percent units,
so no additional factor of 100 is needed in this expression. Independently
refreshed inputs can break the comparison; use the same cached responses for
all three builders.

Implementation: [src/market_trends/commentary/why_the_buffett_indicator_keeps_rising/market_value_per_dollar_of_profit.py](https://github.com/NimbleOx/market-trends/blob/main/src/market_trends/commentary/why_the_buffett_indicator_keeps_rising/market_value_per_dollar_of_profit.py).

## federal-deficit-share

```text
value = (FGEXPND − FGRECPT) / GDP × 100
```

All inputs are billions of dollars at seasonally adjusted annual rates. The
result is positive for a deficit and negative for a surplus. It compares
federal **current** expenditures and receipts on the National Income and
Product Accounts basis. It is not the unified federal budget deficit or a
fiscal-year total. Definitions: [`FGEXPND`](https://fred.stlouisfed.org/series/FGEXPND)
and [`FGRECPT`](https://fred.stlouisfed.org/series/FGRECPT).

The shared national-accounts basis makes this useful beside the profit share.
The comparison does not establish that a change in the federal deficit caused
an equal change in corporate profits. A quarterly annual-rate ratio can also
differ substantially from the deficit measured across a full fiscal year.

Implementation: [src/market_trends/commentary/why_the_buffett_indicator_keeps_rising/federal_deficit_share.py](https://github.com/NimbleOx/market-trends/blob/main/src/market_trends/commentary/why_the_buffett_indicator_keeps_rising/federal_deficit_share.py).

## effective-tariff-rate

```text
annualised imports = mean(BOPGIMP for the quarter's 3 months) × 12 / 1,000
value = B235RC1Q027SBEA / annualised imports × 100
```

[`B235RC1Q027SBEA`](https://fred.stlouisfed.org/series/B235RC1Q027SBEA)
is customs duties in billions of dollars at a seasonally adjusted annual
rate. [`BOPGIMP`](https://fred.stlouisfed.org/series/BOPGIMP) is monthly
goods imports in millions of dollars, seasonally adjusted. The conversion
puts the denominator on the same annual-rate and dollar-unit basis.

The builder groups import rows into calendar quarters and keeps only groups
with exactly three observations. It assumes the upstream supplies one row per
month; it does not separately verify three distinct months. A retained quarter
must also have a duties observation and a positive imports denominator.

This is an aggregate collections-to-imports ratio. Product mix, exemptions,
timing, and sourcing changes can make it differ from announced tariff rates;
it is not the rate charged on every shipment.

Implementation: [src/market_trends/commentary/analyzing_the_effects_of_tariffs_on_prices_and_inflation.py](https://github.com/NimbleOx/market-trends/blob/main/src/market_trends/commentary/analyzing_the_effects_of_tariffs_on_prices_and_inflation.py).

## Shared calculation and display conventions

- **Dates identify periods.** Monthly rows use the first day of the month;
  quarterly rows use January 1, April 1, July 1, or October 1. A period-start
  label does not imply a first-day measurement: the equity numerator is a
  quarter-end value.
- **Joins use exact dates.** After any source aggregation, a builder keeps
  only dates present in every required input. It drops missing dates and
  nonpositive denominators rather than filling them. Coverage may have gaps,
  including early equity data with only annual observations.
- **Aggregation follows the inputs.** GDP-based ratios remain quarterly;
  daily Bitcoin readings become monthly averages; monthly imports become
  quarterly annualised values. Historical gold already contains annual values
  repeated into monthly rows upstream, as described above.
- **Storage and display differ.** All ratios except Bitcoin are rounded to
  four decimal places. `precision` requests display decimals; it does not
  control calculation rounding. The quarterly series request one display
  decimal and a linear scale.
- **Validation has a limited role.** It checks series structure and values,
  not the economic interpretation, source units, complete periods, or release
  freshness. See [Output](output.md) for the checks and
  [Development](development.md) for the tests.
