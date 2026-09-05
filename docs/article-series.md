# Article series

Article series are datasets prepared for dated analysis. They use a separate
catalogue and output directory from maintained [trend series](series.md), while
sharing source adapters, validation, and the JSON/CSV format.

| | Trend series | Article series |
| --- | --- | --- |
| Builders | `src/market_trends/series/` | `src/market_trends/article_series/` |
| Registry | `src/market_trends/registry.py` | `src/market_trends/article_series/registry.py` |
| List | `trends list` | `trends articles list` |
| Validate | `trends check` | `trends articles check` |
| Generate | `trends build` | `trends articles build` |
| Default output | `dist-trends/` | `dist-commentary/` |

Use trend series for maintained histories that extend as new observations
arrive. Use article series when an analysis needs a defined observation window
or a dataset that is reviewed separately from the maintained catalogue.

Ordinary trend builds leave article output alone, and article builds leave
`dist-trends/` alone. Article output lives outside `dist-trends/` so it is also excluded from
consumers that copy the entire trend directory.

## Discover and build

From the checkout with the [environment active](development.md#set-up-a-checkout):

```bash
trends articles list
trends articles check
trends articles build
```

`list` prints registered IDs without fetching data. `check` computes and
validates selected series without writing generated output. `build` validates
all selected series before writing their JSON, CSV, and index. Both `check`
and `build` can download missing source inputs into the cache.

Read the builder module for a series' definition, date window, transformations,
and reference readings. These details belong with the implementation and its
tests. The generated JSON carries the actual coverage, units, display metadata,
and source records for consumers.

## Select a subset or output directory

Article commands accept the same `--only` and `--out` options as trend commands.
Replace `SERIES_ID` below with an ID returned by `trends articles list`:

```bash
trends articles check --only SERIES_ID
trends articles build --only SERIES_ID --out /tmp/article-preview
```

Omitting `--only`, or supplying it without IDs, selects the entire article
catalogue. An ID from the trend catalogue is not accepted by article commands.
Date bounds and transformations are configured in each builder; the CLI does
not provide `--from` or `--to` overrides.

A build replaces its output index and removes unselected JSON/CSV files from
that output's `series/` directory. It does not merge a partial build with an
older full build. Use a separate output directory for partial previews.

The CLI rejects an output path inside the other collection's default directory,
and a custom directory whose index lists registered series from the other
collection. Give custom article and trend builds separate paths.

## Read and consume output

Each selected series produces a JSON/CSV pair, alongside one index:

```text
dist-commentary/
├── index.json
└── series/
    ├── <id>.json
    ├── <id>.csv
    └── ...
```

The index uses [schema version 1](output.md), and its file paths are relative to
the directory containing the index. Consumers can discover the available files
without hardcoding a dataset count or filenames:

```python
import json
from pathlib import Path

root = Path("dist-commentary")
index = json.loads((root / "index.json").read_text(encoding="utf-8"))
for entry in index["series"]:
    series = json.loads((root / entry["file"]).read_text(encoding="utf-8"))
    print(series["id"], series["firstDate"], series["lastDate"], series["observationCount"])
```

Use JSON when importing chart data or inspecting provenance. Keep each CSV
with its JSON: CSV contains observations only, without units or source terms.
See [Output](output.md) for the full field contract and loading examples.

In a consuming application, keep article imports separate from maintained
trend imports. Update article data deliberately after reviewing the generated
diff. Chart rendering, interaction, and publishing belong to the consumer;
this project produces data files and does not modify downstream applications.

## Refresh and review

```bash
TRENDS_REFRESH=1 trends articles check
trends articles build --out /tmp/article-review
diff -ru dist-commentary /tmp/article-review
```

The refresh variable requests fresh inputs from the selected source adapters.
Without it, existing cached responses are reused. `--out` relocates generated
files, not the cache. See [CLI](cli.md#use-and-refresh-the-cache) for details.

A fixed date window does not freeze the upstream data vintage: publishers can
revise historical observations. Review changed values, dates, counts, units,
and source metadata before replacing an existing snapshot. Keep the original
inputs and code revision when exact reproduction of an earlier run matters.

`generatedAt` changes on each build. Current adapters record the local build
date in `sources[].retrievedAt`, including cache hits, rather than the original
download date. A timestamp-only diff does not mean the observations changed.
See [Build dates and reproducibility](output.md#build-dates-and-reproducibility).

## Add an article series

1. Create a module under `src/market_trends/article_series/` with a
   zero-argument builder returning a `Series`. Keep its ID unique across both
   catalogues.
2. Describe the measure, exact source, input units, date window, transformations,
   and missing-value policy in the module docstring. Put dataset-specific
   coverage and reference readings there and in tests, so the general guides
   do not depend on individual publications.
3. Fetch and parse inputs through a shared source adapter. Keep article-specific
   window selection and transformations in the builder. Record source terms
   and cache routing as described in [Sources and licences](sources.md).
4. Set the title, unit, frequency, precision, scale, description, sources, and
   observations. Declare coverage requirements explicitly when a truncated
   source would otherwise produce a misleading snapshot. Validation rejects
   duplicate dates, non-finite values, and other structural errors; it does not
   know which dates or economic interpretation an analysis requires.
5. Register the builder in `src/market_trends/article_series/registry.py`.
   Keep it out of the maintained trend registry.
6. Add offline tests for parsing, transformations, and window boundaries, plus
   meaningful reference-value and live-source checks. Mark tests that fetch
   upstream data with `@pytest.mark.network`.
7. Build into a preview directory and review the output before replacing a
   published snapshot.

Run Ruff, `pytest -m "not network"`, and `pytest -m network` when changing a
builder or source. Run the strict MkDocs build when editing documentation.
See [Development](development.md) for the complete commands.
