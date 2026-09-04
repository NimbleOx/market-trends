# Cached upstream responses

The source adapters store downloaded responses here so repeated builds can
reuse the same inputs. The first use of a source downloads its response;
later calls read its cached file unless a refresh is requested. There is no
expiry or automatic freshness check.

Run commands from the repository root after installing the project and
activating its virtual environment:

```bash
# Validate with cached responses; download any missing inputs.
trends check

# Replace the inputs needed by one series and validate the result.
TRENDS_REFRESH=1 trends check --only corporate-profit-share
```

`check` writes no output series, but it can create or replace cache files.
`build` uses the same cache behaviour and also writes output. See the
[CLI reference](../docs/cli.md) for build options.

## Storage and distribution

| Directory | Current routing decision |
| --- | --- |
| `open/` | Sources the adapters mark `redistributable=True`: the two `datasets` packages and the configured FRED inputs |
| `restricted/` | Sources marked `redistributable=False`: blockchain.com Bitcoin prices |

Raw responses in both directories are git-ignored. The tracked `.gitkeep`
retains the empty `open/` directory. A fresh clone contains no cached data and
needs network access for its first computation.

The required `redistributable` argument to `fetch()` and `fetch_bytes()` selects
the directory. It does not verify source rights or prevent derived output
from being written or distributed. In particular, the S&P package's declared
PDDL licence has underlying-source qualifications. See
[Sources and licences](../docs/sources.md) before deciding what to publish.

The default Bitcoin output paths in `dist/series/` are separately git-ignored.
Those rules do not cover custom output directories, archives, or uploads.

## What the cache preserves

Keeping the same responses and code preserves calculated observations across
builds. It does not guarantee that a fresh clone produces the same history:
upstream URLs are live and can return revisions. Output timestamps also change,
and `sources[].retrievedAt` records the local build date, including cache hits,
rather than the original download date.

A refresh replaces files one at a time; it has no rollback if a later source
fails. Cache files are named by each adapter, not by a hash of the URL or
content. When changing a source URL or its meaning, refresh the affected file
or give it a new name so old responses are not silently reused.

The implementation is in `src/market_trends/sources/cache.py`. The network tests
also exercise temporary empty caches, independently of files in this directory.
