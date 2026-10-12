"""Build the planning geography for a package: areas → zones → segments around landmarks (C1).

    python data/scripts/build_geography.py hy-2025-11

Reads `<package>/geography-source.json` (zones and landmarks: city zones cut along streets by
cut_city_zones.py, rural zones hand-drawn) and
`<package>/no-satellite-data.geojson` (from `flood_check.py nodata`), and writes:

    areas.geojson       P-A/P-B/P-C, each the union of its zones
    zones.geojson       B-1…B-5 etc.
    districts.geojson   the city's 4 districts (เขต 1–4), each the union of its zones
    segments.geojson    one per landmark, named "B-3 · L5 School": the street-cut piece given in the source,
                        or (rural zones) the part of the zone nearer that landmark than any other
    landmarks.geojson   landmarks and destinations (D1); shared map markers sit here, never at houses
and the C1 fixture `contract/fixtures/areas.<package>.json`: the same IDs without geometry, for the
seed script (`areas/{areaId}`) and the friend's contract tests.

Each segment and zone carries `noSatelliteDataShare`: the share of its area inside the
"no satellite data" mask (D26). The people estimate per segment is added on Tuesday (D27).
Needs shapely (data/requirements.txt). Nothing here runs in the app.
"""

import json
import math
import sys
from pathlib import Path

import numpy as np
from shapely import transform, voronoi_polygons
from shapely.geometry import MultiPoint, Point, Polygon, mapping, shape
from shapely.ops import unary_union
from shapely.validation import make_valid

DATA_DIR = Path(__file__).resolve().parents[1]
LABEL = "Synthetic planning zones and generic landmarks for the demo; not official boundaries or real buildings."


def to_metres(lat0):
    scale = np.array([111_320 * math.cos(math.radians(lat0)), 110_574])  # local metres; fine at city scale
    return lambda xy: xy * scale


def rounded(geom, dp=5):
    return transform(geom, lambda xy: np.round(xy, dp))


def feature(geom, props):
    return {"type": "Feature", "properties": props, "geometry": mapping(rounded(geom))}


def write(path, features, meta):
    doc = {"type": "FeatureCollection", "features": features, "reachpoint": meta}
    path.write_text(json.dumps(doc, ensure_ascii=False, separators=(",", ":")))


def build(package):
    folder = DATA_DIR / package
    src = json.loads((folder / "geography-source.json").read_text())
    nodata = unary_union([make_valid(shape(f["geometry"]))
                          for f in json.loads((folder / "no-satellite-data.geojson").read_text())["features"]])
    lat0 = sum(z["polygon"][0][1] for z in src["zones"]) / len(src["zones"])
    metres = to_metres(lat0)

    def area_m2(g):
        return transform(g, metres).area

    def nodata_share(g):
        return round(area_m2(g.intersection(nodata)) / area_m2(g), 2)

    meta = {"label": LABEL, "package": package, "version": src["version"], "updatedAt": src["updatedAt"],
            "dataMode": "synthetic", "attribution": "Built-up mask: ESA WorldCover 10 m 2021 v200 (CC BY 4.0)"}
    common = {"package": package, "version": src["version"], "dataMode": "synthetic"}
    areas = {a["id"]: {**a, "zones": []} for a in src["areas"]}
    zone_f, seg_f, mark_f, cat_zones = [], [], [], []

    for z in src["zones"]:
        poly = Polygon(z["polygon"])
        district = z.get("district")
        if not poly.is_valid:
            sys.exit(f"{z['id']}: polygon is not valid")
        marks = z["landmarks"]
        pts = [Point(m["at"]) for m in marks]
        for m, p in zip(marks, pts):
            if not poly.contains(p):
                sys.exit(f"{z['id']}-{m['code']}: landmark is outside its zone")
        cells = voronoi_polygons(MultiPoint(pts), extend_to=poly.buffer(0.01))
        seg_ids = []
        for m, p in zip(marks, pts):
            if "segment" in m:  # cut along streets
                cell = Polygon(m["segment"]).intersection(poly)
            else:
                cell = next(c for c in cells.geoms if c.contains(p)).intersection(poly)
            sid = f"{z['id']}-{m['code']}"
            label = f"{z['id']} · {m['code']} {m['type']}"
            seg_ids.append(sid)
            seg_f.append(feature(cell, {**common, "id": sid, "kind": "segment", "zoneId": z["id"], "areaId": z["area"],
                                        "district": district,
                                     "labelAt": [round(c, 5) for c in poly.representative_point().coords[0]], "landmarkId": sid, "label": label, "area_m2": round(area_m2(cell)),
                                        "noSatelliteDataShare": nodata_share(cell)}))
            mark_f.append(feature(p, {**common, "id": sid, "kind": "landmark", "code": m["code"], "type": m["type"],
                                      "zoneId": z["id"], "areaId": z["area"], "segmentId": sid, "label": label}))
        zone_f.append(feature(poly, {**common, "id": z["id"], "kind": "zone", "areaId": z["area"], "label": z["id"],
                                     "district": district,
                                     "labelAt": [round(c, 5) for c in poly.representative_point().coords[0]],
                                     "segmentIds": seg_ids, "area_m2": round(area_m2(poly)),
                                     "noSatelliteDataShare": nodata_share(poly)}))
        areas[z["area"]]["zones"].append(z["id"])
        cat_zones.append({"id": z["id"], "areaId": z["area"], "district": district, "segments": [
            {"id": s, "landmarkId": s, "label": f["properties"]["label"],
             "noSatelliteDataShare": f["properties"]["noSatelliteDataShare"]}
            for s, f in zip(seg_ids, seg_f[-len(seg_ids):])]})

    for d in src["destinations"]:
        mark_f.append(feature(Point(d["at"]), {**common, "id": d["id"], "kind": "destination", "code": d["id"],
                                                "type": d["type"], "zoneId": None, "label": f"{d['id']} {d['type']}"}))

    area_f = []
    for a in areas.values():
        geom = unary_union([Polygon(z["polygon"]) for z in src["zones"] if z["area"] == a["id"]])
        area_f.append(feature(geom, {**common, "id": a["id"], "kind": "area", "need": a["need"], "label": a["label"],
                                     "district": "Hat Yai", "zoneIds": a["zones"]}))

    dist_f = []
    for name in sorted({z["district"] for z in src["zones"] if z.get("district")}):
        geom = unary_union([Polygon(z["polygon"]) for z in src["zones"] if z.get("district") == name]).buffer(1e-6).buffer(-1e-6)
        dist_f.append(feature(geom, {**common, "id": name, "kind": "district",
                                     "label": f"{name} · Hat Yai City Municipality",
                                     "zoneIds": [z["id"] for z in src["zones"] if z.get("district") == name]}))
    write(folder / "districts.geojson", dist_f, {**meta, "label": "Hat Yai City Municipality districts (เขต 1–4), "
                                                 "approximate, from the city's 2022 community map; edges follow OpenStreetMap streets"})
    write(folder / "areas.geojson", area_f, meta)
    write(folder / "zones.geojson", zone_f, meta)
    write(folder / "segments.geojson", seg_f, meta)
    write(folder / "landmarks.geojson", mark_f, meta)
    catalogue = {
        **meta,
        "areas": [{"id": a["id"], "need": a["need"], "label": a["label"], "description": a["description"],
                   "district": "Hat Yai", "zoneIds": a["zones"]} for a in areas.values()],
        "zones": cat_zones,
        "landmarks": [{k: f["properties"][k] for k in ("id", "code", "type", "zoneId", "label")}
                      | {"at": f["geometry"]["coordinates"]} for f in mark_f],
    }
    fixture = DATA_DIR.parent / "contract" / "fixtures" / f"areas.{package}.json"
    fixture.parent.mkdir(parents=True, exist_ok=True)
    fixture.write_text(json.dumps(catalogue, ensure_ascii=False, indent=1) + "\n")
    print(f"{len(area_f)} areas, {len(zone_f)} zones, {len(seg_f)} segments, {len(mark_f)} landmarks + destinations")
    for f in zone_f:
        p = f["properties"]
        print(f"  {p['id']} ({p['areaId']}): {p['area_m2'] / 1e6:.2f} km², {len(p['segmentIds'])} segments, "
              f"{p['noSatelliteDataShare']:.0%} no satellite data")


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else "hy-2025-11")
