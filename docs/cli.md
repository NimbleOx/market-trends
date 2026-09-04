# CLI

The package installs one command, `trends`, with three subcommands. All three
read the list of series from `registry.py`, so a series added there appears in
every command at once.

```text
trends list
trends check [--only ID ...]
trends build [--only ID ...] [--out DIR]
```

Run it from a checkout with the venv active, or prefix it with `uv run`.

## trends list

Prints the id of every series the repo publishes, one per line, sorted.

```console
$ trends list
btc-in-gold
buffett-indicator
corporate-profit-share
effective-tariff-rate
federal-deficit-share
market-value-per-dollar-of-profit
sp500-in-gold
```

These ids are the file names under `dist/series/` and the ids the site charts
by. They are lowercase and hyphenated, and `validate()` refuses anything else.

## trends check

Builds every series and validates it, and writes nothing. It is `build` without
the last step, for confirming that the upstreams are reachable and the numbers
still pass the checks.

```console
$ trends check
  building btc-in-gold ... 191 observations, 2010-09-01 to 2026-07-01
  building buffett-indicator ... 302 observations, 1947-10-01 to 2026-01-01
  building corporate-profit-share ... 318 observations, 1947-01-01 to 2026-04-01
  building effective-tariff-rate ... 138 observations, 1992-01-01 to 2026-04-01
  building federal-deficit-share ... 318 observations, 1947-01-01 to 2026-04-01
  building market-value-per-dollar-of-profit ... 302 observations, 1947-10-01 to 2026-01-01
  building sp500-in-gold ... 1867 observations, 1871-01-01 to 2026-07-01
all series valid; nothing written
```

Each line reports the count and the span, which is the quickest way to notice
a source that stopped short.

| Flag | Meaning |
| --- | --- |
| `--only ID [ID ...]` | Check only the named series. |

## trends build

Builds every series, validates all of them, then writes `dist/`. Validation
happens before any file is touched, so a failing series aborts the run and
leaves `dist/` as it was rather than half updated.

```console
$ trends build
  building btc-in-gold ... 191 observations, 2010-09-01 to 2026-07-01
  ...
  building sp500-in-gold ... 1867 observations, 1871-01-01 to 2026-07-01
wrote 15 files to /path/to/market-trends/dist
```

It writes two files per series, `dist/series/<id>.json` and
`dist/series/<id>.csv`, and an index at `dist/index.json`, then deletes any
JSON or CSV under `dist/series/` that it did not write on this run. The
deletion is deliberate: a renamed or removed series would otherwise keep being
vendored into the site forever. See [Output](output.md) for what each file
carries.

| Flag | Meaning |
| --- | --- |
| `--only ID [ID ...]` | Build only the named series. |
| `--out DIR` | Write somewhere other than `dist/`. The directory is created if it does not exist. |

!!! warning "`--only` writes a partial dist"
    Because `build` removes every series file it did not write,
    `trends build --only sp500-in-gold` into the real `dist/` deletes the other
    six series' files and writes an index that lists one series. When iterating on a
    single series, pair `--only` with `--out` pointed at a scratch directory,
    and run a full `trends build` before committing.

## Refreshing the cache

A build reads upstream responses from `cache/`, not from the network. The first
run on a fresh clone fetches everything. After that nothing is refetched until
you say so:

```bash
TRENDS_REFRESH=1 trends build
```

That refetches every source and overwrites its cached copy. An upstream
revision then shows up as a git diff in `dist/`, one line per changed
observation, which is the reason the cache exists. See
[Sources and licences](sources.md) for what lands where, and why none of it is
committed.

## Exit codes

| Code | Meaning |
| --- | --- |
| `0` | Every series built and validated. For `build`, every file was written. |
| `1` | A series failed validation. The message starts with `refused to publish:` and names the series and the check. Nothing is written. |
| `2` | An id passed to `--only` is not in the registry. |

An unreachable upstream is not caught. httpx raises, the run ends with a
traceback that names the URL, and the exit code is non-zero.

## A typical session

```bash
uv run trends check                    # is everything still buildable?
TRENDS_REFRESH=1 uv run trends build   # pull the latest upstream data, write dist/
git diff --stat dist/                  # which series moved, and by how many lines?
git diff dist/series/buffett-indicator.json   # the moved observations, one per line
```

An upstream revision looks like a few changed lines at the recent end of a
file. A units mistake looks like every line changing. The output format is
chosen so that the difference is visible at a glance; see [Output](output.md).
