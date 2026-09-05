# market-trends

[![ci](https://github.com/NimbleOx/market-trends/actions/workflows/ci.yml/badge.svg)](https://github.com/NimbleOx/market-trends/actions/workflows/ci.yml)
[![docs](https://img.shields.io/badge/docs-mkdocs-blue)](https://nimbleox.github.io/market-trends/)

Build maintained market trends and commentary datasets as JSON and CSV. This
repository contains the calculations and source metadata behind the charts at
[jameswarrick.com/markets/](https://www.jameswarrick.com/markets/).
Use the output in a chart, a dataframe, or another application; chart rendering
lives in the consuming application.

Commentary datasets are grouped by article in a separate catalogue. Discover
them with `trends articles groups` and generate them with `trends articles build`.
Each article has fixed default dates in this project, with optional `--from` and
`--to` overrides.
See [Article series](docs/article-series.md) for the workflow, output contract,
and how to add a dataset. Ordinary trend builds write `dist-trends/`; article builds
write `dist-commentary/`.

## Quick start

You need **Python 3.11 or later**, Git, and
[uv](https://docs.astral.sh/uv/getting-started/installation/). The commands below
use Bash or Zsh on macOS, Linux, or WSL. For Windows PowerShell or installation
with standard `pip`, see [Development](docs/development.md#set-up-a-checkout).

```bash
git clone https://github.com/NimbleOx/market-trends.git
cd market-trends
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"

trends list
trends build
```

The first build downloads the upstream data, computes and validates the three
maintained trends, and writes **7 files**: three JSON files, three CSV files, and an index.
It needs internet access; the current adapters do not require API keys. Later
builds reuse the local cache until you request a refresh.

Keep the editable installation (`-e`) and the checkout together. The default
`cache/` and `dist-trends/` paths are resolved from the source tree, even when you run
`trends` from another directory. See the [CLI reference](docs/cli.md) for custom
output paths and troubleshooting.

## Read the output

You can inspect the two trend series committed under `dist-trends/` immediately after
cloning. To generate all three trend series locally, run the full build above.

After a successful full build:

```text
dist-trends/
├── index.json                    # Available series and relative file paths
└── series/
    ├── sp500-in-gold.json         # Metadata, sources, and observations
    ├── sp500-in-gold.csv          # date,value rows
    └── ...                       # The other two trend series, in both formats
```

For example, run this Python code from the checkout root:

```python
import json
from pathlib import Path

series = json.loads(Path("dist-trends/series/sp500-in-gold.json").read_text(encoding="utf-8"))
print(series["title"], series["unit"])
print(series["observations"][-1])  # {"date": "YYYY-MM-DD", "value": ...}
```

The [output reference](docs/output.md) documents every field, date conventions,
timestamps, and CSV loading. Keep each CSV with its JSON: source and licence
metadata appear only in the JSON.

The repository includes generated files for two trend series and all six
commentary datasets. Bitcoin output is git-ignored under the project's data
policy, so a fresh clone's index can refer
to missing Bitcoin files until you run a full build.

## Maintained trends

| ID | Measure | Frequency | History begins |
| --- | --- | --- | --- |
| `sp500-in-gold` | S&P Composite index divided by the gold price | Monthly | 1871 |
| `btc-in-gold` | Bitcoin price divided by the gold price | Monthly | 2010 |
| `buffett-indicator` | Nonfinancial corporate equity value as a percentage of GDP | Quarterly | 1947 |

See [Series](docs/series.md) for formulas, units, joins, rounding, and limitations.
In particular, gold prices before 1960 repeat annual averages in monthly rows;
the monthly output does not imply monthly gold price detail for that period.

## Commentary groups

| Article | Commentary datasets | Shared trend |
| --- | --- | --- |
| Analyzing the Effects of Tariffs on Prices and Inflation | `effective-tariff-rate` | — |
| Uncle Sam Has Competition | `treasury-10-year-yield-2026`, `treasury-30-year-yield-2026` | — |
| Why the Buffett Indicator Keeps Rising | `corporate-profit-share`, `federal-deficit-share`, `market-value-per-dollar-of-profit` | `buffett-indicator` |

```bash
trends articles groups
trends articles check --article why-the-buffett-indicator-keeps-rising
trends articles build
```

The commentary index records these groups. Shared trends remain in
`dist-trends/`; commentary builds do not duplicate them. Default inclusive windows
are hard-coded per article in `src/market_trends/commentary/registry.py` and shown
by `trends articles groups`. Override either bound with `--from YYYY-MM-DD` or
`--to YYYY-MM-DD`; omitted bounds retain that article's defaults. Treasury
builds fetch each calendar year in the window; quarterly ratios are calculated
before filtering observations by their period dates. See [Article series](docs/article-series.md) for selecting groups,
importing both collections, and migrating from the former mixed trend output.

## Common commands

Run these with the virtual environment active:

```bash
trends list                                      # List registered series IDs
trends check                                     # Compute and validate; leave dist-trends/ untouched
trends check --only sp500-in-gold                  # Check one series
trends build --only sp500-in-gold --out /tmp/trends-preview
TRENDS_REFRESH=1 trends build                     # Download fresh inputs and rebuild dist-trends/
```

`check` can download and update cached inputs. It skips writing output files.
Cached responses have no automatic expiry, and an ordinary check does not
establish that the upstream data is current or reachable.

**Use a separate output directory for partial builds.** A build replaces the
index and removes JSON and CSV files in its `series/` directory that were not
produced by that run. `--only` therefore removes unselected series from that
output directory. The [CLI reference](docs/cli.md) explains refresh behavior,
failure modes, and exit codes.

## Work on the code

```bash
ruff check src tests
pytest -m "not network"
```

The offline tests check the schema and emitted files. After changing a source
adapter or a calculation, also run `pytest -m network`: it checks every series,
includes historical value assertions, and exercises downloads into empty
temporary caches. It requires network access even if your checkout's cache is
full.

| Path | Responsibility |
| --- | --- |
| [`src/market_trends/sources/`](src/market_trends/sources/) | Fetch and parse upstream responses; attach source metadata. |
| [`src/market_trends/trends/`](src/market_trends/trends/) | Join inputs and compute maintained trends; module docstrings explain the methodology. |
| [`src/market_trends/commentary/`](src/market_trends/commentary/) | Build commentary datasets grouped by article, with fixed default date windows and optional overrides. |
| [`registry.py`](src/market_trends/registry.py) | Register builders used by the CLI and generic series tests. |
| [`schema.py`](src/market_trends/schema.py) | Define Python data objects, validation, and the JSON shape. |
| [`emit.py`](src/market_trends/emit.py) | Write JSON, CSV, and the index; remove stale series files. |
| [`cli.py`](src/market_trends/cli.py) | Parse commands and coordinate computation, validation, and output. |
| [`cache/`](cache/README.md) | Store downloaded responses locally; raw data files are git-ignored. |
| [`tests/`](tests/) | Check validation, serialization, and calculations. |
| [`docs/`](docs/index.md) | Source for the MkDocs documentation site. |
| [`dist-trends/`](dist-trends/) | Generated data for downstream consumers. |
| [`dist-commentary/`](dist-commentary/) | Generated article JSON, CSV, and index, separate from trend output. |

The [development guide](docs/development.md) covers adding a series or source,
reviewing data changes, running CI checks locally, and previewing the docs.

## Data sources and licences

The code is licensed under [MIT](LICENSE). Upstream data has separate terms,
recorded in each series' JSON `sources` array. See
[Sources and licences](docs/sources.md) for the source inventory, upstream links,
and the distinction between recorded licence metadata and reuse permission.

Raw upstream responses are never committed. The `open` and `restricted` cache
directories record the project's classification of each source; the cache
flag does not enforce restrictions on generated output. Bitcoin JSON and CSV
are excluded explicitly in `.gitignore`.

## Project policy

This is a personal project published for transparency. It does not accept
contributions; pull requests will be closed and feature requests will not be
taken up. See [CONTRIBUTING.md](CONTRIBUTING.md) for the policy and links for
working on a fork.

Much of the code was written with AI assistance. The repository includes
validation and selected historical checks to help inspect the results; these
checks do not independently verify every observation.
