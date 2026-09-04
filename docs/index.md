# market-trends

Computes the long-run financial series published at
[jameswarrick.com/money/trends/](https://www.jameswarrick.com/money/trends/).

This repo emits **numbers**, not charts. It fetches a handful of public
upstreams, computes seven ratios from them, and writes JSON with enough
metadata for a site to draw. The site vendors the JSON. Nothing here plots.

## Install

```bash
git clone https://github.com/NimbleOx/market-trends
cd market-trends
uv venv && uv pip install -e ".[dev]"
```

Python 3.11 or later, with one runtime dependency, httpx. Install editable and
run from the checkout: `cache/` and `dist/` are found relative to the source
tree, not the working directory.

## Use

```bash
trends list     # the seven series ids
trends check    # fetch, compute, validate; write nothing
trends build    # the same, then write dist/
```

Activate the venv first, or prefix each command with `uv run`. The first run
fetches every upstream into `cache/`; later runs read from there until you ask
for a refresh. The [CLI page](cli.md) has every command, flag and exit code.

## Where to go

- [CLI](cli.md): the commands, their flags, the cache, and exit codes.
- [Series](series.md): what each of the seven series measures and why it is
  built that way.
- [Output](output.md): the JSON contract a consumer can rely on.
- [Sources and licences](sources.md): every upstream, its terms, and what
  those terms decide.
- [Development](development.md): setup, checks, CI, and the docs build.
- [Contributing](contributing.md): why this project does not take
  contributions, and notes for anyone who forks it.
