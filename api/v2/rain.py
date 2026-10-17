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


@lru_cache(maxsize=1)
def _observed() -> dict | None:
    p = PKG / "v2-basin-rain.json"
    return json.loads(p.read_text()) if p.exists() else None


def outlook(now_h: float) -> dict | None:
    """Rain over the basin (mean of the IMERG cells) in the last 6 hours and the next 6 hours.

    The replay has no archived forecast, so "next 6 hours" is the rain that really fell next (NASA GPM IMERG),
    standing in for a forecast and labelled that way. In live use this slot takes a real forecast."""
    from datetime import datetime, timedelta
    from api.v2.pipeline import scenario
    r = _observed()
    if not r or not r.get("cells"):
        return None
    now = datetime.fromisoformat(scenario()["start"]) + timedelta(hours=now_h)
    i = int((now - datetime.fromisoformat(r["start"])).total_seconds() // 3600)

    def mean(a: int, b: int) -> float | None:
        a, b = max(0, a), min(r["hours"], b)
        if a >= b:
            return None
        return round(sum(sum(c["mm"][a:b]) for c in r["cells"]) / len(r["cells"]), 1)

    past, nxt = mean(i - 6, i), mean(i, i + 6)
    heavy = nxt is not None and nxt >= 20
    return {"past6hMm": past, "next6hMm": nxt, "heavy": heavy, "source": r["source"],
            "kind": "replay: rain that fell next, standing in for a forecast"}
