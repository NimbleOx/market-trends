# CLI

Use `trends` to discover, validate, and generate the registered series. The
examples below assume you have [set up a checkout](development.md#set-up-a-checkout),
activated its virtual environment, and opened a shell in the repository root.
If you use uv, you can prefix commands with `uv run`, such as `uv run trends list`.

| Command | Purpose | Side effects |
| --- | --- | --- |
| `trends list` | Print the available series IDs. | No data fetches or output writes. |
| `trends check` | Compute and validate every series. | May download and cache missing source data. Does not write `dist-trends/`. |
| `trends build` | Compute, validate, and write every series. | May update the cache. Replaces the output index and series files, and removes stale series files. |

```text
trends list
trends check [--only [ID ...]]
trends build [--only [ID ...]] [--out DIR]
```

Run `trends --help` for command names, or `trends build --help`
for a command's options.

## Article commands

Use the `articles` group for dated article datasets:

```text
trends articles list
trends articles check [--only [ID ...]]
trends articles build [--only [ID ...]] [--out DIR]
```

These commands use `src/market_trends/article_series/registry.py` and default
to `dist-commentary/`. The ordinary commands continue to use the trend registry
and `dist-trends/`. IDs are resolved only within the selected collection; neither
build includes the other collection. See [Article series](article-series.md)
for output separation, dataset registration, and downstream use.

## List series

```bash
trends list
```

The output is one ID per line, sorted alphabetically:

```text
btc-in-gold
buffett-indicator
corporate-profit-share
effective-tariff-rate
federal-deficit-share
market-value-per-dollar-of-profit
sp500-in-gold
```

The ordinary commands use `src/market_trends/registry.py`. Use these
IDs with `--only`; they also identify the JSON and CSV files under `dist-trends/series/`.
See [Series](series.md) for definitions and formulas.

## Check data without writing output

```bash
trends check
trends check --only buffett-indicator corporate-profit-share
```

`check` computes and validates each selected series in ID order. For each one,
it prints the observation count and the first and last date, then finishes with:

```text
selected series valid; no output files written
```

Here, “no output files written” refers to published data: a missing cache entry is
still downloaded and saved under `cache/`. With a populated cache, a successful
check confirms that the cached inputs are buildable; it does not test whether
the upstream is reachable or has newer data.

The date span is useful for spotting an unexpectedly short series. Validation
does not check freshness or require an observation in every period; review the
span and relevant data changes yourself.

## Build output

```bash
trends build
```

The CLI computes and validates every selected series before the emitter writes
any output. A computation or validation failure leaves the output directory
unchanged, although source data may already have been cached.

A successful full build currently writes 15 files: two per series plus
`index.json`. The final line reports the number of files written and the output
directory. See [Output](output.md) for their contents and how to read them.

| Option | Available on | Behavior |
| --- | --- | --- |
| `--only ID [ID ...]` | `check`, `build` | Select the named series. IDs are case-sensitive and processed in sorted order. |
| `--out DIR` | `build` | Choose the output directory; missing directories are created. |

Omitting `--only` selects every series. A bare `--only` also selects every
series, because the parser accepts an empty list. Supply all desired IDs after
one `--only` option, listing each ID once; repeated IDs are not deduplicated.

In an editable checkout, the default output is the repository's `dist-trends/`, even
when you invoke `trends` from another directory. A relative `--out` path is
resolved from your current working directory. Both default output and cache paths are derived from the
installed module's location. Use the documented editable checkout workflow so
these paths resolve inside the repository.

### Build one series safely

For a quick validation, use `check --only`. To inspect generated files, choose
a separate output directory:

```bash
trends build --only sp500-in-gold --out /tmp/market-trends-preview
```

This writes `index.json`, `series/sp500-in-gold.json`, and
`series/sp500-in-gold.csv` inside `/tmp/market-trends-preview`.

!!! warning "A build replaces the selected output set"
    Every build replaces the index with only the selected series, then deletes
    other `.json` and `.csv` files directly inside the output's `series/`
    directory. Running `trends build --only sp500-in-gold` without `--out`
    therefore removes the other series from the default output. Use a directory
    dedicated to this project's generated files, and run a full build before
    committing the published dataset.

Validation happens before writing, but writing is not a filesystem transaction.
A disk error, permissions error, or interrupted process during emission can
leave partially updated output. Fix the cause and rerun the build.

## Use and refresh the cache

Both `check` and `build` use a fetch-through cache:

- An existing response is reused without a network request.
- A missing response is downloaded and saved for later runs.
- Setting `TRENDS_REFRESH=1` bypasses existing entries and saves fresh responses.

Refresh and validate one series without changing published output:

```bash
TRENDS_REFRESH=1 trends check --only buffett-indicator
```

Refresh all inputs and regenerate the dataset:

```bash
TRENDS_REFRESH=1 trends build
```

The variable must be exactly `1` to enable refresh. These shell commands set it
for that invocation only. Refresh applies to source requests made by the
selected builders, so a shared source can be fetched more than once in a full
run. A failed run can leave some cache entries refreshed and others unchanged.

`--out` changes only the output location; it does not isolate or relocate the
cache. There is no cache-expiration policy or offline flag. To run without
network access, all required responses must already be cached and refresh must
be disabled. See [Sources and licences](sources.md) and the repository's
`cache/README.md` for cache locations and data terms.

## Errors and exit codes

| Exit code | Meaning | Output behavior |
| --- | --- | --- |
| `0` | The command succeeded, or help was displayed. | `build` completed its writes and cleanup; `check` wrote no published output. |
| `1` for a caught validation error | The message starts with `refused to publish:` and identifies the series and failed rule. | No published output is changed. The cache may have changed. |
| `2` | Invalid arguments, a missing subcommand, or an unknown `--only` ID. Unknown IDs produce `unknown series: ...`. | Rejected before any series is built. |

Network failures, parsing errors, and filesystem errors are not caught by the
CLI. They produce a traceback and a nonzero exit status rather than the
`refused to publish:` message. A nonzero status alone therefore does not imply
a validation failure.

For a failed download, inspect the exception at the end of the traceback and
the affected source's URL. For a validation or parsing failure, inspect the
source or series and its cached response. If you suspect stale or incomplete
input, refresh the affected series with `check --only` before rebuilding. For
an unknown ID, use `trends list` to find its exact spelling.

## Review a dataset update

```bash
trends check
TRENDS_REFRESH=1 trends build
git diff --stat -- dist-trends/
git diff -- dist-trends/series/buffett-indicator.json
git status --short
```

Review changed values and date spans as well as new or removed files. A cached
rebuild can still change timestamps and source dates; see
[Build dates and reproducibility](output.md#build-dates-and-reproducibility).
The Bitcoin files are generated locally but ignored by Git, so they will not
appear in this diff. Run the [development checks](development.md) before
committing changes.
