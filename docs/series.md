# Series

This page documents nine maintained trends and four commentary ratios.
Each builder transforms or combines upstream observations and returns a
`Series` with its source records and display metadata. A build writes
`series/<id>.json` and `series/<id>.csv` under the output directory.
See [Output](output.md) for the file format and
[Sources and licences](sources.md) for reuse terms.

The trend registry contains `sp500-in-gold`, `btc-in-gold`,
`buffett-indicator`, `federal-deficit`, `federal-deficit-gdp`,
`federal-deficit-monthly`, `federal-deficit-ttm`, `labor-share-gdi`, and `capital-share-gdi`.
The other four ratios belong to commentary article groups
and are emitted under `dist-commentary/`. The daily Treasury commentary pair
is documented with its [article group](article-series.md#commentary-groups).

| ID | Measures | Frequency | History starts¹ | Scale | Catalogue |
| --- | --- | --- | --- | --- | --- |
| [`sp500-in-gold`](#sp500-in-gold) | S&P Composite index relative to gold | monthly | 1871-01 | linear | Trends |
| [`btc-in-gold`](#btc-in-gold) | Gold equivalent of one bitcoin | monthly | 2010-09 | log | Trends |
| [`buffett-indicator`](#buffett-indicator) | Nonfinancial corporate equity value / GDP | quarterly | 1947 Q4 | linear | Trends |
| [`federal-deficit`](#federal-deficit) | Federal budget deficit in current dollars | annual (fiscal year) | FY1901 | linear | Trends |
| [`federal-deficit-gdp`](#federal-deficit-gdp) | Federal budget deficit / fiscal-year GDP | annual (fiscal year) | FY1930 | linear | Trends |
| [`federal-deficit-monthly`](#federal-deficit-monthly) | Actual monthly federal budget deficit in current dollars | monthly | 1980-10 | linear | Trends |
| [`federal-deficit-ttm`](#federal-deficit-ttm) | Trailing 12-month federal budget deficit in current dollars | monthly | 1981-09 | linear | Trends |
| [`labor-share-gdi`](#labor-share-gdi) | Nominal employee compensation / gross domestic income | quarterly | 1947 Q1 | linear | Trends |
| [`capital-share-gdi`](#capital-share-gdi) | Adjusted corporate profits before tax / gross domestic income | quarterly | 1947 Q1 | linear | Trends |
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

## federal-deficit

```text
value = −FYFSD / 1,000
```

OMB's [`FYFSD`](https://fred.stlouisfed.org/series/FYFSD), hosted by FRED,
records federal budget surpluses as positive and deficits as negative, in
millions of current dollars. Negation makes deficits positive and surpluses
negative; division by 1,000 converts to billions. Stored values preserve
million-dollar detail with three decimals, and `precision: 1` requests one
decimal place for display. These are nominal dollars, without inflation
adjustment. An annual deficit is a flow, not the stock of federal debt.

The history begins in FY1901. Both annual budget series use historical actuals
from their source; neither adds budget projections or a partial current year.
Observation dates remain fiscal-year ends: June 30 through FY1976 and
September 30 from FY1977. The separate July–September 1976 transition quarter
is excluded from these annual inputs. The optional `dateBasis: "fiscal-year"`
metadata tells consumers to label observations as fiscal years. See the
[OMB Historical Tables introduction](https://www.whitehouse.gov/wp-content/uploads/2026/04/hist_intro_fy2027.pdf)
for the fiscal-year convention and historical-table definitions.

These unified-budget balances differ from the BEA national-accounts current
expenditure/receipt gap in commentary's [federal-deficit-share](#federal-deficit-share).

Implementation: [src/market_trends/trends/federal_deficit.py](https://github.com/NimbleOx/market-trends/blob/main/src/market_trends/trends/federal_deficit.py).

## federal-deficit-gdp

```text
value = −FYFSDFYGDP
```

[`FYFSDFYGDP`](https://fred.stlouisfed.org/series/FYFSDFYGDP) is OMB's federal
budget surplus or deficit as a percentage of **fiscal-year GDP**. Negate the
published percentage directly, keeping its stored precision, so deficits are
positive and surpluses are negative. The result has `precision: 1` and begins
in FY1930; no values are inferred before the source starts. This is a separate
history from the longer dollar series, not a join with quarterly GDP.

Do not substitute the similarly named FRED `FYFSGDA188S`: its denominator is
calendar-year GDP. Fiscal-year dates, actuals coverage, and the omitted 1976
transition quarter follow [federal-deficit](#federal-deficit). Both series use
a linear scale so budget surpluses can appear below zero.

Implementation: [src/market_trends/trends/federal_deficit.py](https://github.com/NimbleOx/market-trends/blob/main/src/market_trends/trends/federal_deficit.py).

## federal-deficit-monthly

```text
value = −MTSDS133FMS / 1,000
```

Treasury's Monthly Treasury Statement, hosted by FRED as
[`MTSDS133FMS`](https://fred.stlouisfed.org/series/MTSDS133FMS), records the
actual federal surplus or deficit for each month in millions of current
dollars. Negate and divide by 1,000 to express deficits as positive and
surpluses as negative, in billions. Stored values are rounded to six decimals;
`precision: 1` requests one decimal for display. This is the nominal cash
balance of the unified budget, without inflation or seasonal adjustment.

The history begins in October 1980. Dates use the first day of the reference
month and have no fiscal-year `dateBasis` metadata. Each observation is that
month's actual balance, not an annualized rate or an interpolated annual value.
Missing months are not filled. Completed months remain valid even when the
fiscal year is incomplete, so this series can extend beyond the annual actuals.
Tax-payment deadlines and payment timing contribute to substantial month-to-month
changes, including seasonal surpluses.

Monthly Treasury Statement sums can differ from OMB's revised annual history
because source vintages and accounting adjustments differ. For example, the
September 2026 snapshot's FY2025 monthly sum is $1,775.711461 billion, while
`FYFSD` reports $1,774.684 billion. Each series preserves its own source;
the builder does not force the monthly values to reconcile to the annual total.

Implementation: [src/market_trends/trends/federal_deficit.py](https://github.com/NimbleOx/market-trends/blob/main/src/market_trends/trends/federal_deficit.py).

## federal-deficit-ttm

```text
value(t) = sum(federal-deficit-monthly for months t−11 through t)
```

The trailing-year total sums twelve consecutive signed observations from
[`federal-deficit-monthly`](#federal-deficit-monthly), including the current
reference month. It preserves the nominal billions-of-dollars units and source
attribution. `math.fsum` computes each total, then the builder rounds to six
decimals; `precision: 1` requests one decimal for display. Deficits remain
positive and surpluses negative, on a linear scale.

Each point covers a complete twelve-month span, recalculated monthly. Initial
windows with fewer than twelve months are omitted. Windows crossing a missing
month are also omitted until twelve consecutive observations are available
again; twelve rows spread over thirteen calendar months are not a valid year.
The calculation uses full history before any chart range filtering and never
uses future months. Dates label the final reference month, with no fiscal-year
`dateBasis` metadata. The first complete window ends in September 1981.

This smooths the repeating calendar cycle by including each calendar month
once. It is a trailing-year total, **not an official seasonally adjusted
monthly estimate**. It can lag turning points, and exceptional payment shifts
can remain visible. As with the underlying monthly data, source vintages and
accounting adjustments mean a twelve-month Treasury sum can differ from OMB's
annual history, even when the period ends in September.

Implementation: [src/market_trends/trends/federal_deficit.py](https://github.com/NimbleOx/market-trends/blob/main/src/market_trends/trends/federal_deficit.py).

## labor-share-gdi

```text
value = COE / GDI × 100
```

Labor's share of gross domestic income uses BEA's nominal employee compensation
[`COE`](https://fred.stlouisfed.org/series/COE), account code `A033RC`, divided by
nominal [`GDI`](https://fred.stlouisfed.org/series/GDI). Both inputs are quarterly
flows in billions of current dollars at seasonally adjusted annual rates.
Their units and annualisation cancel, so no dollar conversion or inflation
adjustment is needed.

Employee compensation includes wages and salaries plus employer contributions
for pensions, insurance, and government social insurance. It does not add an
estimate of labor income earned by the self-employed, whose earnings are
recorded separately as proprietors' income. This employee-compensation measure
can therefore differ from labor-share estimates that include self-employment.
See BEA's [compensation definition](https://www.bea.gov/help/glossary/compensation-employees)
and [NIPA handbook, chapter 10](https://www.bea.gov/sites/default/files/methodologies/nipa-handbook-all-chapters.pdf).

The builder keeps matching quarters with a positive GDI denominator, beginning
in 1947 Q1. Dates retain FRED's quarter-start labels: `1947-01-01` denotes all
of 1947 Q1. The output retains the full history; a consuming chart chooses its
display window. Stored ratios are rounded to four decimals, with
`unit: "percent of GDI"`, `precision: 1`, and a linear scale. GDI and GDP have
different measured values, so substituting GDP changes this series.

Implementation: [src/market_trends/trends/labor_share_gdi.py](https://github.com/NimbleOx/market-trends/blob/main/src/market_trends/trends/labor_share_gdi.py).

## capital-share-gdi

```text
value = CPROFIT / GDI × 100
```

Capital's share of gross domestic income uses BEA's corporate profits **before
tax, with inventory valuation and capital consumption adjustments**,
[`CPROFIT`](https://fred.stlouisfed.org/series/CPROFIT), account code `A051RC`,
divided by nominal [`GDI`](https://fred.stlouisfed.org/series/GDI). Both inputs
are quarterly flows in billions of current dollars at seasonally adjusted
annual rates, so their units and annualisation cancel.

This is a corporate-profits proxy for capital's share. It does not include all
capital income or all non-labor income: rental income, net interest, and
proprietors' income are separate components. It is **not** `100 − labor-share-gdi`,
and the two measures do not sum to 100. Read the numerator's coverage literally
when comparing these charts. BEA's [NIPA Table 1.12, via FRED](https://fred.stlouisfed.org/release/tables?eid=15372&rid=53)
shows these components separately and splits adjusted corporate profits into
corporate income taxes and after-tax adjusted profits. The commentary series
[`corporate-profit-share`](#corporate-profit-share) uses a different numerator
(`CP`, after-tax profits without these adjustments) and denominator (`GDP`).

The builder keeps every matching quarter with positive GDI, starting in 1947 Q1,
without filling gaps or truncating history. Dates preserve upstream quarter-start
labels; `1947-01-01` denotes 1947 Q1. Stored ratios are rounded to four decimal
places and displayed with `precision: 1`, `unit: "percent of GDI"`, and a linear
scale. Chart consumers choose the display window.

Implementation: [src/market_trends/trends/capital_share_gdi.py](https://github.com/NimbleOx/market-trends/blob/main/src/market_trends/trends/capital_share_gdi.py).

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
  quarter-end value. Annual federal budget observations retain fiscal-year ends.
- **Joins use exact dates.** After any source aggregation, a builder keeps
  only dates present in every required input. It drops missing dates and
  nonpositive denominators rather than filling them. Coverage may have gaps,
  including early equity data with only annual observations.
- **Aggregation follows the inputs.** Quarterly GDP- and GDI-based ratios remain quarterly;
  daily Bitcoin readings become monthly averages; monthly imports become
  quarterly annualised values. Historical gold already contains annual values
  repeated into monthly rows upstream, as described above. Annual federal
  budget balances and the fiscal-year GDP share remain annual. Monthly budget
  balances remain actual monthly flows, without seasonal adjustment or annualization.
  The trailing-year series sums twelve consecutive monthly balances for each point.
- **Storage and display differ.** Most ratios are rounded to four decimal
  places; Bitcoin and the monthly and trailing-year federal budget balances use six, while the
  annual federal budget GDP share preserves the upstream decimals and the
  annual dollar series preserves million-dollar detail.
  `precision` requests display decimals; it does not
  control calculation rounding. The quarterly series request one display
  decimal and a linear scale.
- **Validation has a limited role.** It checks series structure and values,
  not the economic interpretation, source units, complete periods, or release
  freshness. See [Output](output.md) for the checks and
  [Development](development.md) for the tests.
