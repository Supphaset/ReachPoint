"""Shelters: candidate places to go (data/scripts/build_v2_shelters.py), whether a family can walk there now, and
who has checked in. Walking is judged along the direct line from the house, sampling the water every ~40 m (flood
model corrected by nearby reports): walkable only if no stretch is deeper than WALK_M. Streets may differ from the
direct line, so the agent says "about" and never promises a dry route.
"""

from __future__ import annotations

import json
import math
from functools import lru_cache

from api.v2 import geo as G, pipeline as P

WALK_M = 0.5        # above knee-to-thigh water, walking is unsafe (currents, open drains)
STEP_M = 40.0


@lru_cache(maxsize=1)
def load() -> list[dict]:
    p = G.PKG / "v2-shelters.json"
    return json.loads(p.read_text())["shelters"] if p.exists() else []


def by_id(sid: str | None) -> dict | None:
    return next((s for s in load() if s["id"] == sid), None)


def route(w, lon: float, lat: float, s: dict) -> dict:
    x0, y0 = G.to_m(lon, lat)
    x1, y1 = G.to_m(s["lon"], s["lat"])
    dist = math.hypot(x1 - x0, y1 - y0)
    n = max(2, int(dist // STEP_M))
    ds = []
    for k in range(n + 1):
        f = k / n
        lo, la = G.to_ll(x0 + (x1 - x0) * f, y0 + (y1 - y0) * f)
        ds.append(P.local_depth(w, lo, la, w.now_h)[0])
    # a canal crossed on a bridge reads as one very deep sample between shallow ones: not something people wade
    ds = [d for i, d in enumerate(ds) if not (d > 3.0 and min(ds[max(0, i - 1)], ds[min(len(ds) - 1, i + 1)]) < 1.5)] or [0.0]
    deepest, wet = max(ds), sum(d > 0.1 for d in ds)
    return {"shelterId": s["id"], "name": s["name"], "kind": s["kind"], "lon": s["lon"], "lat": s["lat"],
            "km": round(dist / 1000, 1), "deepestM": round(deepest, 2), "wetShare": round(wet / len(ds), 2),
            "walkable": deepest <= WALK_M, "minutes": int(round(dist / 1000 / 3.0 * 60))}


def options(w, lon: float, lat: float, k: int = 3) -> list[dict]:
    """The nearest shelters with their walk check, nearest first; walkable ones before the rest."""
    near = sorted(load(), key=lambda s: math.hypot(*(a - b for a, b in zip(G.to_m(lon, lat), G.to_m(s["lon"], s["lat"])))))[:k]
    out = [route(w, lon, lat, s) for s in near]
    return sorted(out, key=lambda r: (not r["walkable"], r["km"]))


def occupancy(w) -> list[dict]:
    out = []
    for s in load():
        hs = [h for h in w.households.values() if h.shelter_id == s["id"] and h.status in ("atShelter", "toShelter")]
        here = [h for h in hs if h.status == "atShelter"]
        out.append({**s, "households": len(here), "people": sum(h.people or 1 for h in here),
                    "coming": sum(h.people or 1 for h in hs if h.status == "toShelter")})
    return out
