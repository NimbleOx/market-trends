"""Command line: ``trends build``, ``trends check``, ``trends list``."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .emit import write
from .registry import BUILDERS
from .schema import ValidationError, validate

ROOT = Path(__file__).resolve().parents[2]
DIST = ROOT / "dist"


def _build(ids: list[str]):
    for series_id in ids:
        print(f"  building {series_id} ...", end="", flush=True)
        series = BUILDERS[series_id]()
        validate(series)
        print(
            f" {len(series.observations)} observations, "
            f"{series.first_date} to {series.last_date}"
        )
        yield series


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="trends")
    sub = parser.add_subparsers(dest="command", required=True)

    build = sub.add_parser("build", help="compute, validate, and replace generated output")
    build.add_argument(
        "--only", nargs="*", metavar="ID",
        help="limit to these IDs; no IDs selects all; unselected output series are removed",
    )
    build.add_argument(
        "--out", type=Path, default=DIST,
        help="output directory to create or update (default: %(default)s)",
    )

    check = sub.add_parser("check", help="compute and validate without writing output files")
    check.add_argument(
        "--only", nargs="*", metavar="ID", help="limit to these IDs; no IDs selects all"
    )

    sub.add_parser("list", help="list registered series IDs")

    args = parser.parse_args(argv)

    if args.command == "list":
        for series_id in sorted(BUILDERS):
            print(series_id)
        return 0

    ids = sorted(args.only or BUILDERS)
    unknown = [i for i in ids if i not in BUILDERS]
    if unknown:
        print(f"unknown series: {', '.join(unknown)}", file=sys.stderr)
        return 2

    try:
        built = list(_build(ids))
    except ValidationError as error:
        print(f"\nrefused to publish: {error}", file=sys.stderr)
        return 1

    if args.command == "check":
        print("selected series valid; no output files written")
        return 0

    written = write(built, args.out)
    print(f"wrote {len(written)} files to {args.out}")
    return 0
