"""Publish one basin-model run for the app: downscale it to the 30 m city grid and cut it to the scenario's hours.

    python data/scripts/publish_v2_sim.py r19

The basin model runs at 150 m (75 m for the final run). Water surfaces are smooth over that distance, terrain is
not, so the water surface is interpolated to the 30 m FABDEM city grid (v2-terrain.json) and the depth there is
surface minus ground (standard flood downscaling). Writes data/hy-2025-11/v2-sim.json and v2-sim.bin.gz in the
format api/v2/sim.py and the web map already read (hourly, scenario hours 0-168 from 21 Nov 06:00).
"""

from __future__ import annotations

import gzip
import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from api.v2 import geo as G  # noqa: E402
from api.v2 import ground as GR  # noqa: E402

PKG = ROOT / "data" / "hy-2025-11"
CACHE = ROOT / "data" / ".cache"
SCEN_START = datetime.fromisoformat("2025-11-21T06:00:00+07:00")
HOURS = 168
STEP_M = 0.04


def main(run: str, as_truth: bool = False) -> None:
    prefix = (CACHE / "v2-truth-sim") if as_truth else (PKG / "v2-sim")
    meta = json.loads((CACHE / f"v2-basin-sim-{run}.json").read_text())
    with gzip.open(CACHE / f"v2-basin-sim-{run}.bin.gz", "rb") as fh:
        coarse = np.frombuffer(fh.read(), np.uint8).reshape(meta["hours"] + 1, meta["rows"], meta["cols"]).astype(np.float32) * meta["stepM"]
    # coarse ground on the same window, to turn depth into water surface
    with gzip.open(PKG / "v2-basin.json.gz", "rt") as fh:
        b = json.load(fh)
    off = int(round((SCEN_START - datetime.fromisoformat(meta["start"])).total_seconds() / 3600))
    t = json.loads((PKG / "v2-terrain.json").read_text())
    zf = np.array([[np.nan if v is None else v for v in r] for r in t["z"]], dtype=np.float32)
    # the same terrain corrections as the model run, on built-up 30 m cells (WorldCover from the basin grid)
    udem = meta["params"].get("urbanDemM", 0.0)
    built = GR.built_on(np.array(b["landcover"]), b["bbox"], t["bbox"], t["rows"], t["cols"])
    if meta["params"].get("streetGround"):
        zf = GR.street_level(zf, built, float(t["cellM"])).astype(np.float32)
    if udem:
        zf = np.where(built, zf - udem, zf)
    R, C = zf.shape
    w, s, e, n = t["bbox"]
    lat = n - (np.arange(R) + 0.5) * (n - s) / R
    lon = w + (np.arange(C) + 0.5) * (e - w) / C
    cw, cs, ce, cn = meta["bbox"]
    fi = np.clip((cn - lat) / (cn - cs) * meta["rows"] - 0.5, 0, meta["rows"] - 1)
    fj = np.clip((lon - cw) / (ce - cw) * meta["cols"] - 0.5, 0, meta["cols"] - 1)
    i0, j0 = np.floor(fi).astype(int), np.floor(fj).astype(int)
    i1, j1 = np.minimum(i0 + 1, meta["rows"] - 1), np.minimum(j0 + 1, meta["cols"] - 1)
    ai, aj = (fi - i0)[:, None], (fj - j0)[None, :]
    # coarse ground in the window: mean of the fine ground inside each coarse cell (consistent with the model)
    zc = np.full((meta["rows"], meta["cols"]), np.nan, np.float32)
    ci = np.clip(((cn - lat) / (cn - cs) * meta["rows"]).astype(int), 0, meta["rows"] - 1)
    cj = np.clip(((lon - cw) / (ce - cw) * meta["cols"]).astype(int), 0, meta["cols"] - 1)
    sums = np.zeros_like(zc)
    cnts = np.zeros_like(zc)
    for a in range(R):
        for c in range(C):
            if not np.isnan(zf[a, c]):
                sums[ci[a], cj[c]] += zf[a, c]
                cnts[ci[a], cj[c]] += 1
    zc = np.where(cnts > 0, sums / np.maximum(cnts, 1), np.nan)
    frames = np.zeros((HOURS + 1, R, C), np.uint8)
    for k in range(HOURS + 1):
        hc = coarse[min(off + k, meta["hours"])]
        wse = np.where(hc > 0.02, zc + hc, np.nan)
        # interpolate the surface where the coarse cells are wet; a wet cell's surface spreads to its wet neighbours
        q = np.stack([wse[i0][:, j0], wse[i0][:, j1], wse[i1][:, j0], wse[i1][:, j1]])
        wq = np.stack([(1 - ai) * (1 - aj), (1 - ai) * aj, ai * (1 - aj), ai * aj])
        wq = np.where(np.isnan(q), 0, wq)
        surf = np.nansum(np.nan_to_num(q) * wq, axis=0) / np.maximum(wq.sum(axis=0), 1e-6)
        has = wq.sum(axis=0) > 0.25
        d = np.where(has & ~np.isnan(zf), np.maximum(0.0, surf - zf), 0.0)
        frames[k] = np.clip(np.round(d / STEP_M), 0, 255).astype(np.uint8)
    geo = G.load()
    zone_of = np.array([[geo.zone_at(float(lon[j]), float(lat[i])) or "" for j in range(C)] for i in range(R)], dtype=object)
    zones = {}
    for zid in sorted({v for v in zone_of.ravel() if v}):
        m = zone_of == zid
        ser = []
        for k in range(HOURS + 1):
            d = frames[k][m] * STEP_M
            wet = d > 0.1
            surf = float(np.median((zf[m] + d)[wet])) if wet.any() else None
            ser.append([k, None if surf is None else round(surf, 2), round(float(wet.mean()), 3)])
        zones[zid] = ser
    with gzip.open(str(prefix) + ".bin.gz", "wb", compresslevel=9) as fh:
        fh.write(frames.tobytes())
    out = {"package": "hy-2025-11", "start": SCEN_START.isoformat(), "hours": HOURS, "rows": R, "cols": C, "bbox": t["bbox"],
           "cellM": t["cellM"], "stepM": STEP_M, "frameBytes": R * C, "run": run, "params": meta["params"],
           "model": meta["model"] + "; downscaled to FABDEM 30 m by water surface", "stageX44": meta["stageX44"],
           "groundDm": [-9999 if np.isnan(v) else int(round(float(v) * 10)) for v in zf.ravel()],
           "zones": zones}
    pathlib_out = Path(str(prefix) + ".json")
    pathlib_out.write_text(json.dumps(out, separators=(",", ":")))
    peak = max(range(HOURS + 1), key=lambda k: int((frames[k] > 2).sum()))
    print("published", run, "; peak wet hour", peak, "; wet share at peak", round(float((frames[peak] > 2).mean()), 2))


if __name__ == "__main__":
    main(sys.argv[1], as_truth="--truth" in sys.argv)
