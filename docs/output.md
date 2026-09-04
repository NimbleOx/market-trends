# Output

`trends build` writes three kinds of file under `dist/`: an index, one JSON
file per series, and one CSV per series. All are plain text, formatted for
review as a git diff rather than for size.

## dist/index.json

One entry per series, with enough metadata to list them without opening each
file. Entries are sorted by id.

```json
{
  "schemaVersion": 1,
  "generatedAt": "2026-08-31T16:24:09+00:00",
  "series": [
    {
      "id": "buffett-indicator",
      "title": "The Buffett indicator",
      "unit": "percent of GDP",
      "frequency": "quarterly",
      "scale": "linear",
      "firstDate": "1947-10-01",
      "lastDate": "2026-01-01",
      "observationCount": 302,
      "file": "series/buffett-indicator.json",
      "csv": "series/buffett-indicator.csv"
    }
  ]
}
```

The index lists every series in the registry, including `btc-in-gold`, whose
files are git-ignored. A clone that has not yet run `trends build` will find
that entry pointing at files that are not there.

## dist/series/&lt;id&gt;.json

The series itself: metadata, provenance, then the observations.

```json
{
  "schemaVersion": 1,
  "id": "sp500-in-gold",
  "title": "The S&P 500 priced in gold",
  "unit": "ounces of gold",
  "precision": 2,
  "frequency": "monthly",
  "scale": "linear",
  "description": "The S&P Composite index divided by the price of one troy ounce of gold. ...",
  "sources": [
    {
      "name": "Robert J. Shiller, US Stock Markets 1871-Present (via datasets/s-and-p-500)",
      "url": "https://github.com/datasets/s-and-p-500",
      "licence": "ODC-PDDL-1.0",
      "retrievedAt": "2026-08-31"
    }
  ],
  "generatedAt": "2026-08-31T16:24:09+00:00",
  "firstDate": "1871-01-01",
  "lastDate": "2026-07-01",
  "observationCount": 1867,
  "observations": [
    {"date": "1871-01-01", "value": 0.2345},
    {"date": "1871-02-01", "value": 0.2377}
  ]
}
```

| Field | Type | Meaning |
| --- | --- | --- |
| `schemaVersion` | integer | The shape of this file. Currently `1`. |
| `id` | string | Lowercase, hyphenated. Matches the file name. |
| `title` | string | For the chart heading. |
| `unit` | string | For the axis label. |
| `precision` | integer | Decimal places to render. A property of the series, not the chart. |
| `frequency` | `monthly`, `quarterly` or `annual` | The spacing of observations. |
| `scale` | `linear` or `log` | How to space the axis. A log series never carries a zero or negative value. |
| `description` | string | One paragraph shown beside the chart. |
| `sources` | array | Every upstream the series was computed from: `name`, `url`, `licence`, `retrievedAt`. |
| `generatedAt` | ISO 8601 timestamp, UTC | When the file was written. |
| `firstDate`, `lastDate` | ISO dates | The span, so a consumer need not scan the array. |
| `observationCount` | integer | The length of `observations`, carried separately so a truncated file is detectable. |
| `observations` | array of `{date, value}` | Dates ascend strictly, with no duplicates. Every value is finite. |

## dist/series/&lt;id&gt;.csv

The observations alone, for a spreadsheet or a dataframe. A `date,value`
header, one row per observation, LF line endings, and no comment lines, because
a spreadsheet would show them as rows and a dataframe reader would have to be
told to skip them.

```csv
date,value
1871-01-01,0.2345
1871-02-01,0.2377
```

Values are written by the same encoder as the JSON, so the number in the CSV
is the same text as the number in the JSON beside it. Everything the CSV cannot
say, the title, the unit, the precision, and above all the sources and their
licences, is in the JSON, which is why the JSON is the record and the CSV is a
convenience. The terms recorded in the JSON apply to the CSV.

```python
import pandas as pd

sp500_in_gold = pd.read_csv(
    "https://raw.githubusercontent.com/NimbleOx/market-trends/main/dist/series/sp500-in-gold.csv",
    parse_dates=["date"],
    index_col="date",
)
```

## Formatting

Every JSON field is on its own line except an observation, which is kept to
one line, and the CSV is one row per observation. A revised month therefore
shows up as one changed line in each file's diff instead of a reflowed blob,
and an upstream revision can be read for what it is.

## What a consumer can rely on

Every rule below is enforced by `validate()` before anything is written, and a
series that breaks one aborts the whole build.

- At least two observations, so the series is a line.
- Dates ascend strictly. No duplicates.
- Every value is finite. A zero denominator upstream fails the build rather
  than producing a `NaN` or `Infinity`.
- A `log` series has no zero or negative value.
- At least one source, and every source has a licence that is not `unknown`.
- `observationCount` equals the length of `observations`.
- The CSV carries exactly the observations in the JSON, in the same order,
  encoded the same way.

## How the site consumes it

The site copies `dist/` into its own tree with a sync script, validates each
file against the same shape at build time, and draws from there. A series that
changed shape upstream fails that build with a message rather than rendering an
empty chart, and nothing is fetched in the browser.
