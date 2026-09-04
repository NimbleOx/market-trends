# Development

Notes for working on the repo, in this copy or in a fork. The project does not
take contributions; [Contributing](contributing.md) says why.

## Setting up

```bash
git clone https://github.com/NimbleOx/market-trends
cd market-trends
uv venv && uv pip install -e ".[dev]"
uv run pytest -m "not network"   # passes on a clean checkout
uv run trends check              # fetches every upstream into cache/, builds every series
```

`cache/` arrives empty and fills on the first build. Nothing in it is ever
committed; `cache/README.md` says why.

## Checks

```bash
uv run ruff check src tests
uv run pytest -m "not network"   # schema, emit, formatting
uv run pytest -m network         # every series, from the cache and from an empty one
uv run trends build              # and commit dist/ if the numbers moved
```

The network tests carry value assertions at the turning points the charts exist
to show, so a units mistake or a bad join fails loudly rather than shifting a
level quietly. Run them after touching a source or a series.

A changed number in `dist/` should be explainable. An upstream revision shows
up as a few changed lines at the recent end of a file, and anything else is
your change. Every build also rewrites `generatedAt` and `retrievedAt`, so a
rebuild without a refresh still touches every JSON file even when no value
moved.

## CI

Two workflows under `.github/workflows/`.

**`ci.yml`** runs on every push and pull request to `main`: the lint, and the
no-network tests on Python 3.11, 3.12 and 3.13. Weekly, on Monday at 06:00 UTC,
and on manual dispatch, it also runs the network tests, which build every
series from an empty cache against the live upstreams. That job is scheduled
rather than run per push so CI stays off other people's public datasets. A
moved URL or a feed gone behind a key surfaces there, not on somebody's fresh
clone.

GitHub disables scheduled workflows on a public repository after sixty days
without a commit. A push or a manual dispatch re-enables them.

**`docs.yml`** runs when a push or pull request to `main` touches `docs/`,
`mkdocs.yml`, `CONTRIBUTING.md`, `pyproject.toml` or the workflow itself. It
builds the site with `--strict`, and on a push to `main` deploys it to GitHub
Pages. The repository's Pages setting has to be "GitHub Actions" for the deploy
step to work.

## Docs

The site under `docs/` is built with MkDocs and the Material theme. Preview it
with:

```bash
uv pip install -e ".[docs]"
uv run mkdocs serve
```

The server mounts the site under `/market-trends/` to match `site_url`, so use
the address it prints rather than the bare port.

The strict build fails on a broken link or a missing snippet, which is the
point of running it in CI. [Contributing](contributing.md) is the repository's
`CONTRIBUTING.md` included verbatim, so there is one copy to keep current. The
[CLI page](cli.md) is the one most likely to need an edit when a command
changes.
