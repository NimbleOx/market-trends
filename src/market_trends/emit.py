"""Writing ``dist/``.

The output is vendored into the site and reviewed as a git diff before it goes
live, so the formatting is chosen for diffs rather than for compactness: one
observation per line means a revised month shows up as one changed line instead
of a reflowed blob.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .schema import SCHEMA_VERSION, Series, to_dict


def _dump_series(payload: dict) -> str:
    """JSON with every field on its own line except an observation, which is
    kept to one line each. ``json.dumps`` cannot express that on its own."""
    observations = payload.pop("observations")
    head = json.dumps(payload, indent=2, ensure_ascii=False)

    # Reattach the array by hand, so the closing brace of the head becomes the
    # start of the observations key.
    lines = [
        "  " + json.dumps({"date": o["date"], "value": o["value"]}, ensure_ascii=False)
        for o in observations
    ]
    body = ",\n".join("  " + line for line in lines)

    return f'{head[:-2]},\n  "observations": [\n{body}\n  ]\n}}\n'


def write(series_list: list[Series], out: Path) -> list[Path]:
    """Write every series plus the index. Nothing is written until all of them
    validate, so a failure cannot leave ``dist/`` half updated."""
    payloads = {series.id: to_dict(series) for series in series_list}

    series_dir = out / "series"
    series_dir.mkdir(parents=True, exist_ok=True)

    written: list[Path] = []
    for series in series_list:
        path = series_dir / f"{series.id}.json"
        path.write_text(_dump_series(dict(payloads[series.id])), encoding="utf-8")
        written.append(path)

    index = {
        "schemaVersion": SCHEMA_VERSION,
        "generatedAt": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "series": [
            {
                "id": series.id,
                "title": series.title,
                "unit": series.unit,
                "frequency": series.frequency,
                "scale": series.scale,
                "firstDate": series.first_date.isoformat(),
                "lastDate": series.last_date.isoformat(),
                "observationCount": len(series.observations),
                "file": f"series/{series.id}.json",
            }
            for series in sorted(series_list, key=lambda s: s.id)
        ],
    }
    index_path = out / "index.json"
    index_path.write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    written.append(index_path)

    # Stale files left behind by a renamed or removed series would keep being
    # vendored into the site, so anything not written this run goes.
    for existing in series_dir.glob("*.json"):
        if existing not in written:
            existing.unlink()

    return written
