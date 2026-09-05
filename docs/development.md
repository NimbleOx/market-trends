# Development

Use this guide to run checks, change the computation, or maintain your own fork.
The project does not accept contributions; see the
[contribution policy](contributing.md).

## Set up a checkout

You need Git and Python **3.11 or newer**. The commands below use
[uv](https://docs.astral.sh/uv/); a standard `pip` alternative follows.
Run them in a terminal from the directory where you keep your projects:

```bash
git clone https://github.com/NimbleOx/market-trends.git
cd market-trends
uv venv
source .venv/bin/activate
uv pip install -e ".[dev,docs]"
```

If you are working in a fork, clone its URL instead. In Windows PowerShell,
replace `source .venv/bin/activate` with `.venv\Scripts\Activate.ps1`.
Activate the environment again whenever you open a new terminal.

The editable install (`-e`) makes changes under `src/` available immediately.
Use the checkout even if you only want to run the CLI: the application finds
`cache/` and its default `dist-trends/` relative to the installed source tree. A wheel
installation is not the intended workflow.

The `dev` extra installs pytest and Ruff; the `docs` extra installs MkDocs and
Material. You can use `".[dev]"` if you do not need to build the documentation.

### Without uv

Start from the cloned repository and create the same environment with Python:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev,docs]"
```

Make sure `python3` is Python 3.11 or newer. On Windows, use an appropriate
Python 3.11+ interpreter, such as `py -3.11 -m venv .venv`, followed by the
PowerShell activation command above.

### Verify the setup

Run all remaining commands from the repository root with the environment
active:

```bash
trends list
ruff check src tests
pytest -m "not network"
```

These checks do not download source data. `trends list` prints the registered
series IDs; the test selection covers schema validation and file emission.

To check the data pipeline, run:

```bash
trends check
```

This builds and validates every series. It downloads any missing upstream
responses into `cache/`, but does not write `dist-trends/`. A fresh clone needs network
access; the current sources do not require API keys.

## Find the code you need

The pipeline is: **source response → observations and provenance → computed
series → validation → JSON and CSV**.

| Change | Start here |
| --- | --- |
| Read or replace an upstream feed | `src/market_trends/sources/` |
| Change a formula, join, or aggregation | `src/market_trends/series/` |
| Make a series available to the CLI | `src/market_trends/registry.py` |
| Change the data model or validation | `src/market_trends/schema.py` |
| Change the output format or file handling | `src/market_trends/emit.py` |
| Add or change a CLI option | `src/market_trends/cli.py` and [CLI reference](cli.md) |
| Check calculations against historical values | `tests/test_series.py` |
| Check validation or emitted files without network access | `tests/test_schema.py` and `tests/test_emit.py` |

Source functions return observations and a `Source` describing their origin.
Series builders combine those observations into a `Series`. The registry maps
public IDs to builders; the CLI uses that mapping to choose what to compute.
See [Output](output.md) for the serialized contract.

## Check a change

```bash
ruff check src tests
pytest -m "not network"
```

Run the network tests after changing a source or calculation:

```bash
pytest -m network
```

This selection includes two kinds of build checks: one uses the normal cache,
and one gives each registered series an empty temporary cache and fetches its
inputs from upstream. It also checks historical values for the Buffett
indicator and S&P 500 in gold. These value assertions catch unit conversions or
joins that could pass schema validation while producing the wrong numbers.
They do not yet cover every formula.

For a quick check of one builder without writing output:

```bash
trends check --only buffett-indicator
```

To inspect one series' files, use a separate output directory:

```bash
trends build --only buffett-indicator --out /tmp/market-trends-preview
```

Replace `/tmp/market-trends-preview` with a temporary directory appropriate for
your system. A build replaces the selected output directory's index and
removes other JSON and CSV files from its `series/` subdirectory. Running
`--only` against the default `dist-trends/` therefore removes the unselected series'
files. See [CLI reference](cli.md) for details.

### Review generated data

When the change is ready, rebuild the complete output:

```bash
trends build
git diff -- dist-trends/
git status --short
```

A normal build reuses cached responses. To deliberately check current upstream
data, use `TRENDS_REFRESH=1 trends build` in Bash or Zsh. In PowerShell, set
`$env:TRENDS_REFRESH = "1"`, run `trends build`, then remove the setting with
`Remove-Item Env:TRENDS_REFRESH`.

Review changes in observations separately from timestamp changes. Upstreams can
revise historical values as well as recent ones; a changed value is not, by
itself, evidence of a bug. Conversely, a schema-valid output does not establish
that a formula is correct.

`generatedAt` is the current build timestamp. Source adapters set `retrievedAt`
to the current date even when reading cached bytes, so a rebuild is not
byte-for-byte reproducible and `retrievedAt` does not establish data freshness.
Commit the intended code, documentation, and permitted generated output
together. Raw cache responses are ignored, as are the generated Bitcoin files;
see [Sources and licences](sources.md).

## Add a series in a fork

1. Create `src/market_trends/series/<name>.py` with a unique, lowercase,
   hyphenated `ID` and a zero-argument `build() -> Series` function. Start from
   `buffett_indicator.py` for a quarterly ratio or `sp500_in_gold.py` for a
   monthly ratio.
2. Explain the measure, formula, input units, date alignment, and limitations
   in the module docstring. Write a shorter `description` that makes sense to
   someone reading the output without opening the code.
3. Set the title, unit, precision, frequency, scale, sources, and observations.
   `precision` controls display; it does not round stored values. If rounding
   is part of the computation, do it explicitly. A logarithmic scale requires
   every value to be positive.
4. Import the module in `src/market_trends/registry.py` and add
   `<module>.ID: <module>.build` to `BUILDERS`. This registers it with the CLI
   and the generic build tests; it does not update documentation or add tests
   of its meaning.
5. Add historical value assertions to `tests/test_series.py` using
   `@pytest.mark.network` when the test calls a real source. Choose values
   that would reveal a wrong unit, date alignment, or denominator. Add
   small, offline tests for new parsing or transformation logic where useful.
6. Update the series catalogue in [Series](series.md), the repository README,
   and any affected source or output documentation. If redistribution is
   restricted, also update `.gitignore` as described below.
7. Run the checks above, build all series, and review the generated diff before
   committing the change in your fork.

Choose a frequency supported by the inputs. A quarterly GDP denominator makes
a quarterly ratio; converting it to monthly would create apparent detail the
source does not provide. If an upstream repeats coarser observations on finer
dates, document that limitation. The current historical gold feed, for
example, repeats annual averages across months before 1960.

## Add a source in a fork

For a dated article dataset, use `src/market_trends/article_series/` and its
own registry instead of the maintained trend registry. The same source and
validation conventions below apply. See [Article series](article-series.md)
for fixed-window builders, reference-value tests, and output separation.

1. **Record the terms before writing the adapter.** Identify the publisher,
   the exact dataset, and the terms that apply to its components and your
   intended use. Record the decision in `Source.licence` and explain relevant
   limitations in the module docstring and [Sources and licences](sources.md).
   `validate()` only rejects an empty licence string or `unknown`
   (case-insensitive). It does not verify permission or enforce redistribution
   restrictions.
2. **Choose a retrievable endpoint.** Prefer a documented, stable URL and a
   format the adapter can parse without manual steps. Check freshness, units,
   frequency, missing-value conventions, and how revisions appear. If using a
   mirror, check its provenance and terms as well as those of the original
   publisher.
3. **Keep fetching and parsing in `src/market_trends/sources/`.** Use
   `fetch()` for UTF-8 text or `fetch_bytes()` for binary responses. Supply a
   unique cache `name` and an explicit `redistributable=True` or `False`.
   Return parsed `Observation` values with a `Source`, following the existing
   adapters. Neither cache directory is committed.
4. **For FRED, extend the existing adapter.** Add the series ID to `LICENCES`
   in `src/market_trends/sources/fred.py` as
   `(human_name, licence, redistributable)`. The adapter rejects unlisted IDs.
   FRED hosts data from different publishers, so another FRED series' terms
   are not sufficient.
5. **Apply output restrictions explicitly.** The `redistributable` flag only
   selects `cache/open/` or `cache/restricted/`; it does not prevent the CLI
   from writing or publishing a derived series. For each restricted output,
   add its JSON and CSV paths under `dist-trends/series/` to `.gitignore`, and check
   any downstream publishing workflow separately. The existing
   `btc-in-gold` entries show the pattern. `.gitignore` does not untrack files
   already committed or protect output written with `--out` elsewhere.
6. **Exercise the source through a registered series.** There is no separate
   source registry. The generic network tests only reach an adapter if a
   builder in `BUILDERS` calls it. Add focused parsing tests for the format's
   edge cases and run `pytest -m network` to verify a fresh fetch.

A recorded restriction is different from a grant of permission. The existing
Bitcoin adapter records that no open licence is stated, and its derived files
are ignored. Converting prices into a ratio does not itself establish a right
to redistribute them.

## Build and preview the documentation

If you installed only the `dev` extra, add the documentation tools first:

```bash
uv pip install -e ".[dev,docs]"
```

With standard pip, use `python -m pip install -e ".[dev,docs]"` instead.
Then run:

```bash
mkdocs serve
```

Open the address printed by MkDocs, including the `/market-trends/` prefix,
and leave the command running while you edit. Stop it with `Ctrl+C`.
Before committing documentation changes, run the same build as CI:

```bash
mkdocs build --strict --clean
```

The generated site is in `site/`, which is ignored. Strict mode fails on
warnings such as links to missing documentation files or page sections; this
project enables anchor warnings in `mkdocs.yml`. Snippet path checking also
catches missing includes. The build does not verify external websites, so
inspect changed pages and follow their external links in the preview.

Edit root `CONTRIBUTING.md` to change the contribution policy.
`docs/contributing.md` includes it verbatim through `pymdownx.snippets`. Links
in the shared file must work both on GitHub and in the built site. The
navigation and extensions live in `mkdocs.yml`.

## Understand CI

The workflows are in `.github/workflows/`:

| Workflow | Trigger | Checks and output |
| --- | --- | --- |
| `ci.yml` | Pushes to `main`, pull requests, Monday at 06:00 UTC, or manual dispatch | Ruff, plus offline tests on Python 3.11, 3.12, and 3.13. The network test job runs only on the schedule or manual dispatch. |
| `docs.yml` | Matching file changes on pushes to `main` or pull requests; manual dispatch | A strict, clean MkDocs build. A successful non-PR run on `main` also deploys to GitHub Pages. |

The documentation path filter covers `docs/**`, `mkdocs.yml`,
`CONTRIBUTING.md`, `pyproject.toml`, and `.github/workflows/docs.yml`.
For a fork, update `site_url`, repository links, and author details in
`mkdocs.yml` before publishing. Set the repository's Pages source to
**GitHub Actions** for deployment, and check the Actions tab if scheduled runs
are inactive.
