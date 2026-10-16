"""Hourly rain over the lower U-Tapao basin, 18-30 Nov 2025, on the IMERG 0.1 degree grid.

    python data/scripts/build_v2_basin_rain.py --project YOUR_EE_PROJECT

IMERG (NASA GPM, half-hourly) under-reads intense tropical storms; the Hat Yai rain stations recorded about 630 mm in
19-21 Nov while IMERG gives about half. The model scales IMERG by a factor fitted to that total (see
build_v2_basin_sim.py); this file keeps the satellite values as they are.
Writes data/hy-2025-11/v2-basin-rain.json: cell centres and mm per hour (UTC hours from START).
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import ee

PKG = Path(__file__).resolve().parents[1] / "hy-2025-11"
START = datetime(2025, 11, 18, 0, tzinfo=timezone.utc)
END = datetime(2025, 11, 30, 0, tzinfo=timezone.utc)
BBOX = [100.30, 6.84, 100.62, 7.17]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    args = ap.parse_args()
    ee.Initialize(project=args.project)
    xs = [round(BBOX[0] + 0.05 + 0.1 * i, 2) for i in range(int((BBOX[2] - BBOX[0]) / 0.1) + 1)]
    ys = [round(BBOX[1] + 0.05 + 0.1 * i, 2) for i in range(int((BBOX[3] - BBOX[1]) / 0.1) + 1)]
    pts = ee.FeatureCollection([ee.Feature(ee.Geometry.Point(x, y), {"x": x, "y": y}) for x in xs for y in ys])
    col = ee.ImageCollection("NASA/GPM_L3/IMERG_V07").filterDate(START.isoformat(), END.isoformat()).select("precipitation")
    rows = col.getRegion(pts.geometry(), 11132).getInfo()
    head, body = rows[0], rows[1:]
    ix = {k: head.index(k) for k in ("longitude", "latitude", "time", "precipitation")}
    hours = int((END - START).total_seconds() // 3600)
    cells: dict = {}
    for r in body:
        key = (round(r[ix["longitude"]], 2), round(r[ix["latitude"]], 2))
        h = int((r[ix["time"]] / 1000 - START.timestamp()) // 3600)
        if 0 <= h < hours and r[ix["precipitation"]] is not None:
            cells.setdefault(key, [0.0] * hours)[h] += r[ix["precipitation"]] * 0.5  # mm/h over a half hour
    out = {"package": "hy-2025-11", "start": START.isoformat(), "hours": hours, "source": "NASA GPM IMERG V07 (Earth Engine)",
           "cells": [{"lon": k[0], "lat": k[1], "mm": [round(v, 2) for v in vals]} for k, vals in sorted(cells.items())]}
    (PKG / "v2-basin-rain.json").write_text(json.dumps(out, separators=(",", ":")))
    tot = [sum(c["mm"][24:96]) for c in out["cells"]]
    print(len(out["cells"]), "cells; 19-21 Nov total mm: min", round(min(tot)), "max", round(max(tot)))


if __name__ == "__main__":
    main()
