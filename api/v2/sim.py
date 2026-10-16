"""The flood simulation (data/scripts/build_v2_flood_sim.py) for the server: simulated depth at any point and hour.

The Analyst uses it as the first guess. Reports then correct it: each report's gap from the simulation at its own
house is compared with the gaps of the reports around it, and the board shows the corrected picture.
"""

from __future__ import annotations

import gzip
import json
from functools import lru_cache

from api.v2.geo import PKG


@lru_cache(maxsize=1)
def meta() -> dict:
    return json.loads((PKG / "v2-sim.json").read_text())


@lru_cache(maxsize=1)
def frames() -> bytes:
    with gzip.open(PKG / "v2-sim.bin.gz", "rb") as fh:
        return fh.read()


def depth(lon: float, lat: float, h: float) -> float | None:
    """Simulated water depth (m) at a point and hour; None outside the simulated area."""
    m = meta()
    w, s, e, n = m["bbox"]
    i = int((n - lat) / (n - s) * m["rows"])
    j = int((lon - w) / (e - w) * m["cols"])
    if not (0 <= i < m["rows"] and 0 <= j < m["cols"]):
        return None
    raw, fb, C = frames(), m["frameBytes"], m["cols"]
    h0 = max(0, min(m["hours"], int(h)))
    h1 = min(m["hours"], h0 + 1)
    f = max(0.0, min(1.0, h - h0))
    d0, d1 = raw[h0 * fb + i * C + j], raw[h1 * fb + i * C + j]
    return (d0 + (d1 - d0) * f) * m["stepM"]


def ground(lon: float, lat: float) -> float | None:
    """The ground the simulation was downscaled to (FABDEM with street level in built-up blocks), m."""
    m = meta()
    g = m.get("groundDm")
    if not g:
        return None
    w, s, e, n = m["bbox"]
    i, j = int((n - lat) / (n - s) * m["rows"]), int((lon - w) / (e - w) * m["cols"])
    if not (0 <= i < m["rows"] and 0 <= j < m["cols"]) or g[i * m["cols"] + j] <= -9999:
        return None
    return g[i * m["cols"] + j] / 10


def zone_series(zid: str) -> list:
    return meta()["zones"].get(zid, [])


def zone_at(zid: str, h: float) -> tuple[float | None, float]:
    """(simulated median water surface over wet cells, wet share) for a zone at an hour."""
    ser = zone_series(zid)
    if not ser:
        return None, 0.0
    r = ser[max(0, min(len(ser) - 1, int(round(h))))]
    return r[1], r[2]
