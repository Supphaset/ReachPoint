"""Buildings, streets and zones for v2: snap a point to a building, and name a house's neighbours.

Neighbours are named by compass direction (north, south, east, west of the reporter's house): unlike left and right,
it does not depend on which way the person is facing. "unknown" (next door, beside us) takes the nearest building. No GIS library: the city is small
enough for a local flat projection (metres east and north of a fixed origin) and grid buckets.
"""

from __future__ import annotations

import gzip
import json
import math
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from api.v2.names import bilingual, english_name

PKG = Path(__file__).resolve().parents[2] / "data" / "hy-2025-11"
LAT0, LON0 = 7.02, 100.47
MX = 111_320 * math.cos(math.radians(LAT0))
MY = 110_574
DIRECTIONS = ("north", "east", "south", "west")
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
    block_id: str | None = None
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
    blocks: list = field(default_factory=list)   # v2-blocks.geojson features, when present
    sectors: list = field(default_factory=list)  # v2-sectors.geojson: INSARAG-style sectors A, B, C …

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
        """Building ids in each compass direction from b (a 90° sector each, within 60 m), nearest first."""
        out = {d: [] for d in DIRECTIONS}
        scored = []
        for n in self.near(b.x, b.y, 60):
            if n.id == b.id:
                continue
            dx, dy = n.x - b.x, n.y - b.y
            d = math.hypot(dx, dy)
            if d < 2 or d > 60:
                continue
            ang = math.degrees(math.atan2(dx, dy)) % 360          # bearing: 0 north, 90 east
            side = DIRECTIONS[int(((ang + 45) % 360) // 90)]
            scored.append((side, d, n.id))
        for side, d, nid in sorted(scored, key=lambda s: s[1]):
            out[side].append(nid)
        return out

    def neighbour_on(self, b: Building, side: str | None) -> tuple[str | None, bool]:
        """The building in one direction from b, and whether it is a clear match (the nearest one, within 35 m, with
        no other building almost as close in that direction). Without a direction: the nearest building, not sure."""
        sides = self.neighbours(b)
        if side in DIRECTIONS:
            ids = sides[side]
            if not ids:
                return None, False
            d0 = self._dist(b, ids[0])
            sure = d0 <= 35 and (len(ids) == 1 or self._dist(b, ids[1]) - d0 > 4)
            return ids[0], sure
        near = sorted((self._dist(b, i), i) for ids in sides.values() for i in ids)
        return (near[0][1], False) if near else (None, False)

    def _dist(self, b: Building, nid: str) -> float:
        n = self.buildings[nid]
        return math.hypot(n.x - b.x, n.y - b.y)


@lru_cache(maxsize=1)
def load() -> Geo:
    with gzip.open(PKG / "v2-buildings.json.gz", "rt") as fh:
        raw = json.load(fh)
    blds = {r["id"]: Building(r["id"], r["zoneId"], r["c"][0], r["c"][1], r["groundM"], r["areaM2"], r["outline"])
            for r in raw["buildings"]}
    streets = [{"name": f["properties"].get("name"), "nameTh": f["properties"].get("nameTh"), "nameEn": english_name(f["properties"].get("name"), f["properties"].get("name:en") or f["properties"].get("nameEn")), "kind": f["properties"].get("kind"), "coordinates": f["geometry"]["coordinates"]}
               for f in json.loads((PKG / "v2-streets.geojson").read_text())["features"]]
    zfile, afile, bfile = PKG / "v2-zones.geojson", PKG / "v2-zoning.json", PKG / "v2-blocks.geojson"
    if zfile.exists() and afile.exists():
        # zones and blocks along the city's real barriers (data/scripts/build_v2_zoning.py)
        zones = json.loads(zfile.read_text())["features"]
        assign = json.loads(afile.read_text())["assign"]
        blocks = json.loads(bfile.read_text())["features"] if bfile.exists() else []
        zones = bilingual(zones)
        blocks = bilingual(blocks)
        g = Geo(blds, zones, streets)
        g.blocks = blocks
        sfile = PKG / "v2-sectors.geojson"
        g.sectors = bilingual(json.loads(sfile.read_text())["features"]) if sfile.exists() else []
        from shapely.geometry import Point, shape
        shapes = [(z["properties"]["id"], shape(z["geometry"])) for z in zones]
        for b in blds.values():
            z = assign.get(b.id)
            if z:
                b.zone_id, b.block_id = z[0], z[1]
            else:  # on the city's edge, between simplified outlines: the nearest zone
                p = Point(b.lon, b.lat)
                b.zone_id = min(shapes, key=lambda zs: zs[1].distance(p))[0]
        return g
    zones = [z for z in json.loads((PKG / "zones.geojson").read_text())["features"] if z["properties"]["areaId"] == raw["area"]]
    return Geo(blds, zones, streets)
