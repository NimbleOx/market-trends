"""Trend commands and a separate ``trends articles`` command group."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

from .commentary.registry import ARTICLES, groups_for, windows_for
from .commentary.registry import BUILDERS as ARTICLE_BUILDERS
from .emit import write
from .registry import BUILDERS
from .schema import DateWindow, ValidationError, validate

ROOT = Path(__file__).resolve().parents[2]
DIST = ROOT / "dist-trends"
ARTICLE_DIST = ROOT / "dist-commentary"


def _build(ids: list[str], builders, windows: dict[str, DateWindow] | None = None):
    for series_id in ids:
        print(f"  building {series_id} ...", end="", flush=True)
        series = (
            builders[series_id](windows[series_id])
            if windows is not None else builders[series_id]()
        )
        validate(series)
        print(
            f" {len(series.observations)} observations, "
            f"{series.first_date} to {series.last_date}"
        )
        yield series


def _date(value: str) -> date:
    try:
        parsed = date.fromisoformat(value)
        if parsed.isoformat() == value:
            return parsed
    except ValueError:
        pass
    raise argparse.ArgumentTypeError("expected a valid date in YYYY-MM-DD format")


def _selection(parser, *, articles: bool):
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument(
        "--only", nargs="*", metavar="ID", help="limit to these IDs; no IDs selects all"
    )
    if articles:
        selection.add_argument(
            "--article", choices=sorted(ARTICLES), metavar="SLUG",
            help="select the commentary datasets belonging to one article; see articles groups",
        )
        parser.add_argument(
            "--from", dest="from_date", type=_date, metavar="YYYY-MM-DD",
            help="override the article's inclusive start date (see articles groups for defaults)",
        )
        parser.add_argument(
            "--to", dest="to_date", type=_date, metavar="YYYY-MM-DD",
            help="override the article's inclusive end date (see articles groups for defaults)",
        )


def _commands(sub, default_out: Path, *, articles: bool = False):
    build = sub.add_parser("build", help="compute, validate, and replace generated output")
    _selection(build, articles=articles)
    build.add_argument(
        "--out", type=Path, default=default_out,
        help="output directory to create or update (default: %(default)s)",
    )

    check = sub.add_parser("check", help="compute and validate without writing output files")
    _selection(check, articles=articles)

    sub.add_parser("list", help="list registered series IDs")
    if articles:
        sub.add_parser("groups", help="list articles, their datasets, and shared trend references")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="trends")
    sub = parser.add_subparsers(dest="command", required=True)
    _commands(sub, DIST)
    articles = sub.add_parser("articles", help="build commentary datasets grouped by article")
    _commands(
        articles.add_subparsers(dest="article_command", required=True),
        ARTICLE_DIST, articles=True,
    )
    args = parser.parse_args(argv)
    is_article = args.command == "articles"
    command = args.article_command if is_article else args.command
    builders = ARTICLE_BUILDERS if is_article else BUILDERS

    if command == "list":
        for series_id in sorted(builders):
            print(series_id)
        return 0

    if command == "groups":
        for article_id, article in sorted(ARTICLES.items()):
            print(f"{article_id} — {article.title}")
            print(
                f"  default window: {article.default_window.start} "
                f"through {article.default_window.end}"
            )
            for series_id in sorted(article.builders):
                print(f"  {series_id}")
            for series_id in article.trend_series:
                print(f"  {series_id} (shared trend; built by trends build)")
        return 0

    selected_article = args.article if is_article else None
    ids = sorted(
        ARTICLES[selected_article].builders if selected_article else args.only or builders
    )
    unknown = [i for i in ids if i not in builders]
    if unknown:
        print(f"unknown series: {', '.join(unknown)}", file=sys.stderr)
        return 2

    windows = None
    if is_article:
        try:
            windows = windows_for(ids, start=args.from_date, end=args.to_date)
        except ValidationError as error:
            parser.error(str(error))

    if command == "build":
        other_root = (DIST if is_article else ARTICLE_DIST).resolve()
        out = args.out.resolve()
        if out == other_root or other_root in out.parents:
            parser.error("article and trend output directories must remain separate")
        index = out / "index.json"
        if index.exists():
            other_builders = BUILDERS if is_article else ARTICLE_BUILDERS
            payload = json.loads(index.read_text(encoding="utf-8"))
            collection = "commentary" if is_article else "trends"
            own_root = (ARTICLE_DIST if is_article else DIST).resolve()
            # Older default indexes predate catalogue ownership metadata. Allow
            # rebuilding them to migrate moved series; custom legacy indexes
            # still use their IDs to prevent accidentally replacing another set.
            owner = payload.get("collection")
            wrong_owner = owner is not None and owner != collection
            wrong_legacy = owner is None and out != own_root and any(
                entry["id"] in other_builders for entry in payload.get("series", [])
            )
            if wrong_owner or wrong_legacy:
                parser.error(
                    "output index belongs to the other series collection; use another --out"
                )

    try:
        built = list(_build(ids, builders, windows))
    except ValidationError as error:
        print(f"\nrefused to publish: {error}", file=sys.stderr)
        return 1

    if command == "check":
        print("selected series valid; no output files written")
        return 0

    written = write(
        built, args.out,
        collection="commentary" if is_article else "trends",
        articles=groups_for(ids) if is_article else None,
    )
    print(f"wrote {len(written)} files to {args.out}")
    return 0
