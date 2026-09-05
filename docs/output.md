# Output

`trends build` generates an index and a JSON/CSV pair for each selected series.
Use the index to discover files, the series JSON for metadata and provenance,
and the CSV for loading observations into analysis tools.

```text
dist-trends/
├── index.json
└── series/
    ├── buffett-indicator.json
    ├── buffett-indicator.csv
    └── ...
```

Paths below are relative to the output directory, which defaults to `dist-trends/` in
an editable checkout. `trends build --out DIR` produces the same layout in
`DIR`. A build with `--only` produces a partial dataset and removes unselected
series files from that output; see [CLI](cli.md#build-one-series-safely).

`trends articles build` uses the same schema and file layout under a separate
`dist-commentary/` root. Its index contains commentary datasets and article
group metadata; shared trends are referenced without duplicating files. See
[Article series](article-series.md) for the workflow and collection boundaries.

## Read a series

From the repository root, use Python's standard library to load a committed
series without installing an analysis package:

```python
import json
from pathlib import Path

root = Path("dist-trends")
index = json.loads((root / "index.json").read_text(encoding="utf-8"))
if index["schemaVersion"] != 1:
    raise ValueError("Unsupported index schema")

entry = next(item for item in index["series"] if item["id"] == "buffett-indicator")
series = json.loads((root / entry["file"]).read_text(encoding="utf-8"))
if series["schemaVersion"] != 1:
    raise ValueError("Unsupported series schema")
if series["observationCount"] != len(series["observations"]):
    raise ValueError("Observation count does not match the data")

latest = series["observations"][-1]
print(series["title"])
print(f"{latest['date']}: {latest['value']:.{series['precision']}f} {series['unit']}")
```

Index paths are relative to the directory containing `index.json`, rather than
to the `series/` subdirectory. If your output is elsewhere, change `root`.

The committed index includes `btc-in-gold`, but its JSON and CSV are ignored by
Git because its Bitcoin source does not state an open licence. A fresh clone
therefore has an index entry whose files are absent. Run a full `trends build`
to generate all files locally, or handle missing files when consuming the
committed snapshot. See [Sources and licences](sources.md) for the data terms.

## Index: `index.json`

The index contains one entry per series selected for the build, sorted by ID.
`file` points to the JSON; `csv` points to the CSV. The remaining entry fields
are copied or derived from the series. Windowed entries also carry the requested `window.from` and `window.to` dates.
The index omits `precision`,
`description`, and `sources`; load the series JSON when you need those fields.

CLI builds also include a top-level `collection` field, either `trends` or
`commentary`, to identify the output's owner. Commentary indexes include an
`articles` array describing each emitted article group, its owned dataset IDs,
and its shared trend references. See [Commentary output](article-series.md#read-and-consume-output)
for those fields. These additions retain schema version 1 and the existing
series payloads and file paths. Readers of older snapshots should allow these
index metadata fields to be absent.

This illustrative dataset contains one series with two observations:

```json
{
  "schemaVersion": 1,
  "generatedAt": "2026-09-04T12:00:00+00:00",
  "series": [
    {
      "id": "example-ratio",
      "title": "Example ratio",
      "unit": "percent",
      "frequency": "quarterly",
      "scale": "linear",
      "firstDate": "2020-01-01",
      "lastDate": "2020-04-01",
      "observationCount": 2,
      "file": "series/example-ratio.json",
      "csv": "series/example-ratio.csv"
    }
  ]
}
```

## Series: `series/<id>.json`

The corresponding complete example uses synthetic values and a placeholder
source; it is not one of the published series:

```json
{
  "schemaVersion": 1,
  "id": "example-ratio",
  "title": "Example ratio",
  "unit": "percent",
  "precision": 1,
  "frequency": "quarterly",
  "scale": "linear",
  "description": "Synthetic quarterly values illustrating the output format.",
  "sources": [
    {
      "name": "Example source",
      "url": "https://example.org/",
      "licence": "CC0-1.0",
      "retrievedAt": "2026-09-04"
    }
  ],
  "generatedAt": "2026-09-04T12:00:00+00:00",
  "firstDate": "2020-01-01",
  "lastDate": "2020-04-01",
  "observationCount": 2,
  "observations": [
    {"date": "2020-01-01", "value": 1.2345},
    {"date": "2020-04-01", "value": 2.3456}
  ]
}
```

| Field | Type | Meaning |
| --- | --- | --- |
| `schemaVersion` | integer | Output format version; currently `1`. Check this before interpreting the payload. |
| `id` | string | Series identifier, also used as the filename stem. Registered IDs use lowercase words separated by hyphens. |
| `title` | string | Human-readable heading. |
| `unit` | string | Unit shared by all observation values. |
| `precision` | integer | Suggested decimal places for display. It does not control stored precision. |
| `frequency` | string | Declared frequency: `daily`, `monthly`, `quarterly`, or `annual`. Does not guarantee a gap-free sequence. |
| `scale` | string | Suggested axis scale: `linear` or `log`. Log series contain only positive values. |
| `description` | string | Explanation of what the series measures. |
| `sources` | array of objects | Provenance records with `name`, `url`, `licence`, and `retrievedAt`. |
| `generatedAt` | ISO 8601 timestamp | UTC serialization time, to the second, with offset `+00:00`. |
| `firstDate`, `lastDate` | `YYYY-MM-DD` strings | Dates of the first and last observation. |
| `observationCount` | integer | Number of elements in `observations`. |
| `window` | object, optional | Requested inclusive `from` and `to` dates for a windowed run. Actual coverage is reported by `firstDate` and `lastDate`. Older snapshots and full-history trends may omit it. |
| `observations` | array of objects | Each has a `date` (`YYYY-MM-DD`) and a finite numeric `value`, in strictly ascending date order. |

Dates label observation periods, not release dates or fetch times. Maintained
trend builders use the first day of the month or quarter. Follow each
[series definition](series.md) when interpreting a period; do not treat a
quarterly value as a measurement taken on that single day.

Daily article series preserve the source's observation date. Weekends, holidays,
and missing readings are not filled in; `daily` does not mean one row per
calendar day. Follow the individual builder's definition when interpreting
coverage and missing observations.

### Numeric precision

The JSON and CSV retain the values returned by the builder. Current builders
round most ratios to four decimal places and `btc-in-gold` to six. The emitter
does not round again to `precision`: in the example above, `1.2345` is stored
and `precision: 1` suggests displaying `1.2`. Numeric text may use exponent
notation. Keep stored values for calculations and apply display formatting
only when presenting them.

### Build dates and reproducibility

`generatedAt` is created during serialization. Individual series and the index
receive separate timestamps, so they need not be identical. Rebuilding cached
data can change JSON metadata even when every observation stays the same.

Despite its name, `sources[].retrievedAt` currently records the local calendar
date when the source adapter runs, including when it reads cached bytes. It is
not a reliable record of the original download date or upstream freshness. No
source revision, response hash, or original fetch timestamp is included in
the output. Preserve the cache alongside the code revision if you need to
reproduce the observations from a particular run.

## Observations: `series/<id>.csv`

The CSV contains only a `date,value` header and one row per observation, in the
same order as the JSON:

```csv
date,value
2020-01-01,1.2345
2020-04-01,2.3456
```

The emitter uses the same number encoder for both formats, so the numeric text
matches. Files contain no comment rows or metadata. Keep the JSON alongside
the CSV for units, display precision, provenance, and source terms; those terms
still apply when you use the CSV.

Read a local CSV with the standard library:

```python
import csv
from pathlib import Path

path = Path("dist-trends/series/buffett-indicator.csv")
with path.open(encoding="utf-8", newline="") as stream:
    observations = [(row["date"], float(row["value"])) for row in csv.DictReader(stream)]
```

If pandas is installed in your analysis environment, use:

```python
import pandas as pd

buffett_indicator = pd.read_csv(
    "dist-trends/series/buffett-indicator.csv",
    parse_dates=["date"],
    index_col="date",
)
```

Pandas is optional and is not a project dependency.

## Validation guarantees and limits

Before output writing begins, `validate()` checks each selected series for:

- A nonempty, lowercase ID with no leading/trailing whitespace or literal spaces.
- A recognized `frequency` and `scale`.
- Nonempty `title`, `unit`, and `description` fields.
- At least one source, each with a nonempty licence other than `unknown`
  (case-insensitive).
- At least two observations, strictly ascending dates, and no duplicate dates.
- All observations lie inside the recorded window when one is present.
- Finite values, with all values positive when the scale is `log`.

The emitter derives `firstDate`, `lastDate`, and `observationCount` from the
observations and uses that same data for the JSON and CSV. These relationships
come from serialization; `validate()` does not read back or audit emitted files.
Consumers can compare the count and date span against the array when checking
downloaded or copied output.

Validation is intentionally limited. It does not check freshness, missing
periods, economic plausibility, display precision, source URLs, or whether a
recorded licence grants permission for a particular use. It also does not
enforce a complete URL-safe pattern for IDs. When adding a series, follow the
existing lowercase, hyphen-separated convention and the
[development workflow](development.md).

A validation failure leaves existing output unchanged. Output writes themselves
are not atomic: a filesystem error or interruption during emission can leave a
partial update. Treat a successful build as the prerequisite for copying or
publishing its output.

## Formatting and downstream use

Files are UTF-8. JSON is indented with one observation per line, and CSV has one
row per observation. The emitter uses `\n` line separators; the supported
Linux/macOS workflow produces LF endings. An upstream revision can therefore
be reviewed as changed observation lines rather than a reformatted array.

The intended site workflow copies generated files into its own repository and
serves them as static data. There is no service to run for these artifacts.
This repository defines and emits the format; the downstream site's sync and
rendering implementation is outside this checkout. Other consumers can use
the same files independently, checking `schemaVersion` and handling missing
files in the committed snapshot as described above.
