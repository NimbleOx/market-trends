"""Fetch-through cache for upstream responses.

Existing files are reused unless refresh is requested; missing files require
network access. Keeping the same responses preserves calculated observations,
but live upstream URLs and output timestamps prevent byte-for-byte
reproducibility across fresh clones.

The required ``redistributable`` flag routes responses to ``cache/open`` or
``cache/restricted``. Neither contains committed responses. This flag records
a source decision; it does not enforce a publication policy or verify rights.
See ``cache/README.md`` and ``docs/sources.md``.
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


def fetch_bytes(
    url: str, *, name: str, redistributable: bool, refresh: bool | None = None
) -> bytes:
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
