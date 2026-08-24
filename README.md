# market-trends

Computes the long-run financial series published at
[jameswarrick.com/money/trends/](https://www.jameswarrick.com/money/trends/).

This repo emits **numbers**, not charts. The site vendors the JSON and draws it,
so the source of a series can change without touching the site, and a chart can
be restyled without touching Python.

```bash
uv venv && uv pip install -e ".[dev]"

trends list          # what this repo publishes
trends check         # compute everything, write nothing
trends build         # compute everything, write dist/
TRENDS_REFRESH=1 trends build   # ignore the cache and refetch
```

## Layout

| Path | What lives there |
| --- | --- |
| `sources/` | How to get numbers out of one upstream. One module per feed. |
| `series/` | How to make one published series out of sources. One module per series. |
| `schema.py` | The contract, and the checks that enforce it before anything is written. |
| `cache/` | Raw upstream responses. Never committed; a clone refetches. See `cache/README.md`. |
| `dist/` | The published output. This is what the site vendors. |

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
| blockchain.com charts API | Bitcoin market price, daily since 2010 | No open licence stated | restricted |

Bitcoin is the one restricted source. blockchain.com states no open licence,
only its general terms, so what this repo publishes from it is a *ratio* rather
than their prices — and even that computed file, `dist/series/btc-in-gold.json`,
is git-ignored and rebuilt by a clone rather than shipped in one. The series
code is public; the numbers come from upstream on your own machine.

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
pytest -m "not network"   # schema, emit, formatting
pytest -m network         # builds every series against the cache or live upstreams
```

The network-marked tests include value assertions against turning points the
charts exist to show — the 1982 trough, the dot-com peak, 2009, 2021 — so a
units mistake or a bad join fails loudly rather than shifting a level quietly.

## Licence

Two different things live here and they are not under the same terms.

**The code** — everything in `src/` and `tests/` — is MIT. See `LICENSE`.

**The data** in `dist/` is not mine to relicense. Each series carries its own
provenance: every emitted JSON has a `sources` array naming the upstream, its
URL, and its licence, which is the authoritative statement for that series.
`validate()` refuses to publish a series whose source licence is `unknown`, so
the field is never decoration. If you reuse a series, honour the terms recorded
in its own file — for the current set that means ODC-PDDL-1.0 and US public
domain, which between them ask for little beyond attribution.
