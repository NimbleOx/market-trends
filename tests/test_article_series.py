import json
from dataclasses import replace
from datetime import date

import pytest

from market_trends import cli
from market_trends.commentary import uncle_sam_has_competition as article
from market_trends.commentary.registry import ARTICLES, groups_for
from market_trends.commentary.registry import BUILDERS as ARTICLE_BUILDERS
from market_trends.registry import BUILDERS
from market_trends.schema import (
    DateWindow,
    Observation,
    Series,
    Source,
    ValidationError,
    to_dict,
    validate,
    windowed,
)
from market_trends.sources import cache, treasury

REFERENCE_WINDOW = DateWindow(date(2026, 1, 2), date(2026, 9, 3))


# Small parser fixture, including synthetic out-of-window rows and the legacy
# uppercase 30 YR header. It is not a saved upstream response.
CSV = """Date,30 YR,30 Yr,10 Yr,1 Mo
09/04/2026,999,5.24,4.78,3.79
09/03/2026,999,5.25,4.77,3.83
01/05/2026,999,4.85,4.17,3.71
01/02/2026,999,4.86,4.19,3.72
01/01/2026,999,4.90,4.20,3.70
"""


def test_parser_uses_named_maturities_and_sorts_dates():
    rows = treasury._parse(CSV, 30)
    assert rows[0].date == date(2026, 1, 1)
    assert rows[-1] == Observation(date(2026, 9, 4), 5.24)
    assert rows[1].value == 4.86  # Not the legacy column's 999.


def test_parser_preserves_missing_days_instead_of_filling():
    csv = '\ufeffDate,10 Yr\n01/06/2026,4.18\n01/05/2026,N/A\n01/02/2026,4.19\n'
    rows = treasury._parse(csv, 10)
    assert rows == [Observation(date(2026, 1, 2), 4.19), Observation(date(2026, 1, 6), 4.18)]


@pytest.mark.parametrize("csv", ["Date,30 YR\n", "Date,10 Yr,10 Yr\n", "wrong,10 Yr\n"])
def test_parser_refuses_changed_or_ambiguous_headers(csv):
    with pytest.raises(ValidationError, match="unique"):
        treasury._parse(csv, 10)


@pytest.mark.parametrize("maturity,first,last", [(10, 4.19, 4.77), (30, 4.86, 5.25)])
def test_article_keeps_the_exact_window_and_percent_units(monkeypatch, maturity, first, last):
    monkeypatch.setattr(treasury, "fetch", lambda *args, **kwargs: CSV)
    series = ARTICLE_BUILDERS[f"treasury-{maturity}-year-yield-2026"](REFERENCE_WINDOW)
    payload = to_dict(series)
    assert series.first_date == REFERENCE_WINDOW.start
    assert series.last_date == REFERENCE_WINDOW.end
    assert payload["frequency"] == "daily"
    assert payload["precision"] == 2
    assert payload["unit"] == "percent"
    assert payload["observationCount"] == 3
    assert payload["window"] == {"from": "2026-01-02", "to": "2026-09-03"}
    assert series.observations[0].value == first
    assert series.observations[-1].value == last
    assert series.sources[0].url == treasury.PAGE_URL.format(year=2026)


def test_requested_bound_does_not_have_to_be_an_observation_date(monkeypatch):
    monkeypatch.setattr(treasury, "fetch", lambda *a, **kw: CSV.replace("09/03/2026", "09/02/2026"))
    series = article.build_10_year(REFERENCE_WINDOW)
    assert series.last_date == date(2026, 9, 2)
    assert series.window == REFERENCE_WINDOW


@pytest.mark.parametrize("replacement,error", [
    ("01/02/2026,999,4.85,4.17,3.71", "duplicate"),
    ("01/05/2026,999,4.85,NaN,3.71", "non-finite"),
])
def test_bad_observations_cannot_be_published(monkeypatch, replacement, error):
    csv = CSV.replace("01/05/2026,999,4.85,4.17,3.71", replacement)
    monkeypatch.setattr(treasury, "fetch", lambda *a, **kw: csv)
    with pytest.raises(ValidationError, match=error):
        validate(article.build_10_year(REFERENCE_WINDOW))


def test_adapter_refuses_the_wrong_year(monkeypatch):
    monkeypatch.setattr(treasury, "fetch", lambda *a, **kw: CSV.replace("09/04/2026", "09/04/2025"))
    with pytest.raises(ValidationError, match="another year"):
        article.build_10_year(REFERENCE_WINDOW)


def test_registries_and_list_commands_remain_separate(capsys):
    assert not set(BUILDERS) & set(ARTICLE_BUILDERS)
    assert cli.main(["list"]) == 0
    assert set(capsys.readouterr().out.splitlines()) == set(BUILDERS)
    assert cli.main(["articles", "list"]) == 0
    assert set(capsys.readouterr().out.splitlines()) == set(ARTICLE_BUILDERS)
    assert cli.main(["build", "--only", article.ID_10_YEAR]) == 2
    assert cli.main(["articles", "build", "--only", "buffett-indicator"]) == 2


@pytest.fixture
def local_cli(tmp_path, monkeypatch):
    monkeypatch.setattr(cli, "DIST", tmp_path / "dist-trends")
    monkeypatch.setattr(cli, "ARTICLE_DIST", tmp_path / "dist-commentary")
    monkeypatch.setattr(treasury, "fetch", lambda *a, **kw: CSV)
    trend = Series(
        id="example-trend", title="Example", unit="percent", precision=1,
        frequency="quarterly", description="Synthetic trend for output separation tests.",
        sources=[Source("Example", "https://example.org", "CC0-1.0", date(2026, 1, 1))],
        observations=[Observation(date(2026, 1, 2), 1), Observation(date(2026, 4, 1), 2)],
    )
    monkeypatch.setattr(cli, "BUILDERS", {trend.id: lambda: trend})
    # CLI/output tests use local data for every catalogue entry. The actual
    # Treasury builder still runs against the parser fixture above.
    monkeypatch.setattr(cli, "ARTICLE_BUILDERS", {
        series_id: builder if series_id.startswith("treasury-") else
        lambda window, series_id=series_id: windowed(replace(trend, id=series_id), window)
        for series_id, builder in ARTICLE_BUILDERS.items()
    })
    return cli.DIST, cli.ARTICLE_DIST


def contents(root):
    return {str(path.relative_to(root)): path.read_bytes() for path in root.rglob("*")
            if path.is_file()}


def test_each_build_and_partial_cleanup_leaves_the_other_collection_untouched(local_cli):
    trends_out, articles_out = local_cli
    assert cli.main(["build"]) == 0
    before_trends = contents(trends_out)
    assert cli.main(["articles", "build"]) == 0
    assert contents(trends_out) == before_trends
    index = json.loads((articles_out / "index.json").read_text())
    assert {s["id"] for s in index["series"]} == set(ARTICLE_BUILDERS)
    assert all((articles_out / s["csv"]).exists() for s in index["series"])
    before_articles = contents(articles_out)
    assert cli.main(["build"]) == 0
    assert contents(articles_out) == before_articles
    before_trends = contents(trends_out)
    assert cli.main(["articles", "build", "--only", article.ID_10_YEAR]) == 0
    assert contents(trends_out) == before_trends
    assert not (articles_out / "series" / f"{article.ID_30_YEAR}.json").exists()
    assert not (articles_out / "series" / f"{article.ID_30_YEAR}.csv").exists()


def test_check_writes_no_output_and_bad_data_preserves_existing_output(local_cli, monkeypatch):
    _, articles_out = local_cli
    assert cli.main(["articles", "check"]) == 0
    assert not articles_out.exists()
    assert cli.main(["articles", "build"]) == 0
    before = contents(articles_out)
    monkeypatch.setattr(treasury, "fetch", lambda *a, **kw: CSV.replace("5.25,4.77", "NaN,NaN"))
    assert cli.main(["articles", "build"]) == 1
    assert contents(articles_out) == before


def test_output_override_cannot_cross_collections(local_cli, tmp_path):
    trends_out, articles_out = local_cli
    for args in [
        ["articles", "build", "--out", str(trends_out)],
        ["articles", "build", "--out", str(trends_out / "nested")],
        ["build", "--out", str(articles_out)],
    ]:
        with pytest.raises(SystemExit) as error:
            cli.main(args)
        assert error.value.code == 2
    custom = tmp_path / "custom"
    assert cli.main(["build", "--out", str(custom)]) == 0
    before = contents(custom)
    with pytest.raises(SystemExit) as error:
        cli.main(["articles", "build", "--out", str(custom)])
    assert error.value.code == 2
    assert contents(custom) == before


def test_commentary_is_grouped_by_article_with_shared_trends_referenced():
    assert set(BUILDERS) == {
        "btc-in-gold", "buffett-indicator", "capital-share-gdi",
        "federal-deficit", "federal-deficit-gdp",
        "federal-deficit-monthly", "federal-deficit-ttm", "labor-share-gdi", "sp500-in-gold",
    }
    assert set(ARTICLE_BUILDERS) == {
        "corporate-profit-share", "federal-deficit-share", "market-value-per-dollar-of-profit",
        "effective-tariff-rate", "treasury-10-year-yield-2026", "treasury-30-year-yield-2026",
    }
    owned = [series_id for group in ARTICLES.values() for series_id in group.builders]
    assert len(owned) == len(set(owned)) == len(ARTICLE_BUILDERS)
    assert not set(owned).intersection(BUILDERS)
    for group in ARTICLES.values():
        assert set(group.trend_series).issubset(BUILDERS)
    assert ARTICLES["why-the-buffett-indicator-keeps-rising"].trend_series == ("buffett-indicator",)


def test_article_selection_builds_only_its_datasets_and_records_the_group(local_cli):
    trends_out, articles_out = local_cli
    assert cli.main(["build"]) == 0
    before = contents(trends_out)
    slug = "why-the-buffett-indicator-keeps-rising"
    assert cli.main(["articles", "build", "--article", slug]) == 0
    index = json.loads((articles_out / "index.json").read_text())
    expected = {
        "corporate-profit-share", "federal-deficit-share", "market-value-per-dollar-of-profit",
    }
    assert {series["id"] for series in index["series"]} == expected
    assert {file.stem for file in (articles_out / "series").iterdir()} == expected
    assert index["collection"] == "commentary"
    assert all(entry["window"] == {"from": "1947-01-01", "to": "2026-04-01"}
               for entry in index["series"])
    assert index["articles"] == [{
        "id": slug, "title": "Why the Buffett Indicator Keeps Rising",
        "series": sorted(expected), "trendSeries": ["buffett-indicator"],
    }]
    assert contents(trends_out) == before


def test_partial_series_build_omits_unbuilt_groups_and_references(local_cli):
    _, articles_out = local_cli
    assert cli.main(["articles", "build", "--only", article.ID_10_YEAR]) == 0
    index = json.loads((articles_out / "index.json").read_text())
    assert index["articles"] == [{
        "id": "uncle-sam-has-competition", "title": "Uncle Sam Has Competition",
        "series": [article.ID_10_YEAR], "trendSeries": [],
    }]
    assert groups_for([]) == []


def test_group_listing_and_check_do_not_write_output(local_cli, capsys):
    trends_out, articles_out = local_cli
    assert cli.main(["articles", "groups"]) == 0
    output = capsys.readouterr().out
    for slug in ARTICLES:
        assert slug in output
    assert "default window: 1992-01-01 through 2026-04-01" in output
    assert "default window: 2026-01-02 through 2026-09-03" in output
    assert "default window: 1947-01-01 through 2026-04-01" in output
    assert "buffett-indicator (shared trend; built by trends build)" in output
    assert cli.main(["articles", "check", "--article", "uncle-sam-has-competition"]) == 0
    assert not trends_out.exists()
    assert not articles_out.exists()


@pytest.mark.parametrize("options", [
    ["--article", "missing-article"],
    ["--article", "uncle-sam-has-competition", "--only", article.ID_10_YEAR],
])
def test_invalid_article_selection_is_rejected_before_writing(local_cli, options):
    _, articles_out = local_cli
    with pytest.raises(SystemExit) as error:
        cli.main(["articles", "build", *options])
    assert error.value.code == 2
    assert not articles_out.exists()


def test_default_trend_build_migrates_the_legacy_mixed_catalogue(local_cli):
    trends_out, articles_out = local_cli
    (trends_out / "series").mkdir(parents=True)
    (trends_out / "index.json").write_text(json.dumps({
        "series": [{"id": "example-trend"}, {"id": "corporate-profit-share"}],
    }))
    (trends_out / "series/corporate-profit-share.json").write_text("old output")
    assert cli.main(["build"]) == 0
    index = json.loads((trends_out / "index.json").read_text())
    assert index["collection"] == "trends"
    assert [entry["id"] for entry in index["series"]] == ["example-trend"]
    assert not (trends_out / "series/corporate-profit-share.json").exists()
    assert not articles_out.exists()


def test_collection_marker_prevents_replacing_output_with_the_wrong_build(local_cli, tmp_path):
    out = tmp_path / "custom"
    out.mkdir()
    (out / "index.json").write_text(json.dumps({"collection": "trends", "series": []}))
    before = contents(out)
    with pytest.raises(SystemExit) as error:
        cli.main(["articles", "build", "--out", str(out)])
    assert error.value.code == 2
    assert contents(out) == before


@pytest.mark.parametrize("options", [
    ["--from", "2027-01-01"],
    ["--to", "2025-09-03"],
    ["--from", "2026-09-03", "--to", "2026-01-01"],
    ["--from", "2026-02-30", "--to", "2026-09-03"],
    ["--from", "20260101", "--to", "2026-09-03"],
])
@pytest.mark.parametrize("command", ["check", "build"])
def test_article_runs_reject_invalid_overrides(local_cli, monkeypatch, options, command):
    _, out = local_cli
    monkeypatch.setattr(treasury, "fetch", lambda *a, **kw: pytest.fail("must not fetch"))
    with pytest.raises(SystemExit) as error:
        cli.main(["articles", command, "--article", "uncle-sam-has-competition", *options])
    assert error.value.code == 2
    assert not out.exists()


def test_full_build_uses_each_articles_default_window(local_cli):
    _, out = local_cli
    assert cli.main(["articles", "build"]) == 0
    index = json.loads((out / "index.json").read_text())
    for item in index["series"]:
        expected = {"from": "1947-01-01", "to": "2026-04-01"}
        if item["id"].startswith("treasury-"):
            expected = {"from": "2026-01-02", "to": "2026-09-03"}
        elif item["id"] == "effective-tariff-rate":
            expected = {"from": "1992-01-01", "to": "2026-04-01"}
        payload = json.loads((out / item["file"]).read_text())
        assert item["window"] == payload["window"] == expected


@pytest.mark.parametrize("options,start,end,count", [
    (["--from", "2026-01-05"], "2026-01-05", "2026-09-03", 2),
    (["--to", "2026-09-04"], "2026-01-02", "2026-09-04", 4),
])
def test_one_bound_override_preserves_other_default(local_cli, options, start, end, count):
    _, out = local_cli
    defaults = {slug: group.default_window for slug, group in ARTICLES.items()}
    assert cli.main([
        "articles", "build", "--article", "uncle-sam-has-competition", *options,
    ]) == 0
    index = json.loads((out / "index.json").read_text())
    for item in index["series"]:
        payload = json.loads((out / item["file"]).read_text())
        assert item["window"] == payload["window"] == {"from": start, "to": end}
        assert payload["observationCount"] == count
    assert {slug: group.default_window for slug, group in ARTICLES.items()} == defaults


def test_both_bounds_override_every_selected_articles_defaults(local_cli):
    _, out = local_cli
    assert cli.main([
        "articles", "build", "--from", "2026-01-01", "--to", "2026-09-04",
    ]) == 0
    index = json.loads((out / "index.json").read_text())
    assert len(index["series"]) == 6
    for item in index["series"]:
        payload = json.loads((out / item["file"]).read_text())
        assert item["window"] == payload["window"] == {
            "from": "2026-01-01", "to": "2026-09-04",
        }


def test_all_selected_windows_are_validated_before_any_build(local_cli, monkeypatch, capsys):
    _, out = local_cli
    monkeypatch.setattr(cli, "ARTICLE_BUILDERS", {
        series_id: lambda window: pytest.fail("must not build")
        for series_id in ARTICLE_BUILDERS
    })
    # This bound works for both ratio articles, but predates the Treasury start.
    with pytest.raises(SystemExit) as error:
        cli.main(["articles", "build", "--to", "2025-09-03"])
    assert error.value.code == 2
    assert "uncle-sam-has-competition: window start" in capsys.readouterr().err
    assert not out.exists()


def test_treasury_fetches_each_requested_year_and_preserves_boundary_gaps(monkeypatch):
    responses = {
        2024: "Date,10 Yr\n12/31/2024,4.38\n12/30/2024,4.40\n",
        2025: "Date,10 Yr\n01/06/2025,4.62\n01/03/2025,4.60\n01/02/2025,4.45\n",
    }
    requests = []

    def fetch(url, *, name, redistributable):
        year = int(name.removeprefix("treasury-par-yields-").removesuffix(".csv"))
        requests.append(year)
        assert f"/{year}/all?" in url
        return responses[year]

    monkeypatch.setattr(treasury, "fetch", fetch)
    window = DateWindow(date(2024, 12, 31), date(2025, 1, 5))
    series = article.build_10_year(window)
    assert requests == [2024, 2025]
    assert series.observations == [
        Observation(date(2024, 12, 31), 4.38),
        Observation(date(2025, 1, 2), 4.45),
        Observation(date(2025, 1, 3), 4.60),
    ]
    assert series.window == window
    assert len(series.sources) == 2
    assert series.last_date == date(2025, 1, 3)


def test_cli_window_changes_both_treasury_outputs_without_code_changes(local_cli):
    _, out = local_cli
    assert cli.main([
        "articles", "build", "--article", "uncle-sam-has-competition",
        "--from", "2026-01-05", "--to", "2026-09-04",
    ]) == 0
    index = json.loads((out / "index.json").read_text())
    for item in index["series"]:
        payload = json.loads((out / item["file"]).read_text())
        assert payload["firstDate"] == "2026-01-05"
        assert payload["lastDate"] == "2026-09-04"
        assert payload["observationCount"] == 3
        assert item["window"] == payload["window"] == {
            "from": "2026-01-05", "to": "2026-09-04",
        }


@pytest.mark.parametrize("day", ["2026-09-03", "2026-09-05"])
def test_too_short_a_window_leaves_existing_output_untouched(local_cli, day):
    _, out = local_cli
    assert cli.main(["articles", "build"]) == 0
    before = contents(out)
    assert cli.main([
        "articles", "build", "--article", "uncle-sam-has-competition",
        "--from", day, "--to", day,
    ]) == 1
    assert contents(out) == before


def test_window_does_not_hide_invalid_source_values(monkeypatch):
    # The bad row falls after the requested cutoff, but still indicates an
    # invalid source response and must be rejected before filtering.
    monkeypatch.setattr(treasury, "fetch", lambda *a, **kw: CSV.replace("5.24,4.78", "NaN,NaN"))
    with pytest.raises(ValidationError, match="non-finite"):
        article.build_10_year(REFERENCE_WINDOW)


@pytest.mark.parametrize("series_id", [
    "corporate-profit-share", "federal-deficit-share",
    "market-value-per-dollar-of-profit", "effective-tariff-rate",
])
def test_ratio_builders_apply_window_after_calculating_complete_periods(monkeypatch, series_id):
    from market_trends.sources import fred

    def source(series_id):
        if series_id == "BOPGIMP":
            rows = [Observation(date(2025, month, 1), 1000) for month in range(1, 13)]
        else:
            rows = [Observation(date(2025, month, 1), 1000) for month in (1, 4, 7, 10)]
        return rows, Source(series_id, "https://example.org/", "CC0", date(2026, 1, 1))

    monkeypatch.setattr(fred, "series", source)
    window = DateWindow(date(2025, 4, 1), date(2025, 7, 1))
    series = ARTICLE_BUILDERS[series_id](window)
    assert [observation.date for observation in series.observations] == [
        date(2025, 4, 1), date(2025, 7, 1),
    ]
    assert series.window == window
    if series_id == "effective-tariff-rate":
        # The window ends on July 1, but the Q3 calculation must still include
        # August and September imports before selecting the quarter by its date.
        assert [observation.value for observation in series.observations] == [8333.3333, 8333.3333]


@pytest.mark.network
def test_treasury_article_reproduces_quoted_values_from_an_empty_cache(tmp_path, monkeypatch):
    monkeypatch.setattr(cache, "OPEN", tmp_path / "open")
    for maturity, first, july, last in [(10, 4.19, 4.75, 4.77), (30, 4.86, 5.27, 5.25)]:
        series = ARTICLE_BUILDERS[f"treasury-{maturity}-year-yield-2026"](REFERENCE_WINDOW)
        validate(series)
        assert len(series.observations) == 170
        values = {row.date.isoformat(): row.value for row in series.observations}
        assert values["2026-01-02"] == first
        assert values["2026-07-31"] == july
        assert values["2026-09-03"] == last
    assert (tmp_path / "open" / "treasury-par-yields-2026.csv").exists()
