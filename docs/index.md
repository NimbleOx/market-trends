# market-trends

Build seven historical financial and economic ratios as JSON and CSV for your
own charts, analysis, or applications. This repository contains the calculations
and source metadata behind the charts at
[jameswarrick.com/money/trends/](https://www.jameswarrick.com/money/trends/).

## Quick start

You need Python 3.11 or later, Git, and
[uv](https://docs.astral.sh/uv/getting-started/installation/). These commands use
Bash or Zsh on macOS, Linux, or WSL; the [development guide](development.md#set-up-a-checkout)
also covers Windows PowerShell and standard `pip`.

```bash
git clone https://github.com/NimbleOx/market-trends.git
cd market-trends
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"

trends list
trends build
```

The first build needs internet access to download its inputs. The current
source adapters do not require API keys. A successful full build produces
`dist/index.json` and one JSON and CSV file for each of the seven series.
JSON includes observations, chart metadata, and sources; CSV contains
`date,value` rows. Chart rendering belongs to the consuming application.

Install editable (`-e`) and keep the checkout in place: default output and
cache paths are relative to the source tree. Subsequent builds use cached
responses, which have no automatic expiry. To download fresh data:

```bash
TRENDS_REFRESH=1 trends build
```

## Choose your next step

| I want to… | Read |
| --- | --- |
| Run a command, check one series, or resolve an error | [CLI reference](cli.md) |
| Understand a formula, input, or historical limitation | [Series](series.md) |
| Load the JSON or CSV into an application | [Output reference](output.md) |
| Inspect provenance, cache behavior, and data terms | [Sources and licences](sources.md) |
| Change the code, run checks, or preview these docs | [Development](development.md) |
| Understand the project's contribution policy | [Contributing](contributing.md) |

## Before you build or consume data

- **Partial builds replace the selected output set.** Pair `--only` with
  `--out /tmp/trends-preview` to avoid removing other series from `dist/`.
  See [partial builds](cli.md#build-one-series-safely).
- **Checks can write to the cache.** `trends check` computes and validates
  without changing generated output. It can still download missing inputs.
- **A fresh clone has six series' data files.** Bitcoin output is git-ignored
  under the project's data policy, although it can be listed in the committed
  index. Run a full build before expecting all seven sets of files.
- **Data has its own terms.** The code is MIT; each JSON file records the
  licences of its inputs. Keep that metadata with the observations when you
  reuse them. See [Sources and licences](sources.md).
