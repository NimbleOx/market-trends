# Sources and licences

Every `Source` carries a `licence`, and `validate()` refuses to publish a series
whose source says `unknown`. That is deliberate: the point of the field is that
somebody decided, not that a string exists.

## Current sources

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

FRED redistributes other people's data under their terms, so a licence there
is a property of the individual series rather than of FRED. Every series
fetched from it is named in `LICENCES` in `sources/fred.py` with a decision
already made, and an unknown id raises rather than quietly publishing something
that may not be republishable. FRED is read through its no-key CSV endpoint,
which is what keeps a clone buildable without secrets.

## Nothing upstream is committed

Everything under `cache/` is refetched on a fresh clone. That keeps this repo
from being the system of record for numbers it did not produce, and from
redistributing a source whose terms may not allow it. Every source above is
independently retrievable from its own upstream, and `pytest -m network` builds
the whole set from an empty cache to prove it. CI runs that weekly, so a moved
URL surfaces there rather than on somebody's fresh clone.

The cache has two subdirectories, `cache/open` and `cache/restricted`. Neither
is committed, so the split no longer decides what ships. What it still does is
force the decision: `redistributable` is a required argument to `fetch()`, so a
source cannot be added without saying which it is. It also governs what may
leave the repo downstream.

## The one restricted source

Bitcoin comes from blockchain.com, which states no open licence, only its
general terms. So what this repo publishes from it is a *ratio* rather than
their prices, and even those computed files, `dist/series/btc-in-gold.json`
and its CSV, are git-ignored and rebuilt by a clone rather than shipped in one.
The series code is public; the numbers come from upstream on your own machine.

## Why gold comes from the datasets org

Gold used to come from the World Bank Pink Sheet directly. Two reasons it does
not now: the Pink Sheet URL carries the release year in its path, so a
hardcoded link keeps serving last year's file rather than 404ing, and the
datasets copy reaches back to 1833 instead of 1960, which is what lets
`sp500-in-gold` start where Shiller's prices do.

## Where to look for more

[github.com/orgs/datasets/repositories](https://github.com/orgs/datasets/repositories?type=all)
is worth checking before going hunting. The org maintains cleaned, versioned
copies of a lot of standard economic and financial series, each with a
`datapackage.json` declaring a licence and a history of automated commits, so
an upstream revision arrives as a readable diff rather than a number that
silently changed. They publish the same data to datahub.io. Prefer the GitHub
repo: identical bytes, but the licence is machine-readable and the history is
visible.

## The licence on the output

Two different things live in this repo and they are not under the same terms.

**The code**, everything in `src/` and `tests/`, is MIT.

**The data** in `dist/` is not the author's to relicense. Each series carries
its own provenance: every emitted JSON has a `sources` array naming the
upstream, its URL, and its licence, which is the authoritative statement for
that series. The CSV beside it carries the same numbers under the same terms;
it has no room to say so itself, which is why the JSON is the record. If you
reuse a series, honour the terms recorded in its JSON. For the current set that
means ODC-PDDL-1.0 and US public domain, which between them ask for little
beyond attribution.
