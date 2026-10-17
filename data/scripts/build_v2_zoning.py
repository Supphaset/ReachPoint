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
SECTOR_MIN, SECTOR_MAX = 8000, 16000       # people per sector (level 1)
TEAM_MIN_B, TEAM_MAX_B = 200, 450          # buildings per team zone (level 2): one team, one shift
TEAM_MAX_KM2 = 0.4
TEAM_ALONE_B = 80                          # a piece walled in by main roads/canals may stand alone from this size                         # ~500-650 m across
BLOCK_MIN, BLOCK_MAX = 120, 400            # people per block (level 3)


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
            score[name] += KIND_W.get(kind, 0.2) * (4.0 if THAI.search(name) else 1.0)
    return score


def _midline(poly):
    """A straight line across the middle of a shape's long side."""
    r = poly.minimum_rotated_rectangle
    c = list(r.exterior.coords)[:4]
    long_first = math.dist(c[0], c[1]) >= math.dist(c[1], c[2])
    (a0, a1), (b0, b1) = ((c[0], c[1]), (c[3], c[2])) if long_first else ((c[1], c[2]), (c[0], c[3]))
    m0 = ((a0[0] + a1[0]) / 2, (a0[1] + a1[1]) / 2)
    m1 = ((b0[0] + b1[0]) / 2, (b0[1] + b1[1]) / 2)
    dx, dy = m1[0] - m0[0], m1[1] - m0[1]
    return LineString([(m0[0] - dx, m0[1] - dy), (m1[0] + dx, m1[1] + dy)])


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

    # the flood model's deepest water of the week at each building: for "one kind of water per zone" and estimates
    meta = json.loads((PKG / "v2-sim.json").read_text())
    with gzip.open(PKG / "v2-sim.bin.gz", "rb") as fh:
        fr = np.frombuffer(fh.read(), np.uint8).reshape(meta["hours"] + 1, meta["rows"], meta["cols"])
    peak = fr.max(axis=0) * meta["stepM"]
    w0, s0, e0, n0 = meta["bbox"]
    depth = np.array([peak[min(meta["rows"] - 1, max(0, int((n0 - b["c"][1]) / (n0 - s0) * meta["rows"]))),
                           min(meta["cols"] - 1, max(0, int((b["c"][0] - w0) / (e0 - w0) * meta["cols"])))] for b in blds])
    flooded = depth >= 0.3
    nb_cache = {}

    def nbld(poly):
        k = poly.wkb
        if k not in nb_cache:
            nb_cache[k] = len(members(poly))
        return nb_cache[k]

    def km2(poly):
        return poly.area * 111_320 * 110_574 / 1e6

    def compact(poly):  # Polsby-Popper: 1 for a circle, small for long strips
        return 4 * math.pi * poly.area / max(poly.length ** 2, 1e-12)

    def water_spread(poly):
        d = depth[members(poly)]
        return float(np.percentile(d, 80) - np.percentile(d, 20)) if len(d) >= 10 else 0.0

    # --- level 1, sectors (INSARAG): along railway, canals, rivers and trunk/primary roads; ~8,000-16,000 people
    sectors = [solid(z.buffer(NEAR / 2).buffer(-NEAR / 2 + 3e-5).intersection(area))
               for z in partition(area, [t1, t2], pop_of, SECTOR_MIN, SECTOR_MAX)]
    sectors.sort(key=lambda p: (-round(p.centroid.y, 3), p.centroid.x))

    # --- level 2, team zones: what one team covers in a shift. ~500 m across: 150-450 buildings, at most 0.4 km2,
    # compact, and one kind of water (split where the deepest water of the week varies by more than ~1 m inside)
    def too_big(p):
        return (nbld(p) > TEAM_MAX_B or km2(p) > TEAM_MAX_KM2 or (compact(p) < 0.2 and km2(p) > 0.08)
                or (water_spread(p) > 1.0 and nbld(p) > 2 * TEAM_MIN_B))

    def bisect(poly, depth_left=4):
        """Last resort when no street splits a piece: cut it straight across its long side, in the middle."""
        if depth_left == 0 or not too_big(poly):
            return [poly]
        r = poly.minimum_rotated_rectangle
        c = list(r.exterior.coords)[:4]
        e1 = math.dist(c[0], c[1])
        e2 = math.dist(c[1], c[2])
        (a0, a1), (b0, b1) = ((c[0], c[1]), (c[3], c[2])) if e1 >= e2 else ((c[1], c[2]), (c[0], c[3]))
        m0 = ((a0[0] + a1[0]) / 2, (a0[1] + a1[1]) / 2)
        m1 = ((b0[0] + b1[0]) / 2, (b0[1] + b1[1]) / 2)
        dx, dy = m1[0] - m0[0], m1[1] - m0[1]
        line = LineString([(m0[0] - dx, m0[1] - dy), (m1[0] + dx, m1[1] + dy)])
        parts = cut(poly, [line])
        if len(parts) < 2:
            return [poly]
        return [x for q in parts for x in bisect(q, depth_left - 1)]

    def split_team(poly, tiers):
        out = []
        for q in (cut(poly, tiers[0]) if tiers else [poly]):
            if too_big(q):
                out += split_team(q, tiers[1:]) if len(tiers) > 1 else bisect(q)
            else:
                out.append(q)
        return out

    major = unary_union(t1 + t2)   # railway, canals, rivers, trunk, primary and secondary roads

    def across_major(p, q):
        """Do p and q meet along a main road, canal or the railway (rather than a small street)?"""
        border = p.buffer(NEAR).intersection(q.buffer(NEAR))
        if border.is_empty:
            return False
        return major.intersection(border).length > 0.00035          # ~40 m of main line along their border

    def merge_team(pieces):
        """Grow pieces smaller than one team's shift by joining a neighbour across a small street. Joining across a
        main road, canal or the railway is the last resort (a team works the two sides separately); a piece cut off
        by main lines may stay on its own if it has at least TEAM_ALONE_B buildings."""
        pieces = list(pieces)
        alone = set()
        while len(pieces) > 1:
            sizes = [nbld(q) for q in pieces]
            order = [i for i in np.argsort(sizes) if sizes[i] < TEAM_MIN_B and pieces[i].wkb not in alone]
            if not order:
                break
            k = int(order[0])
            p = pieces[k]
            pb = p.buffer(NEAR)
            cands = []
            for i, q in enumerate(pieces):
                if i != k and pb.intersects(q):
                    j = _join(p, q)
                    cands.append((across_major(p, q), too_big(j), -compact(j), sizes[i], i, j))
            if cands and min(cands, key=lambda c: c[:4])[0] and sizes[k] >= TEAM_ALONE_B:
                alone.add(p.wkb)   # every neighbour is across a main line: keep it as its own small zone
                continue
            if not cands:
                if sizes[k] >= TEAM_ALONE_B:
                    alone.add(p.wkb)
                    continue
                i = min((i for i in range(len(pieces)) if i != k), key=lambda i: p.distance(pieces[i]))
                cands = [(True, False, 0, 0, i, _join(p, pieces[i]))]
            *_, best, joined = min(cands, key=lambda c: c[:4])
            pieces = [q for i, q in enumerate(pieces) if i not in (k, best)] + [joined]
        return pieces

    LETTERS = "ABCDEFGHJKLMNPQRSTUVWXYZ"  # no I or O (INSARAG: not confused with 1 and 0)
    facing = {}

    def street_of(i):
        if i not in facing:
            b = geo.buildings.get(blds[i]["id"])
            f = geo.facing(b) if b else None
            facing[i] = (f.street_th or f.street, f.kind) if f and (f.street_th or f.street) else (None, None)
        return facing[i][0]

    def unique_names(polys):
        """The street most each area's own (many of its houses face it, few elsewhere do), each used once."""
        scores = [zone_scores(members(p), street_of, facing) for p in polys]
        total = Counter()
        for sc in scores:
            total.update(sc)
        names, taken = {}, set()
        for _, k, n in sorted(((v * v / total[n], k, n) for k, sc in enumerate(scores) for n, v in sc.items()), reverse=True):
            if k not in names and n not in taken:
                names[k] = n
                taken.add(n)
        return names

    sector_names = unique_names(sectors)
    teams = []
    for si, sp in enumerate(sectors):
        # every main road, canal and the railway separates team zones (cut always); smaller streets only when needed
        pieces = [x for q in cut(sp, t1 + t2) for x in (split_team(q, [t3, t4]) if too_big(q) else [q])]
        merged = merge_team(pieces)
        # still more than one shift's work after merging: split straight across, without merging back
        final = []
        for z in merged:
            if nbld(z) > TEAM_MAX_B * 1.1:
                halves = cut(z, [_midline(z)])
                final += halves if len(halves) > 1 and min(nbld(h) for h in halves) >= TEAM_ALONE_B else [z]
            else:
                final.append(z)
        # one connected area per zone: a detached bit goes to the nearest zone (its buildings are matched at load)
        tz = [solid(z.buffer(NEAR / 2).buffer(-NEAR / 2 + 3e-5).intersection(sp), 1e9) for z in final]
        tz.sort(key=lambda p: (-round(p.centroid.y, 3), p.centroid.x))
        teams += [(si, k, z) for k, z in enumerate(tz, 1)]
    team_names = unique_names([z for _, _, z in teams])

    zf, bf, sf, assign = [], [], [], {}
    for si, sp in enumerate(sectors):
        mem = members(sp)
        lp = sp.representative_point()
        sf.append({"type": "Feature", "geometry": mapping(sp.simplify(0.00003)), "properties": {
            "id": LETTERS[si], "name": sector_names.get(si), "people": int(round(float(ppl[mem].sum()), -2)),
            "labelAt": [round(lp.x, 5), round(lp.y, 5)]}})
    for ti, (si, k, zp) in enumerate(teams):
        zid = f"{LETTERS[si]}{k}"
        mem = members(zp)
        name = team_names.get(ti) or zid
        district = Counter(dist_v1.get(blds[i]["zoneId"]) for i in mem).most_common(1)[0][0] if mem else None
        pop = float(ppl[mem].sum())
        # level 3, blocks: a few per team zone, by soi, for finding a house and for plans that name a soi
        blocks = [solid(b.buffer(NEAR / 2).buffer(-NEAR / 2 + 3e-5).intersection(zp), 0.1)
                  for b in partition(zp, [t3, t4], pop_of, BLOCK_MIN, BLOCK_MAX)]
        blocks.sort(key=lambda p: (-round(p.centroid.y, 4), p.centroid.x))
        for bi, bp in enumerate(blocks, 1):
            bid = f"{zid}·{bi}"
            bm = members(bp)
            bname = Counter(n for n in (street_of(i) for i in bm) if n).most_common(1)
            for i in bm:
                assign.setdefault(blds[i]["id"], [zid, bid])
            lpb = bp.representative_point()
            bf.append({"type": "Feature", "geometry": mapping(bp.simplify(0.00002)),
                       "properties": {"id": bid, "zoneId": zid, "name": bname[0][0] if bname else None,
                                      "people": int(round(float(ppl[bm].sum()))), "buildings": len(bm), "labelAt": [round(lpb.x, 5), round(lpb.y, 5)]}})
        for i in mem:
            assign.setdefault(blds[i]["id"], [zid, None])
        lp = zp.representative_point()
        d = depth[mem] if mem else np.array([0.0])
        zf.append({"type": "Feature", "geometry": mapping(zp.simplify(0.00003)), "properties": {
            "package": "hy-2025-11", "version": 4, "dataMode": "synthetic", "id": zid, "kind": "zone", "areaId": "P-B",
            "label": name, "name": name, "sector": LETTERS[si], "sectorName": sector_names.get(si), "district": district,
            "labelAt": [round(lp.x, 5), round(lp.y, 5)], "area_m2": int(km2(zp) * 1e6), "buildings": len(mem),
            "blocks": len(blocks), "compactness": round(compact(zp), 2),
            "peakDepthM": [round(float(np.percentile(d, 20)), 2), round(float(np.percentile(d, 80)), 2)],
            "estimate": {"everyone": [int(round(pop * 0.85, -1)), int(round(pop * 1.15, -1))], "inSatelliteExtent": [0, 0],
                         "modelledFlooded": [int(round(float(ppl[mem][flooded[mem]].sum()) * 0.8, -1)),
                                             int(round(float(ppl[mem][flooded[mem]].sum()) * 1.2, -1))], "basis": "model"}}})
    meta = {"package": "hy-2025-11", "method": (
        "INSARAG-style sectors along the railway, canals, rivers and main roads (OSM), lettered A, B, C (no I/O); team "
        f"zones of {TEAM_MIN_B}-{TEAM_MAX_B} buildings and at most {TEAM_MAX_KM2} km2 (one team, one shift), compact, one "
        "kind of water; blocks by soi")}
    (PKG / "v2-sectors.geojson").write_text(json.dumps({"type": "FeatureCollection", "meta": meta, "features": sf}, ensure_ascii=False))
    (PKG / "v2-zones.geojson").write_text(json.dumps({"type": "FeatureCollection", "meta": meta, "features": zf}, ensure_ascii=False))
    (PKG / "v2-blocks.geojson").write_text(json.dumps({"type": "FeatureCollection", "meta": meta, "features": bf}, ensure_ascii=False))
    (PKG / "v2-zoning.json").write_text(json.dumps({"package": "hy-2025-11", "assign": assign}, separators=(",", ":")))
    nb = [f["properties"]["buildings"] for f in zf]
    ar = [f["properties"]["area_m2"] / 1e6 for f in zf]
    cp = [f["properties"]["compactness"] for f in zf]
    parts = sum(len(getattr(shape(f["geometry"]), "geoms", [0])) > 1 for f in zf)
    print(f"{len(sf)} sectors; {len(zf)} team zones: buildings {min(nb)}-{max(nb)} (median {np.median(nb):.0f}), "
          f"area {min(ar):.2f}-{max(ar):.2f} km2 (median {np.median(ar):.2f}), compactness median {np.median(cp):.2f} "
          f"(min {min(cp):.2f}), split zones {parts}; {len(bf)} blocks; buildings assigned {len(assign)}/{len(blds)}")
    for f in sf:
        print(" sector", f["properties"]["id"], f["properties"]["name"], f["properties"]["people"],
              "people,", sum(1 for z in zf if z["properties"]["sector"] == f["properties"]["id"]), "team zones")


if __name__ == "__main__":
    main()
