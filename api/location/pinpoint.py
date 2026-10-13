"""Pinpoint (pin-point.co) Thai geocoding, server side only (D25, decision 0009).

The key lives in PINPOINT_API_KEY (env, or ~/.config/reachpoint/env), never in Git or the browser, and only
synthetic demo addresses are ever sent (docs/collaboration/data-handling.md).

FRIEND: `_request` below is the one place to match the call you tested (URL, parameter names, auth header, and
which fields of the reply hold lat/lon and precision). Everything else (snapping, privacy, fallbacks, tests) is
independent of it. PINPOINT_URL overrides the endpoint without a code change.
"""

from __future__ import annotations

import os
from pathlib import Path

import httpx

TIMEOUT_S = 8


def _config(name: str) -> str | None:
    if os.environ.get(name):
        return os.environ[name].strip()
    f = Path(os.path.expanduser("~/.config/reachpoint/env"))
    if f.is_file():
        for line in f.read_text().splitlines():
            if line.startswith(name + "="):
                return line.split("=", 1)[1].strip() or None
    return None


def configured() -> bool:
    return bool(_config("PINPOINT_API_KEY"))


def _request(text: str, key: str) -> list[dict]:
    """ASSUMED request shape until the friend confirms it: GET {url}?keyword=…&key=… → JSON with a list of results."""
    url = _config("PINPOINT_URL") or "https://api.pin-point.co/v1/geocode"
    r = httpx.get(url, params={"keyword": text, "key": key}, timeout=TIMEOUT_S)
    r.raise_for_status()
    body = r.json()
    items = body if isinstance(body, list) else body.get("data") or body.get("results") or body.get("result") or []
    return items if isinstance(items, list) else [items]


def _point(item: dict) -> tuple[float, float] | None:
    """Accept the usual spellings of a coordinate pair in a geocoder reply."""
    for la, lo in (("lat", "lng"), ("lat", "lon"), ("latitude", "longitude")):
        src = item.get("location") if isinstance(item.get("location"), dict) else item
        if la in src and lo in src:
            return float(src[lo]), float(src[la])
    return None


def geocode(text: str) -> dict | None:
    """Best match as {at: [lon, lat], precision, label}, or None (not configured, no match, or the call failed)."""
    key = _config("PINPOINT_API_KEY")
    if not key:
        return None
    try:
        for item in _request(text, key):
            p = _point(item)
            if p:
                level = str(item.get("level") or item.get("precision") or item.get("type") or "").lower()
                precision = "house" if level in ("house", "address", "building", "rooftop") else "street" if "street" in level or "road" in level else "area"
                return {"at": [p[0], p[1]], "precision": precision, "label": item.get("name") or item.get("address") or text}
    except (httpx.HTTPError, ValueError, KeyError, TypeError):
        return None  # never the key or the address in a log line
    return None
