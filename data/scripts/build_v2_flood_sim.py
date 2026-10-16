"""Flood simulation for v2: water from the U-Tapao canal spreading over the real terrain, hour by hour, 21–28 Nov 2025.

    python data/scripts/build_v2_flood_sim.py

A simple diffusive shallow-water model on the 30 m FABDEM grid (v2-terrain.json):
- the canal cells hold water at the real gauge X.44 level (RID), rising gently upstream (0.2 m per km south);
- the real IMERG rainfall over the city falls on every cell, less what soaks in or drains away (60%);
- drains, pumps and soil remove about 1.5 cm per hour everywhere; the canal takes water back as it falls;
- water moves to lower neighbours in proportion to the difference in water surface; the north edge drains to the
  lake. It is a planning picture, not a hydraulic study: no buildings, pipes, pumps or dykes.
Writes data/hy-2025-11/v2-sim.bin.gz (one frame per hour, depth in 2 cm steps, uint8) and v2-sim.json (grid,
frames, and per zone: the simulated water surface and wet share per hour, for the zone cards and the evaluation).
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from api.v2 import geo as G  # noqa: E402

PKG = ROOT / "data" / "hy-2025-11"
TZ = timezone(timedelta(hours=7))
START = datetime(2025, 11, 21, 6, tzinfo=TZ)
HOURS = 168
SUBSTEPS = 24
K = 0.2                 # share of the surface difference that moves per substep
RAIN_KEPT = 0.4         # share of rain that stays on the surface
SLOPE_M_PER_KM = 0.2
GAUGE_LAT = 7.03
STEP_M = 0.02
DRAIN_M_PER_H = 0.015


def gauge_hourly() -> np.ndarray:
    g = json.loads((PKG / "gauge-x44.json").read_text())
    pts = sorted(((datetime.fromisoformat(r["at"]) - START).total_seconds() / 3600, r["levelM"]) for r in g["readings"])
    hs = np.arange(HOURS + 1)
    return np.interp(hs, [p[0] for p in pts], [p[1] for p in pts])


def rain_hourly() -> np.ndarray:
    r = json.loads((PKG / "rain-imerg.json").read_text())["areas"]["P-B"]
    out = np.zeros(HOURS + 1)
    for t, mm in r:
        h = (datetime.fromisoformat(t.replace("Z", "+00:00")) - START).total_seconds() / 3600
        if 0 <= h <= HOURS:
            out[int(h)] += mm
    return out / 1000.0  # metres per hour


def main() -> None:
    t = json.loads((PKG / "v2-terrain.json").read_text())
    rows, cols = t["rows"], t["cols"]
    z = np.array([[np.nan if v is None else v for v in r] for r in t["z"]], dtype=np.float64)
    wall = np.isnan(z)
    z = np.where(wall, 999.0, z)
    canal = np.array(t["canal"], dtype=bool) & ~wall
    w, s, e, n = t["bbox"]
    lats = n - (np.arange(rows) + 0.5) * (n - s) / rows
    lons = w + (np.arange(cols) + 0.5) * (e - w) / cols
    km_south = np.maximum(0.0, (GAUGE_LAT - lats) * 110.574)[:, None] * np.ones((1, cols))
    gauge, rain = gauge_hourly(), rain_hourly()

    h = np.zeros_like(z)
    frames = np.zeros((HOURS + 1, rows, cols), dtype=np.uint8)
    for hour in range(HOURS + 1):
        g0 = gauge[hour]
        g1 = gauge[min(hour + 1, HOURS)]
        for k in range(SUBSTEPS):
            level = g0 + (g1 - g0) * k / SUBSTEPS + SLOPE_M_PER_KM * km_south
            # canal cells sit at the canal level: a source while the canal is high, a sink as it falls
            h[canal] = np.maximum(0.0, level - z)[canal]
            h += rain[hour] * RAIN_KEPT / SUBSTEPS
            eta = z + h
            dh = np.zeros_like(h)
            for axis in (0, 1):
                a = eta[:-1, :] if axis == 0 else eta[:, :-1]
                b = eta[1:, :] if axis == 0 else eta[:, 1:]
                ha = h[:-1, :] if axis == 0 else h[:, :-1]
                hb = h[1:, :] if axis == 0 else h[:, 1:]
                d = a - b
                q = np.where(d > 0, np.minimum(K * d, 0.25 * ha), -np.minimum(K * -d, 0.25 * hb))
                if axis == 0:
                    dh[:-1, :] -= q
                    dh[1:, :] += q
                else:
                    dh[:, :-1] -= q
                    dh[:, 1:] += q
            h = np.maximum(0.0, h + dh)
            h[wall] = 0.0
            h[0, :] *= 0.5  # the north edge drains toward Songkhla lake
            h = np.maximum(0.0, h - DRAIN_M_PER_H / SUBSTEPS)  # drains, pumps and soil
        frames[hour] = np.clip(np.round(h / STEP_M), 0, 255).astype(np.uint8)
        if hour % 24 == 0:
            print(f"hour {hour}: gauge {g0:.2f} m, wet cells {(h > 0.1).sum()}", flush=True)

    # per zone: simulated water surface (median over wet cells) and wet share, every hour
    geo = G.load()
    zone_of = np.full((rows, cols), "", dtype=object)
    for i in range(rows):
        for j in range(cols):
            zone_of[i, j] = geo.zone_at(float(lons[j]), float(lats[i])) or ""
    zones = {}
    for zid in sorted({v for v in zone_of.ravel() if v}):
        m = zone_of == zid
        series = []
        for hour in range(HOURS + 1):
            d = frames[hour][m] * STEP_M
            wet = d > 0.1
            surf = float(np.median((z[m] + d)[wet])) if wet.any() else None
            series.append([hour, None if surf is None else round(surf, 2), round(float(wet.mean()), 3)])
        zones[zid] = series
    import gzip
    with gzip.open(PKG / "v2-sim.bin.gz", "wb", compresslevel=9) as fh:
        fh.write(frames.tobytes())
    meta = {"package": "hy-2025-11", "start": START.isoformat(), "hours": HOURS, "rows": rows, "cols": cols,
            "bbox": t["bbox"], "cellM": t["cellM"], "stepM": STEP_M, "frameBytes": rows * cols,
            "model": "diffusive shallow water on FABDEM 30 m; canal at gauge X.44 (+0.2 m/km upstream); IMERG rain (40% stays)",
            "zones": zones}
    (PKG / "v2-sim.json").write_text(json.dumps(meta, separators=(",", ":")))
    peak = int(np.argmax([f.sum() for f in frames]))
    print("peak wet hour", peak, "max depth", frames.max() * STEP_M, "m; file", frames.nbytes // 1024, "KB")


if __name__ == "__main__":
    main()
