"""Terrain and land cover for the lower U-Tapao basin around Hat Yai, for a realistic flood model.

    python data/scripts/build_v2_basin.py --project YOUR_EE_PROJECT

The 2025 flood came mostly from rain running off the hills south and west of the city (630 mm in 72 h), not only
from the canal. So the model domain covers the hills, the city and the plain down to Songkhla lake.
Writes data/hy-2025-11/v2-basin.json.gz: FABDEM v1.2 ground (m), ESA WorldCover 2021 class, on a 75 m grid; rows
start at the north edge.
"""

from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path

import ee

PKG = Path(__file__).resolve().parents[1] / "hy-2025-11"
BBOX = [100.30, 6.84, 100.62, 7.17]  # west, south, east, north
SCALE = 75


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    args = ap.parse_args()
    ee.Initialize(project=args.project)
    region = ee.Geometry.Rectangle(BBOX, "EPSG:4326", False)
    proj = ee.Projection("EPSG:32647").atScale(SCALE)
    dem = ee.ImageCollection("projects/sat-io/open-datasets/FABDEM").mosaic().setDefaultProjection("EPSG:4326", None, 30).rename("z").toFloat()
    lc = ee.ImageCollection("ESA/WorldCover/v200").first().rename("lc").toFloat()
    # coarser cells take the mean ground and the most common land cover
    stack = (dem.reduceResolution(ee.Reducer.mean(), maxPixels=64).reproject(proj)
             .addBands(lc.reduceResolution(ee.Reducer.mode(), maxPixels=1024).reproject(proj)))
    arr = stack.sampleRectangle(region=region, defaultValue=-999).getInfo()["properties"]
    z, c = arr["z"][::-1], arr["lc"][::-1]  # Earth Engine returns the south row first
    out = {"package": "hy-2025-11", "bbox": BBOX, "cellM": SCALE, "rows": len(z), "cols": len(z[0]),
           "source": "FABDEM v1.2 (CC BY-NC-SA 4.0); ESA WorldCover 2021 v200 (CC BY 4.0)",
           "z": [[None if v == -999 else round(v, 2) for v in r] for r in z],
           "landcover": [[int(v) if v != -999 else 0 for v in r] for r in c]}
    with gzip.open(PKG / "v2-basin.json.gz", "wt") as fh:
        json.dump(out, fh, separators=(",", ":"))
    zs = [v for r in z for v in r if v != -999]
    print(out["rows"], "x", out["cols"], "cells at", SCALE, "m; ground", round(min(zs), 1), "to", round(max(zs), 1))


if __name__ == "__main__":
    main()
