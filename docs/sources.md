# Sources and licences

Each generated series JSON records its upstream sources in `sources`, with a
name, URL, licence description, and `retrievedAt` date. Keep this JSON with
the companion CSV when reusing the observations: the CSV contains only
`date,value` rows and no provenance.

The code is MIT-licensed. That licence does not grant rights to upstream data.
The source fields document this project's recorded decisions; the upstream
terms remain the basis for assessing a particular use.

## Source inventory

The cache column shows where the **current implementation** stores responses.
It is a routing decision, not an independent verification of rights. External
references on this page were reviewed on 4 September 2026.

| Input | Provider and use | Recorded licence | Cache |
| --- | --- | --- | --- |
| [`datasets/s-and-p-500`](https://github.com/datasets/s-and-p-500) | Shiller history, extended with FRED S&P 500 prices; equity/gold ratio | `ODC-PDDL-1.0`¹ | `open/` |
| [`datasets/gold-prices`](https://github.com/datasets/gold-prices) | Historical gold and World Bank prices; both gold ratios | `ODC-PDDL-1.0`¹ | `open/` |
| FRED [`NCBEILQ027S`](https://fred.stlouisfed.org/series/NCBEILQ027S) | Federal Reserve; nonfinancial corporate equities | Public domain (US federal government work) | `open/` |
| FRED [`GDP`](https://fred.stlouisfed.org/series/GDP) | BEA; gross domestic product | Public domain (US federal government work) | `open/` |
| FRED [`CP`](https://fred.stlouisfed.org/series/CP) | BEA; after-tax corporate profits, without IVA and CCAdj | Public domain (US federal government work) | `open/` |
| FRED [`FGRECPT`](https://fred.stlouisfed.org/series/FGRECPT) | BEA; federal current receipts | Public domain (US federal government work) | `open/` |
| FRED [`FGEXPND`](https://fred.stlouisfed.org/series/FGEXPND) | BEA; federal current expenditures | Public domain (US federal government work) | `open/` |
| FRED [`B235RC1Q027SBEA`](https://fred.stlouisfed.org/series/B235RC1Q027SBEA) | BEA; customs duties | Public domain (US federal government work) | `open/` |
| FRED [`BOPGIMP`](https://fred.stlouisfed.org/series/BOPGIMP) | Census and BEA; goods imports, balance-of-payments basis | Public domain (US federal government work) | `open/` |
| [Blockchain.com market price](https://www.blockchain.com/explorer/charts/market-price) | Bitcoin prices | No open licence stated; blockchain.com terms | `restricted/` |
| [Daily Treasury Par Yield Curve Rates](https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_yield_curve) | US Treasury; daily nominal par yields | Public domain (US federal government work) | `open/` |

¹ These are the data-package maintainers' declarations. See the limitations
below, particularly the S&P 500 extension.

## Treasury par yields

The Treasury adapter in `src/market_trends/sources/treasury.py` uses annual CSV
exports directly, without FRED or an API key. It supports 10- and 30-year
maturities, selects columns by header, and returns observations in ascending
date order. Values remain in percent, and missing readings are omitted.

Responses are cached as `cache/open/treasury-par-yields-<year>.csv`. The adapter
accepts a year and maturity; individual builders define observation windows
and reference-value checks. Source retrieval is shared infrastructure and does
not determine which output collection a builder belongs to.

## FRED data and service access

The seven FRED inputs above carry the “Public Domain: Citation Requested”
classification on their series pages. FRED hosts data from many providers;
other series can have different restrictions. Cite both the original provider
and FRED when using these records, following the suggested citation on each
series page.

The adapter uses `https://fred.stlouisfed.org/graph/fredgraph.csv?id=<ID>`
and requires no API key. `LICENCES` in `src/market_trends/sources/fred.py`
lists every accepted ID, its source name, licence text, and cache decision.
Requesting an ID absent from that mapping raises `KeyError` before a fetch.

A public-domain data classification does not resolve the terms for accessing
the hosting service. The current FRED terms include restrictions on automated
extraction and caching, with separate provisions for the API. The no-key
fetcher's technical availability is not evidence of permission for a
particular access pattern or downstream use. Review the
[FRED service terms](https://fred.stlouisfed.org/legal/) when assessing or
changing this integration.

## Data packages: declarations and underlying sources

Both `datasets` packages declare PDDL. The
[PDDL text](https://opendatacommons.org/licenses/pddl/1-0/) explains the rights
being dedicated, notes that a party can license only rights it holds, and does
not itself require attribution. Preserve attribution and provenance for
traceability, and check the underlying source terms as well as the package's
declaration.

### S&P Composite prices

The [package README](https://github.com/datasets/s-and-p-500#data) describes
Shiller data through June 2023, followed by an extension using FRED's `SP500`.
Its licence statement also acknowledges that the original Shiller data has no
explicit licence statement. FRED's
[`SP500` notes](https://fred.stlouisfed.org/series/SP500) identify S&P Dow Jones
Indices as the owner and state reproduction restrictions.

The current adapter records only `ODC-PDDL-1.0` and stores this response in
`cache/open/`; that label does not capture these underlying qualifications.
The resulting `sp500-in-gold` files are currently committed. Computing a ratio
does not, by itself, establish permission to redistribute it. This source's
recorded licence and publication policy need to be considered together before
reusing or expanding its distribution.

### Gold prices

The [gold package](https://github.com/datasets/gold-prices) combines historical
records compiled by Timothy Green, originally hosted by the National Mining
Association, with World Bank data from 1960 onward. It provides a CSV and a
longer history than the World Bank series alone. The pre-1960 monthly rows
repeat annual averages; see [Series](series.md#sp500-in-gold) for how this
affects the ratio.

Both adapters fetch GitHub raw files from the packages' `main` branches. Their
repositories expose source-processing code and revision history, but these
URLs are not pinned to a commit. Updates can change existing observations.

## Bitcoin data

The project records no open licence for blockchain.com data. Its
[API terms](https://www.blockchain.com/legal/api-terms) address access, storage,
display, and distribution, and incorporate the
[general terms](https://www.blockchain.com/legal/terms). Neither the presence
of a public endpoint nor converting prices into a ratio is a blanket grant
of redistribution rights.

The raw response goes into `cache/restricted/`. The default output files
`dist-trends/series/btc-in-gold.json` and `dist-trends/series/btc-in-gold.csv` are also
git-ignored. A full build still writes them, and the committed `dist-trends/index.json`
still lists the series even when those files are absent from a fresh clone.
Output in a custom `--out` directory is not covered by those two ignore rules.

Git ignores protect the normal repository workflow; they do not filter a
deployment, upload, archive, or downstream copy. Review the applicable terms
before including Bitcoin-derived output in one of those destinations.

## What is enforced

| Mechanism | What it does | What it does not establish |
| --- | --- | --- |
| `validate()` | Rejects empty licence text and the case-insensitive literal `unknown` | That the licence is accurate, open, or sufficient for reuse |
| FRED `LICENCES` mapping | Rejects unlisted FRED IDs | That a recorded decision remains current |
| Required `redistributable` argument | Routes a raw response to `cache/open/` or `cache/restricted/` | Permission to fetch, publish, or redistribute an output |
| `.gitignore` | Excludes raw cache files and the two default Bitcoin output paths from ordinary Git additions | Protection against forced additions or distribution outside Git |
| Network tests | Exercise builders against live inputs, including temporary empty caches | Source rights, permanent availability, or unrevised historical data |

A restricted-source description is a valid nonempty licence string, so
validation permits `btc-in-gold`. The emitter does not inspect the cache class
or apply a publication filter. Any distribution policy must account for that
behaviour explicitly.

## Cache, freshness, and reproducibility

Raw cache responses are not committed. A fresh clone fetches each required
input on first use; later calls reuse its file unless refresh is requested.
There is no expiry or automatic freshness check. With the project's virtual
environment activated, recompute using the existing cache without writing
output files:

```bash
trends check
```

To fetch again and validate a single series without replacing `dist-trends/`:

```bash
TRENDS_REFRESH=1 trends check --only corporate-profit-share
```

Both commands can write cache files. A refresh replaces each response as it
arrives; there is no snapshot or rollback across inputs. An unchanged cache
and unchanged code preserve the observations, but a fresh clone may fetch
revised history. `generatedAt` changes on each build, and source adapters set
`retrievedAt` to the local build date even for cached responses. That field is
not the original download date or the upstream release date.

The weekly and manually dispatched CI upstream job runs
`uv run pytest -m network -q`. Its empty-cache tests use temporary directories,
so they test live retrieval even when a developer already has a populated
cache. See [Development](development.md) for routine verification and
[Add a source in a fork](development.md#add-a-source-in-a-fork) for extending
the source inventory.
