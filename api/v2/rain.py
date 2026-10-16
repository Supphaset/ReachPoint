"""Rain warnings from the flood model: how much the water at a house is expected to rise for forecast rain, and
how soon (data/scripts/build_v2_rain_response.py: one extra-rain model run, used as a linear response)."""

from __future__ import annotations

import json
from functools import lru_cache

from api.v2.geo import PKG

FORECAST_MM = 60.0   # the demo's rain alert: heavy rain, about 60 mm in the next 6 hours
WARN_M = 0.10        # warn a household when the model expects at least this much rise


@lru_cache(maxsize=1)
def load() -> dict | None:
    p = PKG / "v2-rain-response.json"
    return json.loads(p.read_text()) if p.exists() else None


def rise(lon: float, lat: float, mm: float = FORECAST_MM) -> tuple[float, int] | None:
    """(expected rise in m, hours until it peaks) at a point, or None outside the model."""
    r = load()
    if not r:
        return None
    w, s, e, n = r["bbox"]
    i, j = int((n - lat) / (n - s) * r["rows"]), int((lon - w) / (e - w) * r["cols"])
    if not (0 <= i < r["rows"] and 0 <= j < r["cols"]):
        return None
    k = i * r["cols"] + j
    return r["per10mm"][k] / 1000 * mm / 10, r["lagH"][k]
