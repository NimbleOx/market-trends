import json
from datetime import date

import pytest

from market_trends import cli
from market_trends.article_series import uncle_sam_has_competition as article
from market_trends.article_series.registry import BUILDERS as ARTICLE_BUILDERS
from market_trends.registry import BUILDERS
from market_trends.schema import Observation, Series, Source, ValidationError, to_dict, validate
from market_trends.sources import cache, treasury

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
    series = ARTICLE_BUILDERS[f"treasury-{maturity}-year-yield-2026"]()
    payload = to_dict(series)
    assert series.first_date == article.START
    assert series.last_date == article.END
    assert payload["frequency"] == "daily"
    assert payload["precision"] == 2
    assert payload["unit"] == "percent"
    assert payload["observationCount"] == 3
    assert series.observations[0].value == first
    assert series.observations[-1].value == last
    assert series.sources[0].url == treasury.PAGE_URL.format(year=2026)


def test_article_refuses_incomplete_coverage(monkeypatch):
    monkeypatch.setattr(treasury, "fetch", lambda *a, **kw: CSV.replace("09/03/2026", "09/02/2026"))
    with pytest.raises(ValidationError, match="must cover"):
        article.build_10_year()


@pytest.mark.parametrize("replacement,error", [
    ("01/02/2026,999,4.85,4.17,3.71", "duplicate"),
    ("01/05/2026,999,4.85,NaN,3.71", "non-finite"),
])
def test_bad_observations_cannot_be_published(monkeypatch, replacement, error):
    csv = CSV.replace("01/05/2026,999,4.85,4.17,3.71", replacement)
    monkeypatch.setattr(treasury, "fetch", lambda *a, **kw: csv)
    with pytest.raises(ValidationError, match=error):
        validate(article.build_10_year())


def test_adapter_refuses_the_wrong_year(monkeypatch):
    monkeypatch.setattr(treasury, "fetch", lambda *a, **kw: CSV.replace("09/04/2026", "09/04/2025"))
    with pytest.raises(ValidationError, match="another year"):
        article.build_10_year()


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
        observations=[Observation(date(2020, 1, 1), 1), Observation(date(2020, 4, 1), 2)],
    )
    monkeypatch.setattr(cli, "BUILDERS", {trend.id: lambda: trend})
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
    monkeypatch.setattr(treasury, "fetch", lambda *a, **kw: CSV.replace("09/03/2026", "09/02/2026"))
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


@pytest.mark.network
def test_treasury_article_reproduces_quoted_values_from_an_empty_cache(tmp_path, monkeypatch):
    monkeypatch.setattr(cache, "OPEN", tmp_path / "open")
    for maturity, first, july, last in [(10, 4.19, 4.75, 4.77), (30, 4.86, 5.27, 5.25)]:
        series = ARTICLE_BUILDERS[f"treasury-{maturity}-year-yield-2026"]()
        validate(series)
        assert len(series.observations) == 170
        values = {row.date.isoformat(): row.value for row in series.observations}
        assert values["2026-01-02"] == first
        assert values["2026-07-31"] == july
        assert values["2026-09-03"] == last
    assert (tmp_path / "open" / "treasury-par-yields-2026.csv").exists()
