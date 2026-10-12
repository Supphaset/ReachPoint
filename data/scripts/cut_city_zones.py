"""Cut the city (P-B) into zones and segments along real streets, grouped by the city's 4 districts.

    python data/scripts/cut_city_zones.py --fetch                       # once: cache OSM lines (needs internet)
    python data/scripts/cut_city_zones.py --districts PATH/districts-traced.geojson

How rescue teams cut a search area (research §6): edges a crew can see on the ground (roads,
the railway, canals), pieces of similar workload, and IDs that never change during the event.
So, inside the Hat Yai City Municipality boundary (OpenStreetMap):

1. **Zones**: blocks between main roads (trunk/primary/secondary), the railway, the river and canals.
   Each block goes to the district (เขต 1–4) that holds most of it, and small blocks are merged
   with a neighbour **in the same district**, so every zone sits inside one district.
2. **Segments**: each zone is cut again along tertiary roads; pieces under MIN_SEGMENT_HA merge
   with a neighbour. One generic landmark per segment ("L3 Community building").

The district outlines come from the city's 2022 community map, traced by hand and kept outside the
repo (pass the file with --districts). Only the district *membership* is used, so every edge in the
output is an OpenStreetMap line. The result is written into geography-source.json (P-B zones);
then run build_geography.py. IDs B-1… are kept for the demo scenes (see SCENES).
"""

import argparse
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np
from shapely import set_precision, transform
from shapely.geometry import LineString, Polygon, mapping, shape
from shapely.ops import polygonize, unary_union

DATA_DIR = Path(__file__).resolve().parents[1]
PKG = DATA_DIR / "hy-2025-11"
LINES = PKG / "osm-lines.geojson"
MUNICIPALITY = PKG / "osm-municipality.geojson"
OVERPASS = "https://overpass-api.de/api/interpreter"  # mirror: https://overpass.kumi.systems/api/interpreter
OSM_RELATION = 19981578  # เทศบาลนครหาดใหญ่, Hatyai city municipality
BBOX = (6.98, 100.42, 7.06, 100.52)  # south, west, north, east

ZONE_ROADS = {"trunk", "primary", "secondary"}
SEGMENT_ROADS = ZONE_ROADS | {"tertiary"}
MIN_ZONE_HA = 60
MIN_SEGMENT_HA = 12
MIN_WIDTH_M = {"zone": 40, "segment": 25}  # area / perimeter; removes slivers between dual carriageways
LANDMARK_TYPES = ["Temple", "Market", "Community building", "Mosque", "School", "Health centre", "Shrine"]

# Demo scenes need: B-3 = the hot zone in the centre (most reported flooding, C-01 at L3, L5 school),
# B-4 = a quiet zone with no reports (B-4 · L5), B-5 = the south-west (people stranded, phones down).
SCENES = {"B-3": "most_reports", "B-4": "no_reports", "B-5": "south_west"}


def metres(g):
    return transform(g, lambda xy: xy * np.array([110_487, 110_574]))


def ha(g):
    return metres(g).area / 1e4


def width_m(g):
    m = metres(g)
    return m.area / max(m.length, 1)


def fetch():
    s, w, n, e = BBOX
    query = f"""[out:json][timeout:180];
(way["highway"~"^(trunk|primary|secondary|tertiary)(_link)?$"]({s},{w},{n},{e});
 way["railway"="rail"]({s},{w},{n},{e});
 way["waterway"~"^(river|canal)$"]({s},{w},{n},{e}););
out geom tags;
rel({OSM_RELATION});
out geom;"""
    req = urllib.request.Request(OVERPASS,
                                 data=urllib.parse.urlencode({"data": query}).encode(),
                                 headers={"User-Agent": "ReachPoint-hackathon-prototype/0.1"})
    els = json.load(urllib.request.urlopen(req, timeout=240))["elements"]
    feats, outer = [], []
    for e in els:
        if e["type"] == "way":
            t = e["tags"]
            kind = t.get("highway", "").replace("_link", "") or ("rail" if t.get("railway") else t.get("waterway"))
            coords = [[round(g["lon"], 6), round(g["lat"], 6)] for g in e["geometry"]]
            feats.append({"type": "Feature", "properties": {"kind": kind, "name": t.get("name")},
                          "geometry": {"type": "LineString", "coordinates": coords}})
        elif e["type"] == "relation":
            outer = [LineString([(g["lon"], g["lat"]) for g in m["geometry"]]) for m in e["members"] if m["role"] == "outer"]
    meta = {"attribution": "© OpenStreetMap contributors (ODbL)", "query_bbox": BBOX}
    LINES.write_text(json.dumps({"type": "FeatureCollection", "features": feats, "reachpoint": meta}, ensure_ascii=False))
    muni = max(polygonize(unary_union(outer)), key=lambda p: p.area)
    MUNICIPALITY.write_text(json.dumps({"type": "FeatureCollection", "reachpoint": meta, "features": [
        {"type": "Feature", "properties": {"name": "เทศบาลนครหาดใหญ่", "osm_relation": OSM_RELATION},
         "geometry": mapping(muni)}]}, ensure_ascii=False))
    print(f"cached {len(feats)} lines and the municipality boundary")


def cut(area, lines):
    pieces = polygonize(unary_union(lines + [area.boundary]))
    return [p.intersection(area) for p in pieces if p.representative_point().within(area)]


def merge_small(polys, min_ha, min_width, group=None):
    """Merge pieces under min_ha (or thinner than min_width) into the neighbour they share most edge with.
    With `group`, a piece only merges into a neighbour of the same group."""
    group = group or [0] * len(polys)
    items = [[p, g, ha(p), width_m(p)] for p, g in zip(polys, group) if p.area > 0]
    while True:
        bad = [i for i, it in enumerate(items) if it[2] < min_ha or it[3] < min_width]
        bad = sorted(bad, key=lambda i: items[i][2])
        merged = False
        for i in bad:
            p, g = items[i][0], items[i][1]
            bb = p.buffer(2e-5)
            cand = [j for j, it in enumerate(items) if j != i and it[1] == g and it[0].intersects(bb)]
            if not cand:
                continue
            j = max(cand, key=lambda j: items[j][0].intersection(bb).area)
            q = unary_union([items[j][0], p, bb.intersection(items[j][0].buffer(2e-5))]).buffer(0)
            items[j] = [q, g, ha(q), width_m(q)]
            items.pop(i)
            merged = True
            break
        if not merged:
            return [(it[0], it[1]) for it in items]


def largest_part(g):
    """Snap to a 1e-5° grid (about 1 m, as written to JSON) and keep the largest polygon."""
    g = set_precision(g.buffer(0), 1e-5)
    return max(g.geoms, key=lambda p: p.area) if g.geom_type in ("MultiPolygon", "GeometryCollection") else g


def build(districts_path):
    lines_fc = json.loads(LINES.read_text())["features"]
    muni = shape(json.loads(MUNICIPALITY.read_text())["features"][0]["geometry"]).buffer(0)
    districts = {f["properties"]["id"]: shape(f["geometry"]).buffer(0)
                 for f in json.loads(Path(districts_path).read_text())["features"]}

    def lines(kinds):
        return [shape(f["geometry"]) for f in lines_fc
                if f["properties"]["kind"] in kinds | {"rail", "river", "canal"}]

    def district_of(p):
        overlap = {k: d.intersection(p).area for k, d in districts.items()}
        best = max(overlap, key=overlap.get)
        if overlap[best] > 0:
            return best
        return min(districts, key=lambda k: districts[k].distance(p))  # edge strips the trace missed

    blocks = cut(muni, lines(ZONE_ROADS))
    zones = merge_small(blocks, MIN_ZONE_HA, MIN_WIDTH_M["zone"], [district_of(b) for b in blocks])
    reports = [shape(f["geometry"]) for f in json.loads((PKG / "reported-flooding.geojson").read_text())["features"]]

    out = []
    for z, dist in zones:
        z = largest_part(z.buffer(0))
        segs = [s for s, _ in merge_small(cut(z, lines(SEGMENT_ROADS)), MIN_SEGMENT_HA, MIN_WIDTH_M["segment"])]
        segs = sorted((largest_part(s.buffer(0)) for s in segs), key=lambda s: (-round(s.centroid.y, 3), s.centroid.x))
        out.append({"poly": z, "district": dist, "segs": segs,
                    "reports": sum(z.contains(r) for r in reports)})

    # IDs: scene zones first, the rest north → south, west → east.
    ids = {}
    rest = sorted(range(len(out)), key=lambda i: (-round(out[i]["poly"].centroid.y, 2), out[i]["poly"].centroid.x))
    pick = {
        "most_reports": max(rest, key=lambda i: (out[i]["reports"], len(out[i]["segs"]) >= 5)),
    }
    pick["no_reports"] = max((i for i in rest if out[i]["reports"] == 0 and len(out[i]["segs"]) >= 5 and i not in pick.values()),
                             key=lambda i: -out[i]["poly"].centroid.distance(out[pick["most_reports"]]["poly"].centroid))
    sw = [i for i in rest if i not in pick.values()]
    pick["south_west"] = min(sw, key=lambda i: out[i]["poly"].centroid.x + out[i]["poly"].centroid.y)
    for zid, role in SCENES.items():
        ids[pick[role]] = zid
    n = 1
    for i in rest:
        if i in ids:
            continue
        while f"B-{n}" in SCENES:
            n += 1
        ids[i] = f"B-{n}"
        n += 1

    src_path = PKG / "geography-source.json"
    src = json.loads(src_path.read_text())
    keep = [z for z in src["zones"] if z["area"] != "P-B"]
    city = []
    for i, z in enumerate(out):
        marks = []
        for k, s in enumerate(z["segs"]):
            at = s.representative_point()
            marks.append({"code": f"L{k + 1}", "type": LANDMARK_TYPES[(k + i) % len(LANDMARK_TYPES)],
                          "at": [round(at.x, 5), round(at.y, 5)],
                          "segment": [[round(x, 5), round(y, 5)] for x, y in s.exterior.coords]})
        city.append({"id": ids[i], "area": "P-B", "district": z["district"],
                     "polygon": [[round(x, 5), round(y, 5)] for x, y in z["poly"].exterior.coords],  # holes dropped
                     "landmarks": marks})
    # The scenes name B-3 · L3 Community building, B-3 · L5 School and B-4 · L5 School.
    for zid, code, typ in (("B-3", "L3", "Community building"), ("B-3", "L5", "School"), ("B-4", "L5", "School")):
        zone = next(c for c in city if c["id"] == zid)
        if len(zone["landmarks"]) < int(code[1:]):
            sys.exit(f"{zid} has fewer than {code[1:]} segments; lower MIN_SEGMENT_HA")
        zone["landmarks"][int(code[1:]) - 1]["type"] = typ
    city.sort(key=lambda c: int(c["id"].split("-")[1]))
    src["zones"] = city + keep
    src["version"] += 1
    src["cut"] = {"method": "OSM roads, railway, river and canals; grouped by the city's 4 districts",
                  "zoneRoads": sorted(ZONE_ROADS), "segmentRoads": sorted(SEGMENT_ROADS),
                  "minZoneHa": MIN_ZONE_HA, "minSegmentHa": MIN_SEGMENT_HA}
    src_path.write_text(json.dumps(src, ensure_ascii=False, indent=1) + "\n")
    for c in city:
        print(f"  {c['id']:5} {c['district']}  {len(c['landmarks'])} segments")
    print(f"{len(city)} city zones, {sum(len(c['landmarks']) for c in city)} segments -> {src_path.relative_to(DATA_DIR.parent)}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fetch", action="store_true", help="download and cache the OSM lines and municipality boundary")
    ap.add_argument("--districts", help="traced district outlines (GeoJSON, property id = เขต 1…4)")
    a = ap.parse_args()
    if a.fetch:
        fetch()
    if a.districts:
        build(a.districts)
