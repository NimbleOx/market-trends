import json
from datetime import date

from market_trends.emit import write
from market_trends.schema import Observation, Series, Source


def a_series(series_id: str = "a-series") -> Series:
    return Series(
        id=series_id,
        title="A series",
        unit="percent",
        precision=1,
        frequency="quarterly",
        description="Something measured over time.",
        sources=[Source("A source", "https://example.org/", "CC BY 4.0", date(2026, 1, 1))],
        observations=[Observation(date(2020, 1, 1), 1.0), Observation(date(2020, 4, 1), 2.0)],
    )


def test_writes_one_observation_per_line(tmp_path):
    # The output is reviewed as a git diff, so a revised month has to show up as
    # one changed line rather than a reflowed blob.
    write([a_series()], tmp_path)
    text = (tmp_path / "series" / "a-series.json").read_text()

    assert '{"date": "2020-01-01", "value": 1.0}' in text
    assert json.loads(text)["observationCount"] == 2


def test_index_lists_every_series(tmp_path):
    write([a_series("b-series"), a_series("a-series")], tmp_path)
    index = json.loads((tmp_path / "index.json").read_text())

    assert [s["id"] for s in index["series"]] == ["a-series", "b-series"]
    assert index["series"][0]["file"] == "series/a-series.json"


def test_a_removed_series_does_not_linger(tmp_path):
    # Otherwise a renamed series keeps being vendored into the site forever.
    write([a_series("old-name")], tmp_path)
    write([a_series("new-name")], tmp_path)

    assert not (tmp_path / "series" / "old-name.json").exists()
    assert (tmp_path / "series" / "new-name.json").exists()
