"""Shelters: candidate places to go (data/scripts/build_v2_shelters.py), whether a family can walk there now, and
who has checked in. The walk follows the streets (OSM, v2-streets.geojson): the shortest route that avoids deep water
in the flood model, then the water is sampled every ~40 m along it (model corrected by nearby reports). Walkable only
if no stretch is deeper than WALK_M. Water changes by the hour, so the agent says "about" and never promises a dry
route. With no street route, the direct line is used and labelled so.
"""

from __future__ import annotations

from api.v2.names import bilingual_view

import heapq
import json
import math
from functools import lru_cache

from api.v2 import geo as G, pipeline as P, sim as S

WALK_M = 0.5        # above knee-to-thigh water, walking is unsafe (currents, open drains)
STEP_M = 40.0


@lru_cache(maxsize=1)
@bilingual_view
def load() -> list[dict]:
    p = G.PKG / "v2-shelters.json"
    return json.loads(p.read_text())["shelters"] if p.exists() else []


def by_id(sid: str | None) -> dict | None:
    return next((s for s in load() if s["id"] == sid), None)


SNAP_M = 250.0      # how far the house or the shelter may be from the nearest street node
DEEP_COST = 8.0     # each metre of model water multiplies a street's walking cost by (1 + 8·depth): wade less, walk further
WALK_KMH = 3.0      # wading pace


@lru_cache(maxsize=1)
def _streets() -> tuple[list[tuple[float, float]], dict[int, list[tuple[int, float]]]]:
    """The street network as nodes (metres) and edges (length in metres); nodes shared by streets join them."""
    p = G.PKG / "v2-streets.geojson"
    nodes: list[tuple[float, float]] = []
    index: dict[tuple[int, int], int] = {}
    edges: dict[int, list[tuple[int, float]]] = {}

    def node(lon: float, lat: float) -> int:
        x, y = G.to_m(lon, lat)
        k = (round(x), round(y))
        if k not in index:
            index[k] = len(nodes)
            nodes.append((x, y))
        return index[k]

    if not p.exists():
        return nodes, edges
    for f in json.loads(p.read_text())["features"]:
        g = f["geometry"]
        lines = g["coordinates"] if g["type"] == "MultiLineString" else [g["coordinates"]]
        for line in lines:
            ids = [node(lo, la) for lo, la in line]
            for a, b in zip(ids, ids[1:]):
                if a != b:
                    d = math.dist(nodes[a], nodes[b])
                    edges.setdefault(a, []).append((b, d))
                    edges.setdefault(b, []).append((a, d))
    return nodes, edges


def _nearest(x: float, y: float) -> int | None:
    nodes, edges = _streets()
    best, best_d = None, SNAP_M
    for i, (nx, ny) in enumerate(nodes):
        if i in edges:
            d = math.hypot(nx - x, ny - y)
            if d < best_d:
                best, best_d = i, d
    return best


def street_path(w, lon: float, lat: float, s: dict) -> list[tuple[float, float]] | None:
    """Street route from the house to the shelter (lon, lat points), avoiding model water; None if not connected."""
    nodes, edges = _streets()
    a, b = _nearest(*G.to_m(lon, lat)), _nearest(*G.to_m(s["lon"], s["lat"]))
    if a is None or b is None:
        return None
    wet: dict[int, float] = {}

    def depth(i: int) -> float:
        if i not in wet:
            wet[i] = S.depth(*G.to_ll(*nodes[i]), w.now_h) or 0.0
        return wet[i]

    best, prev, todo = {a: 0.0}, {}, [(0.0, a)]
    while todo:
        c, i = heapq.heappop(todo)
        if i == b:
            break
        if c > best.get(i, math.inf):
            continue
        for j, d in edges.get(i, []):
            nc = c + d * (1 + DEEP_COST * min(depth(j), 2.0))
            if nc < best.get(j, math.inf):
                best[j], prev[j] = nc, i
                heapq.heappush(todo, (nc, j))
    if b not in best:
        return None
    path, i = [b], b
    while i != a:
        i = prev[i]
        path.append(i)
    return [(lon, lat)] + [G.to_ll(*nodes[i]) for i in reversed(path)] + [(s["lon"], s["lat"])]


@bilingual_view
def route(w, lon: float, lat: float, s: dict) -> dict:
    line = street_path(w, lon, lat, s)
    by = "streets" if line else "direct line"
    line = line or [(lon, lat), (s["lon"], s["lat"])]
    pts, dist = [], 0.0
    for (lo0, la0), (lo1, la1) in zip(line, line[1:]):
        x0, y0 = G.to_m(lo0, la0)
        x1, y1 = G.to_m(lo1, la1)
        seg = math.hypot(x1 - x0, y1 - y0)
        n = max(1, int(seg // STEP_M))
        for k in range(n):
            pts.append(G.to_ll(x0 + (x1 - x0) * k / n, y0 + (y1 - y0) * k / n))
        dist += seg
    pts.append(line[-1])
    ds = [P.local_depth(w, lo, la, w.now_h)[0] for lo, la in pts]
    # a canal crossed on a bridge reads as one very deep sample between shallow ones: not something people wade
    ds = [d for i, d in enumerate(ds) if not (d > 3.0 and min(ds[max(0, i - 1)], ds[min(len(ds) - 1, i + 1)]) < 1.5)] or [0.0]
    deepest, wet = max(ds), sum(d > 0.1 for d in ds)
    k = max(range(len(ds)), key=ds.__getitem__)
    return {"shelterId": s["id"], "name": s["name"], "nameEn": s.get("nameEn"), "kind": s["kind"], "lon": s["lon"], "lat": s["lat"],
            "km": round(dist / 1000, 1), "deepestM": round(deepest, 2), "wetShare": round(wet / len(ds), 2),
            "walkable": deepest <= WALK_M, "minutes": int(round(dist / 1000 / WALK_KMH * 60)), "by": by,
            # for the map: the route and the water along it (every ~40 m), and where it is deepest
            "path": [[round(lo, 6), round(la, 6)] for lo, la in line],
            "samples": [[round(lo, 6), round(la, 6), round(d, 2)] for (lo, la), d in zip(pts, ds)],
            "deepestAt": [round(pts[min(k, len(pts) - 1)][0], 6), round(pts[min(k, len(pts) - 1)][1], 6)]}


def options(w, lon: float, lat: float, k: int = 3) -> list[dict]:
    """The nearest shelters with their walk check, nearest first; walkable ones before the rest."""
    near = sorted(load(), key=lambda s: math.hypot(*(a - b for a, b in zip(G.to_m(lon, lat), G.to_m(s["lon"], s["lat"])))))[:k]
    out = [route(w, lon, lat, s) for s in near]
    return sorted(out, key=lambda r: (not r["walkable"], r["km"]))


@bilingual_view
def occupancy(w) -> list[dict]:
    out = []
    for s in load():
        hs = [h for h in w.households.values() if h.shelter_id == s["id"] and h.status in ("atShelter", "toShelter")]
        here = [h for h in hs if h.status == "atShelter"]
        out.append({**s, "households": len(here), "people": sum(h.people or 1 for h in here),
                    "coming": sum(h.people or 1 for h in hs if h.status == "toShelter")})
    return out
