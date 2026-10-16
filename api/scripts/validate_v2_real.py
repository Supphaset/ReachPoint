"""Score flood-model runs against REAL data (not the synthetic scenario).

    python api/scripts/validate_v2_real.py r16 r19 r23

For each run in data/.cache/v2-basin-sim-<run>.{json,bin.gz}:
- gauge X.44: the modelled water level at the gauge cell against RID readings (RMSE, peak level and time);
- 12 news-reported depths (reported-flooding.geojson + exposure.json, 23-25 Nov): distance from the modelled depth
  to the reported range on that day (0 when inside); FABDEM ground errors (~1 m in cities) are part of this;
- Sentinel-1 flood extents (24 Nov, 30 Nov passes): hit rate, false alarms and CSI in open (non built-up) cells only,
  since radar can't see water between buildings.
"""

from __future__ import annotations

import gzip
import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "data" / "hy-2025-11"
CACHE = ROOT / "data" / ".cache"


def inside(x, y, ring):
    hit = False
    for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1]):
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1 + 1e-12) + x1:
            hit = not hit
    return hit


def load(run):
    meta = json.loads((CACHE / f"v2-basin-sim-{run}.json").read_text())
    with gzip.open(CACHE / f"v2-basin-sim-{run}.bin.gz", "rb") as fh:
        raw = np.frombuffer(fh.read(), dtype=np.uint8)
    frames = raw.reshape(meta["hours"] + 1, meta["rows"], meta["cols"]).astype(np.float32) * meta["stepM"]
    return meta, frames


def cell(meta, lon, lat):
    w, s, e, n = meta["bbox"]
    i, j = int((n - lat) / (n - s) * meta["rows"]), int((lon - w) / (e - w) * meta["cols"])
    return (i, j) if 0 <= i < meta["rows"] and 0 <= j < meta["cols"] else None


def score(run):
    meta, fr = load(run)
    start = datetime.fromisoformat(meta["start"])
    hour = lambda iso: (datetime.fromisoformat(iso) - start).total_seconds() / 3600
    # gauge
    g = json.loads((PKG / "gauge-x44.json").read_text())["readings"]
    st = dict((h, v) for h, v in meta["stageX44"])
    errs, obs_peak = [], max(g, key=lambda r: r["levelM"])
    for r in g:
        h = round(hour(r["at"]))
        if h in st:
            errs.append(st[h] - r["levelM"])
    mod_peak_h = max(st, key=st.get)
    gauge = {"rmse": round(float(np.sqrt(np.mean(np.square(errs)))), 2) if errs else None,
             "bias": round(float(np.mean(errs)), 2) if errs else None,
             "peak": [round(st[mod_peak_h], 2), mod_peak_h, round(obs_peak["levelM"], 2), round(hour(obs_peak["at"]))]}
    # news depths
    rep = {f["properties"]["id"]: f for f in json.loads((PKG / "reported-flooding.geojson").read_text())["features"]}
    expo = json.loads((PKG / "exposure.json").read_text())
    rng, ground = expo["reportedDepthM"], expo["groundAtReportM"]
    zv = np.array(meta["zView"]) if "zView" in meta else None
    bv = np.array(meta["builtView"]) if "builtView" in meta else None
    off = meta["params"].get("urbanDemM", 0.0)
    dist, rows = [], []
    for k, (lo, hi) in rng.items():
        f = rep[k]
        lon, lat = f["geometry"]["coordinates"]
        c = cell(meta, lon, lat)
        if not c:
            continue
        day = f["properties"]["reported_on"]
        h0, h1 = hour(day + "T06:00:00+07:00"), hour(day + "T18:00:00+07:00")
        hs = range(max(0, int(h0)), min(meta["hours"], int(h1)) + 1)
        if zv is not None:
            # downscaled: the cell's water surface over the 30 m ground at the point (same urban correction)
            zp = ground[k] - (off if bv[c] else 0.0)
            ds = [max(0.0, float(zv[c] + fr[h][c]) - zp) if fr[h][c] > 0.02 else 0.0 for h in hs]
        else:
            ds = [fr[h][c] for h in hs]
        d = float(np.median(ds)) if ds else 0.0
        e = 0.0 if lo <= d <= hi else (lo - d if d < lo else d - hi)
        dist.append(e)
        rows.append((k, day, lo, hi, round(d, 2)))
    # satellite extents in open cells
    with gzip.open(PKG / "v2-basin.json.gz", "rt") as fh:
        b = json.load(fh)
    sat = []
    for fname, at in (("extent-2025-11-23-o164.geojson", "2025-11-24T06:03:00+07:00"), ("extent-2025-11-29-o164.geojson", "2025-11-30T06:01:00+07:00")):
        h = round(hour(at))
        if h > meta["hours"]:
            continue
        polys = []
        for f in json.loads((PKG / fname).read_text())["features"]:
            gm = f["geometry"]
            for poly in ([gm["coordinates"]] if gm["type"] == "Polygon" else gm["coordinates"]):
                ring = [tuple(p) for p in poly[0]]
                xs, ys = [p[0] for p in ring], [p[1] for p in ring]
                polys.append((min(xs), min(ys), max(xs), max(ys), ring))
        w, s, e, n = meta["bbox"]
        bw, bs, be, bn = b["bbox"]
        lc = np.array(b["landcover"])
        tp = fp = fn = 0
        for i in range(meta["rows"]):
            lat = n - (i + 0.5) * (n - s) / meta["rows"]
            for j in range(meta["cols"]):
                lon = w + (j + 0.5) * (e - w) / meta["cols"]
                bi, bj = int((bn - lat) / (bn - bs) * lc.shape[0]), int((lon - bw) / (be - bw) * lc.shape[1])
                if not (0 <= bi < lc.shape[0] and 0 <= bj < lc.shape[1]) or lc[bi, bj] in (50, 80):
                    continue  # built-up: radar can't see; permanent water: not flood
                obs = any(x0 <= lon <= x1 and y0 <= lat <= y1 and inside(lon, lat, r) for x0, y0, x1, y1, r in polys)
                mod = fr[h][i, j] > 0.1
                tp += obs and mod
                fp += mod and not obs
                fn += obs and not mod
        sat.append({"at": at[:10], "hit": round(tp / max(1, tp + fn), 2), "falseAlarm": round(fp / max(1, tp + fp), 2),
                    "csi": round(tp / max(1, tp + fp + fn), 2)})
    return {"run": run, "params": meta["params"], "gauge": gauge,
            "reports": {"meanDistanceM": round(float(np.mean(dist)), 2), "inside": f"{sum(d == 0 for d in dist)}/{len(dist)}", "rows": rows},
            "satellite": sat, "budget": {k: round(v / 1e6, 1) for k, v in meta["budget"].items()}}


if __name__ == "__main__":
    out = [score(r) for r in sys.argv[1:]]
    for o in out:
        print(json.dumps({k: v for k, v in o.items() if k != "reports"}), "| reports", o["reports"]["meanDistanceM"], o["reports"]["inside"])
        for r in o["reports"]["rows"]:
            print("   ", r)
    (CACHE / "v2-validation.json").write_text(json.dumps(out, indent=1))
