# Series

Seven series, each computed from two or three upstreams and published as
`dist/series/<id>.json`, with a CSV of the observations beside it. The module
behind each one, under
`src/market_trends/series/`, opens with a docstring saying why it is built the
way it is. This page is the short version.

| Id | Measures | Frequency | From | Scale |
| --- | --- | --- | --- | --- |
| `sp500-in-gold` | The S&P Composite divided by the price of gold | monthly | 1871 | linear |
| `btc-in-gold` | Bitcoin divided by the price of gold | monthly | 2010 | log |
| `buffett-indicator` | US corporate equities as a share of GDP | quarterly | 1947 | linear |
| `corporate-profit-share` | After-tax corporate profits as a share of GDP | quarterly | 1947 | linear |
| `market-value-per-dollar-of-profit` | Corporate equities divided by after-tax profits | quarterly | 1947 | linear |
| `federal-deficit-share` | Federal expenditures less receipts, as a share of GDP | quarterly | 1947 | linear |
| `effective-tariff-rate` | Customs duties as a share of goods imports | quarterly | 1992 | linear |

## sp500-in-gold

The S&P Composite divided by the price of a troy ounce of gold. Dividing one
price by another strips out the dollar both are quoted in, so the line moves
only when equities and gold move relative to each other. Both inputs are
monthly averages. Gold reaches back to 1833 and Shiller's prices to 1871, so
the ratio starts in 1871. The 1980 low and the 2000 high are the two readings
the chart exists to show.

## btc-in-gold

Bitcoin divided by the price of gold, both monthly averages, from the first
month with enough daily prices to average. The ratio spans four orders of
magnitude, so it is published with `scale: log`. It derives from a source with
no open licence, which is why its file is git-ignored and rebuilt by a clone
rather than shipped in one. See [Sources and licences](sources.md).

## buffett-indicator

The market value of US corporate equities as a percentage of GDP. Built from
the Federal Reserve's Z.1 accounts and BEA GDP rather than a proprietary index,
so both inputs are public domain. Z.1 counts all equity issued by nonfinancial
corporate business, listed or not, so the level runs above charts built on a
total-market index. The shape over time is the same. Quarterly, because GDP is.

## corporate-profit-share

After-tax corporate profits as a percentage of GDP. One of the two terms the
Buffett indicator multiplies together: market value over GDP is profits over
GDP times market value over profits. After tax, because that is the figure a
valuation multiple is applied to.

## market-value-per-dollar-of-profit

Corporate equities divided by after-tax profits, which makes it an aggregate
price-to-earnings ratio. The other term in that product, built from the same
two sources so the decomposition is exact: dividing this series into the
Buffett indicator returns the profit share to within rounding.

## federal-deficit-share

Federal current expenditures less current receipts, as a percentage of GDP, on
the national accounts basis rather than the unified budget. Drawn beside the
profit share because one sector's deficit is another sector's surplus. These
are quarterly figures at annual rates, so a single extraordinary quarter reads
far above the fiscal-year deficit for the same period. A deficit is positive
here; the few surpluses cross below zero.

## effective-tariff-rate

Customs duties collected as a percentage of the value of goods imported, by
quarter. This is the rate importers actually paid, which runs well below the
rates announced: exemptions, carve-outs, announced rates that never took effect
and switching to suppliers in untariffed countries all sit between the two.
Monthly imports are averaged and annualised onto the quarterly numerator's
footing. A quarter without all three months is dropped rather than
extrapolated.

## Conventions all of them share

- A series is never resampled finer than its coarsest input. Anything divided
  by GDP is quarterly, because interpolating GDP up to monthly would invent
  detail the source does not have.
- A ratio is computed only on dates both inputs share. A date missing from
  either side is dropped, not filled in.
- `precision` and `scale` travel with the data, because the sensible rendering
  is a property of the series rather than of any one chart.
