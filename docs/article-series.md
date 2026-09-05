# Commentary by article

Commentary datasets are grouped by the article that uses them. They share source
adapters, validation, and the JSON/CSV format with maintained trends, while
keeping a separate catalogue and generated output.

| | Maintained trends | Commentary |
| --- | --- | --- |
| Builders | `src/market_trends/trends/` | `src/market_trends/commentary/` |
| Registry | `src/market_trends/registry.py` | `src/market_trends/commentary/registry.py` |
| List datasets | `trends list` | `trends articles list` |
| List article groups | — | `trends articles groups` |
| Validate | `trends check` | `trends articles check` |
| Generate | `trends build` | `trends articles build` |
| Default output | `dist-trends/` | `dist-commentary/` |

The existing `articles` CLI name is retained. Each series ID belongs to exactly
one catalogue. An article can reference a shared trend, such as the Buffett
indicator, without duplicating its builder or its generated files.

## Commentary groups

| Article slug | Owned commentary datasets | Shared trend references |
| --- | --- | --- |
| `analyzing-the-effects-of-tariffs-on-prices-and-inflation` | `effective-tariff-rate` | — |
| `uncle-sam-has-competition` | `treasury-10-year-yield-2026`, `treasury-30-year-yield-2026` | — |
| `why-the-buffett-indicator-keeps-rising` | `corporate-profit-share`, `federal-deficit-share`, `market-value-per-dollar-of-profit` | `buffett-indicator` |

All six datasets use inclusive date windows, with fixed defaults configured
per article in this project and optional overrides for each run. The Treasury
pair fetches each calendar year covered by its effective window. Its default
January 2–September 3, 2026 span preserves the original snapshot's coverage.
Existing Treasury IDs retain
their `2026` suffix for compatibility with chart embeds, but the requested
window controls which years are gathered.

Quarterly ratios compute complete periods first, then select observations by
their period-start dates. A `--to 2025-07-01` bound includes the Q3 observation,
whose calculation still uses the full quarter's inputs. It does not claim those
inputs were available on July 1. Chart rendering remains in the consuming site.

Read the [ratio definitions](series.md) for formulas and source units. The
Treasury builder is `src/market_trends/commentary/uncle_sam_has_competition.py`;
its module docstring and tests document the exact source, window behavior, and reference
readings. The Buffett commentary's three supporting builders live together
under `src/market_trends/commentary/why_the_buffett_indicator_keeps_rising/`.

## Discover and build

From the checkout with the [environment active](development.md#set-up-a-checkout):

```bash
trends articles groups
trends articles list
trends articles check
trends articles build
```

`groups` lists article slugs, titles, default date windows, owned dataset IDs, and shared trend
references. `list` remains one owned dataset ID per line for scripts. Neither
command fetches data or writes files. `check` computes and validates selected
datasets without writing output. `build` validates all selected datasets before
writing their JSON, CSV, and index. Both can download missing source inputs.

A full commentary build writes six JSON/CSV pairs and an index: 13 files.
Ordinary trend builds leave commentary output alone; commentary builds leave
`dist-trends/` alone, including any shared trends named in article metadata.

## Select an article or individual datasets

```bash
trends articles check --article why-the-buffett-indicator-keeps-rising
trends articles build --article uncle-sam-has-competition --out /tmp/treasury-preview
trends articles build --only corporate-profit-share --out /tmp/profit-preview
```

`--article SLUG` selects the commentary datasets owned by that article. It is
mutually exclusive with `--only`. Unknown article slugs or series IDs are
rejected before building. Omitting both options, or using a bare `--only`,
selects the entire commentary catalogue.

Shared trends are listed as references, but built separately. To reproduce
all the datasets used by the Buffett commentary in separate preview folders:

```bash
trends articles build --article why-the-buffett-indicator-keeps-rising --out /tmp/buffett-commentary
trends build --only buffett-indicator --out /tmp/buffett-trend
```

A build replaces its output index and removes unselected JSON/CSV files directly
under that output's `series/` directory. This also applies to `--article`: use a
separate `--out` for previews so selecting one article does not remove the other
articles' generated files.

## Default dates and overrides

Each `Article` in `src/market_trends/commentary/registry.py` has a hard-coded
`default_window`. Checks and builds use these dates when no overrides are given:

| Article | From (inclusive) | To (inclusive) |
| --- | --- | --- |
| Analyzing the Effects of Tariffs on Prices and Inflation | 1992-01-01 | 2026-04-01 |
| Uncle Sam Has Competition | 2026-01-02 | 2026-09-03 |
| Why the Buffett Indicator Keeps Rising | 1947-01-01 | 2026-04-01 |

These windows preserve the existing snapshots' observations. They remain fixed
until the project configuration is edited; they do not advance with today's date.
`trends articles groups` displays the configured dates.

Both `--from YYYY-MM-DD` and `--to YYYY-MM-DD` are optional. Each supplied flag
replaces its bound for all selected articles, while an omitted bound retains
each article's own default. Supplying both dates applies one common window to
the selection. Overrides affect only that run and do not change the configuration.

```bash
trends articles check --article uncle-sam-has-competition --to 2026-09-04
trends articles build --from 2025-01-01 --to 2026-09-03 --out /tmp/window-preview
```

Bounds are inclusive and must be valid calendar dates with the start on or
before the end. All selected windows are validated before gathering data;
an override that conflicts with any selected article's remaining default is rejected.

Only recorded observations survive. Dates without observations, such as
weekends and holidays, are not filled, and a bound need not equal an observation
date. `firstDate` and `lastDate` report actual coverage, which can fall inside
the requested window. A window is an observation filter, not a guarantee of
complete source coverage. Runs with fewer than two observations in any selected
dataset fail before replacing output.

The source schema and calculations are validated before filtering. This keeps
an invalid input from being hidden by a narrow window. Each generated series
JSON and its index entry record the effective bounds in a `window` object,
whether they came from defaults or overrides:

```json
{"window": {"from": "2026-01-02", "to": "2026-09-03"}}
```

The Python builders accept `DateWindow(start, end)` from `market_trends.schema`.
A programmatic build can supply a different explicit window to each builder;
the emitted index preserves the window used by each series.

The CLI rejects the other collection's default output directory and directories
inside it. New indexes carry a `collection` marker, which also prevents writing
the wrong collection to a custom output directory, even when its index is empty.
Older custom indexes are checked by their series IDs.

## Read and consume output

The filenames remain flat and stable; article membership is recorded in the
index rather than encoded in each dataset's path:

```text
dist-commentary/
├── index.json
└── series/
    ├── corporate-profit-share.json
    ├── corporate-profit-share.csv
    ├── treasury-10-year-yield-2026.json
    └── ...
```

The index uses [schema version 1](output.md), with additive `collection` and
`articles` fields. `collection` is `commentary`. Each `articles` entry contains:

| Field | Meaning |
| --- | --- |
| `id` | Article slug used with `--article`. |
| `title` | Article title for display. |
| `series` | Owned dataset IDs included in this particular build; resolve their paths through the index's top-level `series` list. |
| `trendSeries` | Shared trend IDs; resolve their files through the separate trend index. They are not copied into commentary output. |

Partial builds include only groups with emitted commentary data, and only the
owned IDs actually emitted. Shared trend references describe the article as a
whole. All file paths in a top-level series entry remain relative to its own
index, so custom output directories work without rewriting file paths.

```python
import json
from pathlib import Path

root = Path("dist-commentary")
index = json.loads((root / "index.json").read_text(encoding="utf-8"))
by_id = {entry["id"]: entry for entry in index["series"]}
for article in index["articles"]:
    print(article["title"])
    for series_id in article["series"]:
        series = json.loads((root / by_id[series_id]["file"]).read_text(encoding="utf-8"))
        print(series_id, series["firstDate"], series["lastDate"])
    for series_id in article["trendSeries"]:
        print(series_id, "is available from the trend catalogue")
```

Use JSON for observations, display metadata, and provenance. Keep each CSV
with its JSON: CSV contains observations only, without source terms or units.

## Migrate from the mixed trend catalogue

The four commentary ratios previously emitted by `trends build` now belong to
`trends articles build`. Their IDs and numerical definitions are unchanged.
After updating this checkout, run both complete builds:

```bash
trends articles build
trends build
```

The first command emits the six commentary datasets within their articles'
configured default windows. To reproduce a snapshot with different dates,
select its article or dataset and pass the bounds recorded in its `window`
metadata; for older output without that field, use its `firstDate` and `lastDate`.
The second rebuilds the
trend index with its three maintained entries and removes the four old
commentary JSON/CSV pairs from `dist-trends/series/`. Legacy default indexes
without a collection marker are accepted for this migration. For older custom
output directories containing the mixed catalogue, use a fresh output directory.

Consumers that previously copied only `dist-trends/` must now import both
collections. In the site, the corresponding destinations are `src/data/trends/`
and `src/data/article-series/`. Import commentary deliberately, and remove the
old copies of the four moved IDs from the trend destination to keep IDs unique.
Update the site's importer before running its next trend sync; copying only the
new trend output would remove data needed by commentary charts. This project
produces data and does not modify downstream applications.

## Refresh and review

```bash
TRENDS_REFRESH=1 trends articles check
trends articles build --out /tmp/commentary-review
diff -ru dist-commentary /tmp/commentary-review
```

Refresh requests fresh source responses. Without it, existing cache entries
are reused. `--out` relocates output files, not the cache. A fixed window does
not freeze historical values: upstream publishers can revise observations.
Review values, dates, counts, units, and sources before replacing an article's
published snapshot. Preserve inputs and the code revision when exact
reproduction matters.

`generatedAt` changes on each build. Adapters record the local build date in
`sources[].retrievedAt`, including cache hits. A timestamp-only diff does not
mean observations changed. See [Build dates and reproducibility](output.md#build-dates-and-reproducibility).

## Add a commentary dataset

1. Add a builder under `src/market_trends/commentary/`, alongside the other
   datasets for its article. A group with several calculations can use a
   package, as the Buffett commentary does.
2. Accept a `DateWindow` argument and document the source, measure, units,
   transformations, and missing-data policy. Reuse shared adapters, compute any
   complete periods before filtering, and return `windowed(series, window)`
   from `market_trends.schema`. Do not embed a fixed source year or date span
   in the builder.
3. Add the builder to its `Article` entry in `commentary/registry.py`, or add a
   new article slug, title, and `default_window=DateWindow(start, end)` with fixed
   dates appropriate to the article. `BUILDERS` is derived from those entries. Keep
   each ID unique across both catalogues and owned by only one article group.
4. If an article uses an existing maintained trend, add its ID to `trend_series`
   instead of copying the builder into commentary.
5. Add meaningful parsing, calculation, and coverage tests. Live-source tests
   belong under `@pytest.mark.network`. Update the catalogue documentation.
6. Build into a preview directory and review the output before replacing a
   published snapshot.

Run Ruff, offline and network tests when changing builders or sources, and a
strict MkDocs build for documentation. See [Development](development.md).
