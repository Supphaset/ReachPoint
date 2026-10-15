"""Buildings, streets and zones for v2: snap a point to a building, and name a house's neighbours.

"Left", "right", "across" and "behind" are as seen standing at the door, looking at the nearest street. That is how
people describe neighbours, and the intake agent asks the question the same way. No GIS library: the city is small
enough for a local flat projection (metres east and north of a fixed origin) and grid buckets.
"""

from __future__ import annotations

import gzip
import json
import math
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

PKG = Path(__file__).resolve().parents[2] / "data" / "hy-2025-11"
LAT0, LON0 = 7.02, 100.47
MX = 111_320 * math.cos(math.radians(LAT0))
MY = 110_574
CELL = 60.0


def to_m(lon: float, lat: float) -> tuple[float, float]:
    return (lon - LON0) * MX, (lat - LAT0) * MY


def to_ll(x: float, y: float) -> tuple[float, float]:
    return x / MX + LON0, y / MY + LAT0


def _inside(pt, ring) -> bool:
    x, y = pt
    inside = False
    for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1]):
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1 + 1e-12) + x1:
            inside = not inside
    return inside


@dataclass
class Building:
    id: str
    zone_id: str
    lon: float
    lat: float
    ground_m: float | None
    area_m2: int
    outline: list[list[float]]
    x: float = 0.0
    y: float = 0.0


@dataclass
class Facing:
    street: str | None          # street name when OSM has one
    street_th: str | None
    kind: str | None
    sx: float                   # nearest point on the street (metres)
    sy: float
    nx: float                   # unit vector from the street to the house
    ny: float
    dist_m: float


@dataclass
class Geo:
    buildings: dict[str, Building]
    zones: list[dict]
    streets: list[dict]
    _bgrid: dict = field(default_factory=dict)
    _sgrid: dict = field(default_factory=dict)

    def __post_init__(self):
        for b in self.buildings.values():
            b.x, b.y = to_m(b.lon, b.lat)
            self._bgrid.setdefault((int(b.x // CELL), int(b.y // CELL)), []).append(b.id)
        for i, s in enumerate(self.streets):
            pts = [to_m(*c) for c in s["coordinates"]]
            s["_m"] = pts
            for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
                n = max(1, int(math.hypot(x2 - x1, y2 - y1) // (CELL / 2)))
                for k in range(n + 1):
                    x, y = x1 + (x2 - x1) * k / n, y1 + (y2 - y1) * k / n
                    self._sgrid.setdefault((int(x // CELL), int(y // CELL)), set()).add(i)

    def near(self, x: float, y: float, r: float) -> list[Building]:
        out = []
        c = int(r // CELL) + 1
        cx, cy = int(x // CELL), int(y // CELL)
        for i in range(cx - c, cx + c + 1):
            for j in range(cy - c, cy + c + 1):
                for bid in self._bgrid.get((i, j), ()):
                    b = self.buildings[bid]
                    if math.hypot(b.x - x, b.y - y) <= r:
                        out.append(b)
        return sorted(out, key=lambda b: math.hypot(b.x - x, b.y - y))

    def zone_at(self, lon: float, lat: float) -> str | None:
        for z in self.zones:
            g = z["geometry"]
            polys = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
            for poly in polys:
                if _inside((lon, lat), [tuple(p) for p in poly[0]]):
                    return z["properties"]["id"]
        return None

    def snap(self, lon: float, lat: float, max_m: float = 40.0) -> Building | None:
        """The building under the point, else the nearest one within max_m."""
        x, y = to_m(lon, lat)
        cands = self.near(x, y, max_m)
        for b in cands[:12]:
            if _inside((lon, lat), [tuple(p) for p in b.outline]):
                return b
        return cands[0] if cands else None

    def facing(self, b: Building) -> Facing | None:
        best = None
        cx, cy = int(b.x // CELL), int(b.y // CELL)
        idx = set()
        for i in range(cx - 2, cx + 3):
            for j in range(cy - 2, cy + 3):
                idx |= self._sgrid.get((i, j), set())
        for i in idx:
            s = self.streets[i]
            if s.get("kind") in ("footway", "pedestrian"):
                continue
            for (x1, y1), (x2, y2) in zip(s["_m"], s["_m"][1:]):
                dx, dy = x2 - x1, y2 - y1
                L2 = dx * dx + dy * dy or 1e-9
                t = max(0.0, min(1.0, ((b.x - x1) * dx + (b.y - y1) * dy) / L2))
                px, py = x1 + t * dx, y1 + t * dy
                d = math.hypot(b.x - px, b.y - py)
                if best is None or d < best[0]:
                    best = (d, px, py, s)
        if best is None:
            return None
        d, px, py, s = best
        nx, ny = ((b.x - px) / d, (b.y - py) / d) if d > 0.5 else (0.0, 1.0)
        return Facing(s.get("name"), s.get("nameTh"), s.get("kind"), px, py, nx, ny, round(d, 1))

    def neighbours(self, b: Building) -> dict[str, list[str]]:
        """Building ids on each side of b, nearest first: left, right, across, behind (as seen from b's door)."""
        f = self.facing(b)
        out = {"left": [], "right": [], "across": [], "behind": []}
        if f is None:
            return out
        fx, fy = -f.nx, -f.ny             # looking at the street
        rx, ry = fy, -fx                  # the person's right hand
        mine = (b.x - f.sx) * f.nx + (b.y - f.sy) * f.ny  # how far b sits back from the street
        scored = []
        for n in self.near(b.x, b.y, 60):
            if n.id == b.id:
                continue
            along = (n.x - b.x) * rx + (n.y - b.y) * ry
            back = (n.x - f.sx) * f.nx + (n.y - f.sy) * f.ny
            if back < -3:                                   # other side of the street
                if abs(along) <= 30 and back > -50:
                    scored.append(("across", abs(along) + abs(back) * 0.3, n.id))
            elif back - mine > 7 and abs(along) <= 12:
                scored.append(("behind", back - mine, n.id))
            elif abs(back - mine) <= 12 and 2 < abs(along) <= 40:
                scored.append(("right" if along > 0 else "left", abs(along), n.id))
        for side, d, nid in sorted(scored, key=lambda s: s[1]):
            out[side].append(nid)
        return out

    def neighbour_on(self, b: Building, side: str) -> tuple[str | None, bool]:
        """The building on one side, and whether it is a clear match. When the strict rules find none, the nearest
        building in roughly that direction (marked not sure)."""
        sides = self.neighbours(b)
        ids = sides.get(side) or (sides.get("left", []) + sides.get("right", []) if side == "next" else [])
        if ids:
            return ids[0], True
        f = self.facing(b)
        if f is None:
            return None, False
        fx, fy = -f.nx, -f.ny
        rx, ry = fy, -fx
        best = None
        for n in self.near(b.x, b.y, 60):
            if n.id == b.id:
                continue
            along = (n.x - b.x) * rx + (n.y - b.y) * ry
            fwd = (n.x - b.x) * fx + (n.y - b.y) * fy
            ok = {"left": along < -2, "right": along > 2, "across": fwd > 5, "behind": fwd < -5, "next": abs(along) > 2}.get(side, True)
            d = math.hypot(n.x - b.x, n.y - b.y)
            if ok and (best is None or d < best[0]):
                best = (d, n.id)
        return (best[1], False) if best else (None, False)


@lru_cache(maxsize=1)
def load() -> Geo:
    with gzip.open(PKG / "v2-buildings.json.gz", "rt") as fh:
        raw = json.load(fh)
    blds = {r["id"]: Building(r["id"], r["zoneId"], r["c"][0], r["c"][1], r["groundM"], r["areaM2"], r["outline"])
            for r in raw["buildings"]}
    zones = [z for z in json.loads((PKG / "zones.geojson").read_text())["features"] if z["properties"]["areaId"] == raw["area"]]
    streets = [{"name": f["properties"].get("name"), "nameTh": f["properties"].get("nameTh"), "kind": f["properties"].get("kind"), "coordinates": f["geometry"]["coordinates"]}
               for f in json.loads((PKG / "v2-streets.geojson").read_text())["features"]]
    return Geo(blds, zones, streets)
