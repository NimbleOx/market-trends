"""Trend commands and a separate ``trends articles`` command group."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .article_series.registry import BUILDERS as ARTICLE_BUILDERS
from .emit import write
from .registry import BUILDERS
from .schema import ValidationError, validate

ROOT = Path(__file__).resolve().parents[2]
DIST = ROOT / "dist-trends"
ARTICLE_DIST = ROOT / "dist-commentary"


def _build(ids: list[str], builders):
    for series_id in ids:
        print(f"  building {series_id} ...", end="", flush=True)
        series = builders[series_id]()
        validate(series)
        print(
            f" {len(series.observations)} observations, "
            f"{series.first_date} to {series.last_date}"
        )
        yield series


def _commands(sub, default_out: Path):
    build = sub.add_parser("build", help="compute, validate, and replace generated output")
    build.add_argument(
        "--only", nargs="*", metavar="ID",
        help="limit to these IDs; no IDs selects all; unselected output series are removed",
    )
    build.add_argument(
        "--out", type=Path, default=default_out,
        help="output directory to create or update (default: %(default)s)",
    )

    check = sub.add_parser("check", help="compute and validate without writing output files")
    check.add_argument(
        "--only", nargs="*", metavar="ID", help="limit to these IDs; no IDs selects all"
    )

    sub.add_parser("list", help="list registered series IDs")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="trends")
    sub = parser.add_subparsers(dest="command", required=True)
    _commands(sub, DIST)
    articles = sub.add_parser("articles", help="build separate, dated article series")
    _commands(articles.add_subparsers(dest="article_command", required=True), ARTICLE_DIST)
    args = parser.parse_args(argv)
    is_article = args.command == "articles"
    command = args.article_command if is_article else args.command
    builders = ARTICLE_BUILDERS if is_article else BUILDERS

    if command == "list":
        for series_id in sorted(builders):
            print(series_id)
        return 0

    ids = sorted(args.only or builders)
    unknown = [i for i in ids if i not in builders]
    if unknown:
        print(f"unknown series: {', '.join(unknown)}", file=sys.stderr)
        return 2

    if command == "build":
        other_root = (DIST if is_article else ARTICLE_DIST).resolve()
        out = args.out.resolve()
        if out == other_root or other_root in out.parents:
            parser.error("article and trend output directories must remain separate")
        index = out / "index.json"
        if index.exists():
            other_builders = BUILDERS if is_article else ARTICLE_BUILDERS
            entries = json.loads(index.read_text(encoding="utf-8")).get("series", [])
            if any(entry["id"] in other_builders for entry in entries):
                parser.error(
                    "output index belongs to the other series collection; use another --out"
                )

    try:
        built = list(_build(ids, builders))
    except ValidationError as error:
        print(f"\nrefused to publish: {error}", file=sys.stderr)
        return 1

    if command == "check":
        print("selected series valid; no output files written")
        return 0

    written = write(built, args.out)
    print(f"wrote {len(written)} files to {args.out}")
    return 0
