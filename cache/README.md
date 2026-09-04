# Cached upstream responses

A build reads from here rather than from the network, so it is reproducible and
an upstream revision shows up as a diff in `dist/` instead of a mystery.
Economic data gets restated quietly; without this you cannot tell a revision
from a bug.

Nothing in here is committed. Every file is a response this repo knows how to
refetch, so a clone arrives empty and populates it on the first build. That
keeps the repo from becoming the system of record for numbers it did not
produce, and from redistributing a source whose terms may not allow it.

Two subdirectories, because the licensing still differs by source even though
neither is published:

- `open/` — sources whose terms permit redistribution: the `datasets` org
  copies (ODC-PDDL-1.0) and US federal data (public domain).
- `restricted/` — sources that may be fetched and used to compute a published
  series, but not themselves republished.

Since neither is committed, the split no longer decides what ships. What it
still does is force the decision: `redistributable` is a required argument to
`fetch()`, so you cannot add a source without saying which it is. The point of
the field is that somebody decided, not that a string exists. It also decides
what may leave this repo downstream — see `dist/series/btc-in-gold.json` and
its CSV, which are derived from a restricted source and so are rebuilt rather
than shipped.

If you are adding a source, decide which of the two it belongs in before you
write the fetcher, not after.
