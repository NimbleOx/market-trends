# Contributing

This project does not accept contributions.

It exists to open-source the code and data behind the charts at
[jameswarrick.com/money/trends/](https://www.jameswarrick.com/money/trends/),
so that anyone can see exactly how each series is computed, where every number
comes from, and under what terms. It is a personal project published for
transparency, not a community one. Pull requests will be closed, and feature
requests will not be taken up.

## If you fork it

The code is MIT, so you are free to take it and change it. The rest of this
file is what I would want to know on day one. Setup, checks, CI and the docs
build are on the
[Development page](https://nimbleox.github.io/market-trends/development/).

### Adding a series

1. Write `src/market_trends/series/<name>.py` with an `ID` and a `build()` that
   returns a `Series`. `buffett_indicator.py` is the shape for a quarterly ratio,
   `sp500_in_gold.py` for a monthly one.
2. Register it in `src/market_trends/registry.py`. That is the only list; the
   CLI, the tests and `dist/index.json` all read from it.
3. Open the module with a docstring that says what the series measures and why
   it is built this way, including any tradeoff a reader would otherwise have to
   rediscover. The `description` field is the shorter version shown beside the
   chart, so it should stand on its own.
4. Choose `precision` and `scale` for the series rather than for a chart. A
   series spanning several orders of magnitude wants `scale="log"`, and
   `validate()` refuses a log series carrying a zero or negative value.
5. Add a value assertion to `tests/test_series.py` at a turning point the chart
   exists to show. That is what catches a units mistake or a bad join later.
6. Run `trends build` and commit the regenerated `dist/` together with the code.

Do not resample a source to a finer frequency than it has. GDP is quarterly, so
anything divided by GDP is quarterly; interpolating up would invent detail.

### Adding a source

1. Settle the licence first. Every `Source` carries one and `validate()` refuses
   `unknown`. If you cannot find a statement of terms, the answer is a different
   source, not a placeholder.
2. Decide whether the raw response may be redistributed. `fetch()` requires
   `redistributable=` and files the response under `cache/open` or
   `cache/restricted`. Neither is committed, but the split governs what may
   leave the repo: a series derived from a restricted source is git-ignored in
   `dist/` and rebuilt by a clone, as `btc-in-gold` is.
3. For a FRED series, add it to `LICENCES` in `sources/fred.py`. FRED
   redistributes other people's data under their terms, so the licence belongs
   to the series id, not to FRED.
4. Prefer a URL that does not carry a release year or a build hash in its path.
   The `datasets` org on GitHub is worth checking before the original publisher;
   the README says why.
