"""Building outlines and ground heights for the v2 city zones (Hat Yai, area P-B).

    python data/scripts/build_v2_buildings.py --project YOUR_EE_PROJECT

Writes data/hy-2025-11/v2-buildings.json.gz: one row per Google Open Buildings v3 outline (confidence >= 0.75,
at least 25 m2) inside a P-B zone, with its FABDEM v1.2 ground height. Outlines are rounded to about 1 m.
Tiles keep each Earth Engine request under its 5,000-feature limit.
"""

from __future__ import annotations

import argparse
import gzip
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path

import ee

PKG = Path(__file__).resolve().parents[1] / "hy-2025-11"
TILE_DEG = 0.006  # about 650 m; dense blocks stay under 5,000 outlines


def tiles(bounds):
    x0, y0, x1, y1 = bounds
    x = x0
    while x < x1:
        y = y0
        while y < y1:
            yield [x, y, min(x + TILE_DEG, x1), min(y + TILE_DEG, y1)]
            y += TILE_DEG
        x += TILE_DEG


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--area", default="P-B")
    args = ap.parse_args()
    ee.Initialize(project=args.project)

    zones = [f for f in json.loads((PKG / "zones.geojson").read_text())["features"] if f["properties"]["areaId"] == args.area]
    dem = ee.ImageCollection("projects/sat-io/open-datasets/FABDEM").mosaic().setDefaultProjection("EPSG:4326", None, 30)
    rows, seen = [], set()
    cache = PKG.parent / ".cache" / "v2-buildings"
    cache.mkdir(parents=True, exist_ok=True)
    for z in zones:
        zid = z["properties"]["id"]
        part = cache / f"{zid}.json"
        if part.exists():
            got_rows = json.loads(part.read_text())
            rows += [r for r in got_rows if r["id"] not in seen]
            seen.update(r["id"] for r in got_rows)
            print(zid, len(got_rows), "buildings (cached)", flush=True)
            continue
        geom = ee.Geometry(z["geometry"])
        coords = z["geometry"]["coordinates"]
        ring = coords[0] if z["geometry"]["type"] == "Polygon" else coords[0][0]
        xs, ys = [c[0] for c in ring], [c[1] for c in ring]
        n0 = len(rows)
        def fetch(t):
            box = ee.Geometry.Rectangle(t).intersection(geom, 1)
            fc = (ee.FeatureCollection("GOOGLE/Research/open-buildings/v3/polygons").filterBounds(box)
                  .filter(ee.Filter.gte("confidence", 0.75)).filter(ee.Filter.gte("area_in_meters", 25)))
            fc = fc.map(lambda f: f.setGeometry(f.geometry().simplify(1)).set("c", f.geometry().centroid(1).coordinates()))
            fc = dem.reduceRegions(fc, ee.Reducer.first(), 30)
            return fc.select(["full_plus_code", "area_in_meters", "c", "first"]).getInfo()["features"]

        with ThreadPoolExecutor(8) as pool:
            batches = list(pool.map(fetch, list(tiles([min(xs), min(ys), max(xs), max(ys)]))))
        for got in batches:
            for f in got:
                p = f["properties"]
                lon, lat = p["c"]
                code = p["full_plus_code"]
                if code in seen:
                    continue
                seen.add(code)
                g = f.get("geometry") or {}
                if g.get("type") == "Polygon":
                    ring = g["coordinates"][0]
                elif g.get("type") == "MultiPolygon":
                    ring = g["coordinates"][0][0]
                else:  # simplified away: keep a 6 m square at the centroid
                    d = 0.00003
                    ring = [[lon - d, lat - d], [lon + d, lat - d], [lon + d, lat + d], [lon - d, lat + d], [lon - d, lat - d]]
                rows.append({"id": code, "zoneId": zid, "c": [round(lon, 6), round(lat, 6)],
                             "groundM": None if p.get("first") is None else round(p["first"], 2),
                             "areaM2": round(p["area_in_meters"]), "outline": [[round(x, 5), round(y, 5)] for x, y in ring]})
        part.write_text(json.dumps(rows[n0:]))
        print(zid, len(rows) - n0, "buildings", flush=True)
    out = {"package": "hy-2025-11", "area": args.area,
           "sources": {"buildings": "Google Open Buildings v3 polygons (CC BY 4.0 / ODbL), confidence >= 0.75",
                       "ground": "FABDEM v1.2 bare-earth DEM, 30 m (CC BY-NC-SA 4.0)"},
           "buildings": rows}
    with gzip.open(PKG / "v2-buildings.json.gz", "wt") as f:
        json.dump(out, f, separators=(",", ":"))
    print("total", len(rows))


if __name__ == "__main__":
    main()
