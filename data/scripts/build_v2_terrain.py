"""Ground-height grid for the v2 flood simulation (Hat Yai city, area P-B).

    python data/scripts/build_v2_terrain.py --project YOUR_EE_PROJECT

Writes data/hy-2025-11/v2-terrain.json: FABDEM v1.2 bare-earth heights (m above sea level) on a 30 m grid over
the city, plus which cells hold the U-Tapao canal (OSM). The browser runs the flood simulation on this grid.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import ee

PKG = Path(__file__).resolve().parents[1] / "hy-2025-11"
BBOX = [100.426, 6.985, 100.509, 7.051]  # west, south, east, north: area P-B (all 13 city zones) with a margin
SCALE = 30


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    args = ap.parse_args()
    ee.Initialize(project=args.project)
    region = ee.Geometry.Rectangle(BBOX, "EPSG:4326", False)
    dem = ee.ImageCollection("projects/sat-io/open-datasets/FABDEM").mosaic().rename("z")
    # resample to a regular 30 m grid in a local metric projection, then read it as one array
    proj = ee.Projection("EPSG:32647").atScale(SCALE)
    img = dem.reproject(proj).clip(region)
    lines = json.loads((PKG / "osm-lines.geojson").read_text())["features"]
    canals = [f["geometry"]["coordinates"] for f in lines if f["properties"]["kind"] in ("canal", "river")]
    water = ee.Image(0).byte().paint(ee.FeatureCollection([ee.Feature(ee.Geometry.LineString(c)) for c in canals]), 1, 2)
    stack = img.toFloat().addBands(water.rename("canal").toFloat().reproject(proj))
    arr = stack.sampleRectangle(region=region, defaultValue=-999).getInfo()["properties"]
    z, c = arr["z"][::-1], arr["canal"][::-1]  # Earth Engine returns the south row first; row 0 here is north
    rows, cols = len(z), len(z[0])
    out = {"package": "hy-2025-11", "bbox": BBOX, "cellM": SCALE, "rows": rows, "cols": cols,
           "source": "FABDEM v1.2 bare-earth DEM, 30 m (CC BY-NC-SA 4.0); canals from OpenStreetMap (ODbL)",
           "z": [[None if v == -999 else round(v, 2) for v in r] for r in z],
           "canal": [[int(v) for v in r] for r in c]}
    (PKG / "v2-terrain.json").write_text(json.dumps(out, separators=(",", ":")))
    zs = [v for r in z for v in r if v != -999]
    print(rows, "x", cols, "cells; ground", round(min(zs), 1), "to", round(max(zs), 1), "m; canal cells", sum(map(sum, c)))


if __name__ == "__main__":
    main()
