"""Server-side Pinpoint geocoding, using the verified autocomplete/details flow."""

from __future__ import annotations

import os
import math

import httpx

from api.ai.budget import within

TIMEOUT_S = 8


def _config(name: str) -> str | None:
    if os.environ.get(name):
        return os.environ[name].strip()
    return None


def configured() -> bool:
    return bool(_config("PINPOINT_API_KEY"))


def _request(text: str, key: str) -> list[dict]:
    """Search returns labels and IDs; details resolves the selected ID to a coordinate."""
    base = _config("PINPOINT_URL") or "https://pin-point.co/g/search"
    headers = {"Referer": _config("PINPOINT_REFERER") or "https://pin-point.co"}
    r = httpx.post(f"{base}/autocomplete", data={"keyword": text, "maxResult": "3", "key": key},
                   headers=headers, timeout=TIMEOUT_S)
    r.raise_for_status()
    body = r.json()
    items = body.get("data") if isinstance(body, dict) and body.get("success") is not False else []
    if not isinstance(items, list):
        return []
    details = []
    for item in items:
        identifier = item.get("LocationID") if isinstance(item, dict) else None
        if not isinstance(identifier, str) or not identifier:
            continue
        r = httpx.post(f"{base}/details", data={"locationid": identifier, "key": key},
                       headers=headers, timeout=TIMEOUT_S)
        r.raise_for_status()
        payload = r.json()
        point = payload.get("data") if isinstance(payload, dict) and payload.get("success") is not False else None
        if isinstance(point, dict) and point.get("LocationID") == identifier:
            details.append(point)
    return details


def _point(item: dict) -> tuple[float, float] | None:
    """Accept the usual spellings of a coordinate pair in a geocoder reply."""
    if isinstance(item.get("LAT_LON"), str):
        lat, lon = [float(v.strip()) for v in item["LAT_LON"].split(",")]
        return (lon, lat) if math.isfinite(lat) and math.isfinite(lon) and -90 <= lat <= 90 and -180 <= lon <= 180 else None
    for la, lo in (("lat", "lng"), ("lat", "lon"), ("latitude", "longitude")):
        src = item.get("location") if isinstance(item.get("location"), dict) else item
        if la in src and lo in src:
            lon, lat = float(src[lo]), float(src[la])
            return (lon, lat) if math.isfinite(lat) and math.isfinite(lon) and -90 <= lat <= 90 and -180 <= lon <= 180 else None
    return None


def _geocode(text: str) -> dict | None:
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
                return {"at": [p[0], p[1]], "precision": precision, "label": item.get("FormattedAddress") or item.get("name") or text}
    except (httpx.HTTPError, ValueError, KeyError, TypeError):
        return None  # never the key or the address in a log line
    return None


def geocode(text: str) -> dict | None:
    return within(10, _geocode, text)
