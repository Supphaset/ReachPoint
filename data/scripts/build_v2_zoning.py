"""Zones and blocks that follow the city's real barriers.

    python data/scripts/build_v2_zoning.py

In a flood the railway embankment, the canals and the main roads are walls: water levels, boat routes and walking
routes change across them. So the city area (the 13 v1 zones' outline, where the building outlines were fetched) is
cut along those lines into pieces, and pieces are merged with the neighbour they share the longest edge with until
each zone holds about 2,500-7,000 people; a piece still too big is cut again along secondary, then tertiary roads.
Each zone is then cut the same way into blocks of about 150-700 people along its larger streets. Zones are named
after the main road most of their houses face, blocks after their soi. People per building come from the v1 zone
estimates (WorldPop + DOPA), shared by building footprint.

Writes data/hy-2025-11/v2-zones.geojson (same properties as zones.geojson), v2-blocks.geojson, and
v2-zoning.json (building id -> [zone id, block id]).
"""

from __future__ import annotations

import gzip
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from shapely.geometry import LineString, MultiLineString, Point, mapping, shape
from shapely.ops import polygonize, unary_union
from shapely.strtree import STRtree

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
PKG = ROOT / "data" / "hy-2025-11"
ZONE_MIN, ZONE_MAX = 2500, 7000
BLOCK_MIN, BLOCK_MAX = 150, 700


def lines(features, kinds):
    out = []
    for f in features:
        if f["properties"].get("kind") not in kinds:
            continue
        g = f["geometry"]
        parts = [g["coordinates"]] if g["type"] == "LineString" else g["coordinates"] if g["type"] == "MultiLineString" else []
        out += [LineString(p) for p in parts if len(p) >= 2]
    return out


def cut(poly, cutters, width=3e-5):
    """Split a polygon along lines: take away a thin strip (~3 m) along each line that crosses it, so roads that
    stop a hair short of an edge still separate. Buildings in the strip go to the nearest piece (members())."""
    inner = [l for l in cutters if l.intersects(poly)]
    if not inner:
        return [poly]
    rest = poly.difference(unary_union(inner).buffer(width, cap_style="flat"))
    parts = [g for g in getattr(rest, "geoms", [rest]) if g.geom_type == "Polygon" and g.area > 1e-9]
    return parts or [poly]


NEAR = 1.2e-4     # ~13 m: pieces this close are neighbours (the road strip between them is ~3 m)


def _join(p, q):
    """One connected area from two neighbours: bridge the road strip between them, then shrink back."""
    return unary_union([p.buffer(NEAR / 2), q.buffer(NEAR / 2)]).buffer(-NEAR / 2).buffer(0)


def solid(g, min_ha=2.0):
    """Drop slivers left between road strips: keep parts of at least min_ha (always the largest)."""
    parts = sorted(getattr(g, "geoms", [g]), key=lambda p: -p.area)
    ha = lambda p: p.area * 111_320 * 110_574 / 1e4
    keep = [parts[0]] + [p for p in parts[1:] if ha(p) >= min_ha]
    return unary_union(keep) if len(keep) > 1 else keep[0]


def merge_small(pieces, pop_of, lo, hi):
    """Merge the smallest piece into a neighbour (within ~13 m), preferring one that stays under hi (the smallest
    such), with the longest shared edge as tie-break, until every piece reaches lo."""
    pieces = list(pieces)
    while len(pieces) > 1:
        pops = [pop_of(p) for p in pieces]
        k = int(np.argmin(pops))
        if pops[k] >= lo:
            break
        p = pieces[k]
        pb = p.buffer(NEAR)
        cands = []
        for i, q in enumerate(pieces):
            if i != k and pb.intersects(q):
                edge = pb.intersection(q).area   # how much border they share
                cands.append((pops[i] + pops[k] > hi, pops[i], -edge, i))
        if not cands:  # truly isolated: the nearest piece
            cands = [(False, pops[i], p.distance(q), i) for i, q in enumerate(pieces) if i != k]
        best = min(cands)[3]
        merged = _join(p, pieces[best])
        pieces = [q for i, q in enumerate(pieces) if i not in (k, best)] + [merged]
    return pieces


def split(poly, tiers, pop_of, hi):
    """Cut along the first tier of lines; pieces still too big are cut along the next tier."""
    out = []
    for p in (cut(poly, tiers[0]) if tiers else [poly]):
        out += split(p, tiers[1:], pop_of, hi) if pop_of(p) > hi and len(tiers) > 1 else [p]
    return out


def partition(poly, tiers, pop_of, lo, hi):
    return merge_small(split(poly, tiers, pop_of, hi), pop_of, lo, hi)


KIND_W = {"trunk": 4, "primary": 4, "secondary": 3, "tertiary": 2}
THAI = __import__("re").compile(r"[\u0e00-\u0e7f]")


def zone_scores(mem, street_of, facing):
    """How strongly each street names a zone: houses facing it, weighted by road class; Thai names first."""
    score = Counter()
    for i in mem:
        street_of(i)
        name, kind = facing[i]
        if name:
            score[name] += KIND_W.get(kind, 0.2) * (1.5 if THAI.search(name) else 1.0)
    return score


def main() -> None:
    from api.v2 import geo as G
    geo = G.load()
    zones_v1 = [f for f in json.loads((PKG / "zones.geojson").read_text())["features"] if f["properties"]["areaId"] == "P-B"]
    area = unary_union([shape(f["geometry"]) for f in zones_v1]).buffer(0)
    basin = json.loads((PKG / "v2-basin-lines.geojson").read_text())["features"]
    streets = json.loads((PKG / "v2-streets.geojson").read_text())["features"]
    t1 = lines(basin, {"rail", "canal", "river", "trunk", "primary"}) + lines(streets, {"primary"})
    t2 = lines(streets, {"secondary"})
    t3 = lines(streets, {"tertiary"})
    t4 = lines(streets, {"residential", "unclassified"})

    # people per building: each v1 zone's estimate shared by footprint
    with gzip.open(PKG / "v2-buildings.json.gz", "rt") as fh:
        blds = json.load(fh)["buildings"]
    est = {f["properties"]["id"]: sum(f["properties"]["estimate"]["everyone"]) / 2 for f in zones_v1}
    dist_v1 = {f["properties"]["id"]: f["properties"].get("district") for f in zones_v1}
    area_by_zone = defaultdict(float)
    for b in blds:
        area_by_zone[b["zoneId"]] += b["areaM2"]
    pts = [Point(b["c"]) for b in blds]
    ppl = np.array([est.get(b["zoneId"], 0) * b["areaM2"] / max(1.0, area_by_zone[b["zoneId"]]) for b in blds])
    tree = STRtree(pts)

    def members(poly):
        return [i for i in tree.query(poly) if poly.contains(pts[i])]

    cache = {}

    def pop_of(poly):
        k = poly.wkb
        if k not in cache:
            cache[k] = float(ppl[members(poly)].sum())
        return cache[k]

    zones = [solid(z.buffer(NEAR / 2).buffer(-NEAR / 2 + 3e-5).intersection(area)) for z in partition(area, [t1, t2, t3], pop_of, ZONE_MIN, ZONE_MAX)]
    # number north-west to south-east
    zones.sort(key=lambda p: (-round(p.centroid.y, 3), p.centroid.x))
    facing = {}

    def street_of(i, major=False):
        if i not in facing:
            b = geo.buildings.get(blds[i]["id"])
            f = geo.facing(b) if b else None
            facing[i] = (f.street_th or f.street, f.kind) if f and (f.street_th or f.street) else (None, None)
        name, kind = facing[i]
        if major and kind not in ("primary", "secondary", "tertiary", "trunk"):
            return None
        return name

    # names: the street most its own (many of its houses face it, few elsewhere do), each used once
    scores = [zone_scores(members(zp), street_of, facing) for zp in zones]
    total = Counter()
    for sc in scores:
        total.update(sc)
    names, taken = {}, set()
    ranked = []
    for zi, sc in enumerate(scores, 1):
        for n, v in sc.items():
            ranked.append((v * v / total[n], zi, n))
    for _, zi, n in sorted(ranked, reverse=True):
        if zi not in names and n not in taken:
            names[zi] = n
            taken.add(n)
    # people likely in flooded homes: the flood model's deepest water of the week at each building >= 0.3 m
    meta = json.loads((PKG / "v2-sim.json").read_text())
    with gzip.open(PKG / "v2-sim.bin.gz", "rb") as fh:
        fr = np.frombuffer(fh.read(), np.uint8).reshape(meta["hours"] + 1, meta["rows"], meta["cols"])
    peak = fr.max(axis=0) * meta["stepM"]
    w0, s0, e0, n0 = meta["bbox"]
    flooded = np.array([peak[min(meta["rows"] - 1, max(0, int((n0 - b["c"][1]) / (n0 - s0) * meta["rows"]))),
                             min(meta["cols"] - 1, max(0, int((b["c"][0] - w0) / (e0 - w0) * meta["cols"])))] >= 0.3 for b in blds])
    zf, bf, assign = [], [], {}
    used = Counter()
    for zi, zp in enumerate(zones, 1):
        zid = f"B-{zi}"
        mem = members(zp)
        name = names.get(zi) or zid
        used[name] += 1
        district = Counter(dist_v1.get(blds[i]["zoneId"]) for i in mem).most_common(1)[0][0] if mem else None
        pop = float(ppl[mem].sum())
        blocks = [solid(b.buffer(NEAR / 2).buffer(-NEAR / 2 + 3e-5).intersection(zp), 0.2) for b in partition(zp, [t2, t3, t4], pop_of, BLOCK_MIN, BLOCK_MAX)]
        blocks.sort(key=lambda p: (-round(p.centroid.y, 4), p.centroid.x))
        for bi, bp in enumerate(blocks, 1):
            bid = f"{zid}·{bi}"
            bm = members(bp)
            bname = Counter(n for n in (street_of(i) for i in bm) if n).most_common(1)
            for i in bm:
                assign.setdefault(blds[i]["id"], [zid, bid])
            lp = bp.representative_point()
            bf.append({"type": "Feature", "geometry": mapping(bp.simplify(0.00002)),
                       "properties": {"id": bid, "zoneId": zid, "name": bname[0][0] if bname else None,
                                      "people": int(round(float(ppl[bm].sum()))), "buildings": len(bm), "labelAt": [round(lp.x, 5), round(lp.y, 5)]}})
        lp = zp.representative_point()
        zf.append({"type": "Feature", "geometry": mapping(zp.simplify(0.00003)), "properties": {
            "package": "hy-2025-11", "version": 3, "dataMode": "synthetic", "id": zid, "kind": "zone", "areaId": "P-B",
            "label": name, "name": name, "district": district, "labelAt": [round(lp.x, 5), round(lp.y, 5)],
            "area_m2": int(zp.area * 111_320 * 110_574 * math.cos(math.radians(7.0))), "blocks": len(blocks),
            "estimate": {"everyone": [int(round(pop * 0.85, -2)), int(round(pop * 1.15, -2))], "inSatelliteExtent": [0, 0],
                         "modelledFlooded": [int(round(float(ppl[mem][flooded[mem]].sum()) * 0.8, -1)),
                                             int(round(float(ppl[mem][flooded[mem]].sum()) * 1.2, -1))], "basis": "model"}}})
    for f in zf:  # the same main road can name two zones: say which part
        n = f["properties"]["name"]
        if used[n] > 1:
            same = [g for g in zf if g["properties"]["name"] == n]
            ys = sorted(g["properties"]["labelAt"][1] for g in same)
            part = "เหนือ" if f["properties"]["labelAt"][1] == ys[-1] else "ใต้" if f["properties"]["labelAt"][1] == ys[0] else "กลาง"
            f["properties"]["label"] = f"{n} ({part})"
    meta = {"package": "hy-2025-11", "method": "cut along railway, canals, rivers, trunk and primary roads (OSM); merged to "
            f"{ZONE_MIN}-{ZONE_MAX} people; blocks along secondary, tertiary and residential streets, {BLOCK_MIN}-{BLOCK_MAX} people"}
    (PKG / "v2-zones.geojson").write_text(json.dumps({"type": "FeatureCollection", "meta": meta, "features": zf}, ensure_ascii=False))
    (PKG / "v2-blocks.geojson").write_text(json.dumps({"type": "FeatureCollection", "meta": meta, "features": bf}, ensure_ascii=False))
    (PKG / "v2-zoning.json").write_text(json.dumps({"package": "hy-2025-11", "assign": assign}, separators=(",", ":")))
    parts = [len(getattr(shape(f["geometry"]), "geoms", [0])) for f in zf]
    print("zone parts (1 = one connected area):", parts)
    pz = [sum(f["properties"]["estimate"]["everyone"]) / 2 for f in zf]
    pb = [f["properties"]["people"] for f in bf]
    print(f"{len(zf)} zones, people {min(pz):.0f}-{max(pz):.0f} (median {np.median(pz):.0f}); {len(bf)} blocks, "
          f"people {min(pb)}-{max(pb)} (median {np.median(pb):.0f}); buildings assigned {len(assign)}/{len(blds)}")
    for f in zf:
        p = f["properties"]
        print(" ", p["id"], p["label"], p["district"], p["estimate"]["everyone"], p["blocks"], "blocks")


if __name__ == "__main__":
    main()
