"""Fetch-through cache for upstream responses.

A build reads from the cache, not the network. That makes a rebuild
reproducible, keeps CI from hammering a public dataset, and turns a quiet
upstream revision into a git diff rather than a number that changed for no
visible reason.

Where a response lands depends on whether its source may be redistributed:
``cache/open`` is committed, ``cache/restricted`` is git-ignored and refetched
on a fresh clone. That decision belongs to the source module, which is why it is
a required argument rather than a default.
"""

from __future__ import annotations

import os
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[3]
OPEN = ROOT / "cache" / "open"
RESTRICTED = ROOT / "cache" / "restricted"

TIMEOUT = httpx.Timeout(60.0)
# Some public datasets refuse a default client string.
HEADERS = {"User-Agent": "market-trends (+https://github.com/NimbleOx/market-trends)"}


def path_for(name: str, *, redistributable: bool) -> Path:
    return (OPEN if redistributable else RESTRICTED) / name


def fetch(url: str, *, name: str, redistributable: bool, refresh: bool | None = None) -> str:
    """Return a cached text response, downloading it if absent or if refreshing."""
    return _fetch(url, name=name, redistributable=redistributable, refresh=refresh).decode("utf-8")


def fetch_bytes(url: str, *, name: str, redistributable: bool, refresh: bool | None = None) -> bytes:
    return _fetch(url, name=name, redistributable=redistributable, refresh=refresh)


def _fetch(url: str, *, name: str, redistributable: bool, refresh: bool | None) -> bytes:
    if refresh is None:
        refresh = os.environ.get("TRENDS_REFRESH") == "1"

    target = path_for(name, redistributable=redistributable)
    target.parent.mkdir(parents=True, exist_ok=True)

    if target.exists() and not refresh:
        return target.read_bytes()

    response = httpx.get(url, timeout=TIMEOUT, follow_redirects=True, headers=HEADERS)
    response.raise_for_status()
    target.write_bytes(response.content)

    return response.content
