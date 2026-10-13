"""Point-in-polygon and nearest landmark on the area package (standard library only)."""

from __future__ import annotations

import json
import math
from functools import lru_cache

from api.views.store import ROOT

PACKAGE = ROOT / "data" / "hy-2025-11"


def _rings(geom: dict) -> list[list[list[list[float]]]]:
    if geom["type"] == "Polygon":
        return [geom["coordinates"]]
    if geom["type"] == "MultiPolygon":
        return geom["coordinates"]
    return []


def _in_ring(lon: float, lat: float, ring: list[list[float]]) -> bool:
    inside = False
    j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]
        if (yi > lat) != (yj > lat) and lon < (xj - xi) * (lat - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside


def contains(geom: dict, lon: float, lat: float) -> bool:
    """True when the point is inside the polygon (outer ring) and outside its holes."""
    return any(_in_ring(lon, lat, poly[0]) and not any(_in_ring(lon, lat, h) for h in poly[1:]) for poly in _rings(geom))


@lru_cache(maxsize=None)
def _layer(name: str) -> tuple:
    return tuple(json.loads((PACKAGE / f"{name}.geojson").read_text())["features"])


def metres(a: tuple[float, float], b: tuple[float, float]) -> float:
    """Distance between two (lon, lat) points, equirectangular (fine at city scale)."""
    k = math.cos(math.radians((a[1] + b[1]) / 2))
    return math.hypot((a[0] - b[0]) * k, a[1] - b[1]) * 111_320


def area_of(lon: float, lat: float) -> dict | None:
    return next((f["properties"] for f in _layer("areas") if contains(f["geometry"], lon, lat)), None)


def segment_of(lon: float, lat: float) -> dict | None:
    return next((f["properties"] for f in _layer("segments") if contains(f["geometry"], lon, lat)), None)


def nearest_landmark(lon: float, lat: float, area_id: str | None = None) -> dict:
    marks = [f for f in _layer("landmarks") if f["properties"].get("zoneId") and (area_id is None or f["properties"].get("areaId") == area_id)]
    best = min(marks, key=lambda f: metres((lon, lat), tuple(f["geometry"]["coordinates"])))
    return best["properties"]
