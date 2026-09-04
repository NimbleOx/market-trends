import csv
import io
import json
from datetime import date

from market_trends.emit import write
from market_trends.schema import Observation, Series, Source


def a_series(series_id: str = "a-series", observations=None) -> Series:
    return Series(
        id=series_id,
        title="A series",
        unit="percent",
        precision=1,
        frequency="quarterly",
        description="Something measured over time.",
        sources=[Source("A source", "https://example.org/", "CC BY 4.0", date(2026, 1, 1))],
        observations=observations
        or [Observation(date(2020, 1, 1), 1.0), Observation(date(2020, 4, 1), 2.0)],
    )


def test_writes_one_observation_per_line(tmp_path):
    # The output is reviewed as a git diff, so a revised month has to show up as
    # one changed line rather than a reflowed blob.
    write([a_series()], tmp_path)
    text = (tmp_path / "series" / "a-series.json").read_text()

    assert '{"date": "2020-01-01", "value": 1.0}' in text
    assert json.loads(text)["observationCount"] == 2


def test_writes_a_csv_beside_the_json(tmp_path):
    # The observations alone, for a spreadsheet or a dataframe: a header, one
    # row per point, no comment lines, LF endings.
    write([a_series()], tmp_path)
    text = (tmp_path / "series" / "a-series.csv").read_text()

    assert text == "date,value\n2020-01-01,1.0\n2020-04-01,2.0\n"


def test_csv_and_json_carry_the_same_numbers(tmp_path):
    # Both go through the JSON encoder, so a value read back from one file
    # equals the value read back from the other, including the awkward ones.
    awkward = [
        Observation(date(2020, 1, 1), 1 / 3),
        Observation(date(2020, 4, 1), 1e-05),
        Observation(date(2020, 7, 1), 212.3456),
    ]
    write([a_series(observations=awkward)], tmp_path)
    series_dir = tmp_path / "series"

    from_json = [
        (o["date"], o["value"])
        for o in json.loads((series_dir / "a-series.json").read_text())["observations"]
    ]
    from_csv = [
        (row["date"], float(row["value"]))
        for row in csv.DictReader(io.StringIO((series_dir / "a-series.csv").read_text()))
    ]

    assert from_csv == from_json
    assert from_csv[0][1] == 1 / 3


def test_index_lists_every_series(tmp_path):
    write([a_series("b-series"), a_series("a-series")], tmp_path)
    index = json.loads((tmp_path / "index.json").read_text())

    assert [s["id"] for s in index["series"]] == ["a-series", "b-series"]
    assert index["series"][0]["file"] == "series/a-series.json"
    assert index["series"][0]["csv"] == "series/a-series.csv"


def test_a_removed_series_does_not_linger(tmp_path):
    # Otherwise a renamed series keeps being vendored into the site forever,
    # in either format.
    write([a_series("old-name")], tmp_path)
    write([a_series("new-name")], tmp_path)

    for suffix in (".json", ".csv"):
        assert not (tmp_path / "series" / f"old-name{suffix}").exists()
        assert (tmp_path / "series" / f"new-name{suffix}").exists()
