import pytest

from market_trends.registry import BUILDERS
from market_trends.schema import validate
from market_trends.sources import cache


@pytest.mark.network
@pytest.mark.parametrize("series_id", sorted(BUILDERS))
def test_every_published_series_builds_and_validates(series_id):
    # Marked network because a cold cache has to fetch. Run the rest with
    # -m "not network".
    series = BUILDERS[series_id]()
    validate(series)
    assert series.observations


@pytest.mark.network
def test_the_buffett_indicator_tracks_the_turning_points_everyone_knows():
    # A guard against a units mistake or a bad join silently shifting the level.
    # These are the peaks and troughs the chart exists to show.
    series = BUILDERS["buffett-indicator"]()
    by_quarter = {o.date.isoformat(): o.value for o in series.observations}

    assert 30 < by_quarter["1982-07-01"] < 45      # the trough before the long bull run
    assert 140 < by_quarter["2000-01-01"] < 180    # dot-com peak
    assert 55 < by_quarter["2009-01-01"] < 85      # financial crisis trough
    assert 190 < by_quarter["2021-10-01"] < 240    # post-pandemic peak


@pytest.mark.network
def test_sp500_in_gold_hits_the_readings_the_chart_exists_to_show():
    # The 1980 gold spike and the 2000 equity peak are the two ends of this
    # chart. If a units mistake or a bad join shifted the ratio, these move.
    series = BUILDERS["sp500-in-gold"]()
    by_month = {o.date.isoformat()[:7]: o.value for o in series.observations}

    assert 0.10 < by_month["1980-01"] < 0.25     # gold at its spike, equities cheap
    assert 4.5 < by_month["1999-12"] < 6.0       # dot-com peak
    assert 0.5 < by_month["2011-08"] < 1.0       # gold's post-crisis top

    # The history the longer gold series opened up. Under the gold standard the
    # ratio is just the index over a pegged $20.67, so these are a check that
    # the splice before 1960 lines up rather than a claim about the market.
    assert 1.2 < by_month["1929-09"] < 1.8       # the month before the crash
    assert 0.15 < by_month["1932-06"] < 0.30     # the Depression trough
    assert series.observations[0].date.year == 1871  # bounded by Shiller now


@pytest.mark.network
@pytest.mark.parametrize("series_id", sorted(BUILDERS))
def test_every_series_builds_from_an_empty_cache(series_id, tmp_path, monkeypatch):
    """Nothing upstream is committed, so a clone must be able to fetch all of it.

    This points the cache at an empty directory, which makes every source go to
    its own upstream rather than reading a file that happens to be lying around
    from an earlier run. A source that quietly stopped being retrievable — a
    moved URL, a feed gone behind a key — fails here rather than on somebody
    else's fresh clone.
    """
    monkeypatch.setattr(cache, "OPEN", tmp_path / "open")
    monkeypatch.setattr(cache, "RESTRICTED", tmp_path / "restricted")

    series = BUILDERS[series_id]()
    validate(series)
    assert series.observations

    # The fetch really did land in the empty cache and not in the repo's.
    written = list(tmp_path.rglob("*"))
    assert [f for f in written if f.is_file()], "built without fetching anything"
