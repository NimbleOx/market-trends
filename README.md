# market-trends

[![ci](https://github.com/NimbleOx/market-trends/actions/workflows/ci.yml/badge.svg)](https://github.com/NimbleOx/market-trends/actions/workflows/ci.yml)
[![docs](https://img.shields.io/badge/docs-mkdocs-blue)](https://nimbleox.github.io/market-trends/)

Computes the long-run financial series published at
[jameswarrick.com/money/trends/](https://www.jameswarrick.com/money/trends/) and elsewhere on [jameswarrick.com](https://www.jameswarrick.com).

This repo emits **data**, not charts. Any charts would be constructed selerately from this data.

This repo is written heavily by AI, although I have made efforts to validate that the data being produced is valid.

```bash
uv venv && uv pip install -e ".[dev]"

trends list          # what this repo publishes
trends check         # compute everything, write nothing
trends build         # compute everything, write dist/
TRENDS_REFRESH=1 trends build   # ignore the cache and refetch
```

Activate the venv first, or prefix each command with `uv run`. Install editable
and run from the checkout: `cache/` and `dist/` are found relative to the source
tree, not the working directory.

## What it publishes

| Series | Measures | Frequency | From |
| --- | --- | --- | --- |
| `sp500-in-gold` | The S&P Composite divided by the price of gold | monthly | 1871 |
| `btc-in-gold` | Bitcoin divided by the price of gold | monthly | 2010 |
| `buffett-indicator` | US corporate equities as a share of GDP | quarterly | 1947 |
| `corporate-profit-share` | After-tax corporate profits as a share of GDP | quarterly | 1947 |
| `market-value-per-dollar-of-profit` | Corporate equities divided by after-tax profits | quarterly | 1947 |
| `federal-deficit-share` | Federal expenditures less receipts, as a share of GDP | quarterly | 1947 |
| `effective-tariff-rate` | Customs duties as a share of goods imports | quarterly | 1992 |

Each lands in `dist/series/<id>.json`, with a CSV of the observations beside
it, and `dist/index.json` lists them all.
Every series module opens with a docstring saying why it is built the way it
is, including the tradeoffs; the `description` field in the JSON is the shorter
version the site shows beside the chart.

## Layout

| Path | What lives there |
| --- | --- |
| `src/market_trends/sources/` | How to get numbers out of one upstream. One module per feed. |
| `src/market_trends/series/` | How to make one published series out of sources. One module per series. |
| `src/market_trends/registry.py` | The list of series the build publishes. A series is added here and nowhere else. |
| `src/market_trends/schema.py` | The contract, and the checks that enforce it before anything is written. |
| `src/market_trends/emit.py` | Writes `dist/`. One observation per line, so a revision reads as a one-line diff. |
| `src/market_trends/cli.py` | `trends build`, `trends check`, `trends list`. |
| `cache/` | Raw upstream responses. Never committed; a clone refetches. See `cache/README.md`. |
| `docs/` | The [docs site](https://nimbleox.github.io/market-trends/), built with MkDocs. The CLI page is the one to read first. |
| `dist/` | The published output: JSON with provenance, and CSV with the numbers alone. The site vendors the JSON. |

Keeping `sources/` and `series/` apart means swapping a gold price feed touches
one file and no series logic.

## Licensing is a per-source decision

Every `Source` carries a `licence`, and `validate()` refuses to publish a series
whose source says `unknown`. That is deliberate: the point of the field is that
somebody decided, not that a string exists.

No upstream data is committed. Everything under `cache/` is refetched on a
fresh clone, which keeps this repo from being the system of record for numbers
it did not produce, and from redistributing a source whose terms may not allow
it. Every source below is independently retrievable from its own upstream, and
`pytest -m network` builds the whole set from an empty cache to prove it.

The `open`/`restricted` split still records which sources *could* be
redistributed. It no longer decides what ships, but it is a required argument to
`fetch()`, so a new source cannot skip the decision — and it governs what may
leave this repo downstream.

Current sources:

| Source | Used for | Licence | Class |
| --- | --- | --- | --- |
| `datasets/s-and-p-500` | S&P Composite, monthly since 1871 (Shiller) | ODC-PDDL-1.0 | open |
| `datasets/gold-prices` | Gold, monthly since 1833 | ODC-PDDL-1.0 | open |
| FRED `NCBEILQ027S` (Fed Z.1) | Corporate equities | Public domain | open |
| FRED `GDP` (BEA) | GDP | Public domain | open |
| FRED `CP` (BEA) | Corporate profits after tax | Public domain | open |
| FRED `FGRECPT` (BEA) | Federal current receipts | Public domain | open |
| FRED `FGEXPND` (BEA) | Federal current expenditures | Public domain | open |
| FRED `B235RC1Q027SBEA` (BEA) | Customs duties | Public domain | open |
| FRED `BOPGIMP` (Census) | Goods imports, balance of payments basis | Public domain | open |
| blockchain.com charts API | Bitcoin market price, daily since 2010 | No open licence stated | restricted |

Bitcoin is the one restricted source. blockchain.com states no open licence,
only its general terms, so what this repo publishes from it is a *ratio* rather
than their prices — and even those computed files, `dist/series/btc-in-gold.json`
and its CSV, are git-ignored and rebuilt by a clone rather than shipped in one.
The series code is public; the numbers come from upstream on your own machine.

Gold used to come from the World Bank Pink Sheet directly. Two reasons it does
not now: the Pink Sheet URL carries the release year in its path, so a hardcoded
link keeps serving last year's file rather than 404ing, and the datasets copy
reaches back to 1833 instead of 1960 — which is what lets sp500-in-gold start
where Shiller's prices do.

## Where to look for data

[github.com/orgs/datasets/repositories](https://github.com/orgs/datasets/repositories?type=all)
is worth checking before going hunting. The org maintains cleaned, versioned
copies of a lot of standard economic and financial series, each with a
`datapackage.json` declaring a licence and a history of automated commits, which
means an upstream revision arrives as a readable diff rather than a number that
silently changed. `s-and-p-500` is where the equity side of sp500-in-gold comes
from.

They publish the same data to datahub.io. Prefer the GitHub repo: identical
bytes, but the licence is machine-readable and the history is visible.

## Tests

```bash
ruff check src tests      # lint
pytest -m "not network"   # schema, emit, formatting
pytest -m network         # builds every series against the cache or live upstreams
```

The network-marked tests include value assertions against turning points the
charts exist to show — the 1982 trough, the dot-com peak, 2009, 2021 — so a
units mistake or a bad join fails loudly rather than shifting a level quietly.

CI runs the lint and the no-network tests on every push and pull request to
`main`, and the network tests weekly against the live upstreams so a moved URL
surfaces before it breaks somebody's fresh clone.

The docs site is MkDocs: `uv pip install -e ".[docs]"` then `mkdocs serve` to
preview it. CI builds it with `--strict` and deploys it to GitHub Pages from
`main`. The [Development page](https://nimbleox.github.io/market-trends/development/)
has the longer version.

## Contributing

This project does not accept contributions. It exists to open-source the code
and data behind the charts on my site, so the computation and the provenance of
every number are open to inspection. [CONTRIBUTING.md](CONTRIBUTING.md) says
so at more length, and carries the notes you would want if you fork it.

## Licence

Two different things live here and they are not under the same terms.

**The code** — everything in `src/` and `tests/` — is MIT. See `LICENSE`.

**The data** in `dist/` is not mine to relicense. Each series carries its own
provenance: every emitted JSON has a `sources` array naming the upstream, its
URL, and its licence, which is the authoritative statement for that series.
`validate()` refuses to publish a series whose source licence is `unknown`, so
the field is never decoration. The CSV beside each JSON carries the same numbers
under the same terms; it has no room to say so itself, which is why the JSON is
the record. If you reuse a series, honour the terms recorded in its JSON — for
the current set that means ODC-PDDL-1.0 and US public domain, which between them
ask for little beyond attribution.
