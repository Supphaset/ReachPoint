"""Flood model of the lower U-Tapao basin (Hat Yai), 19-28 Nov 2025: local-inertial shallow water on 75 m terrain.

    python data/scripts/build_v2_basin_sim.py --member base [--rain 1.9 --n-urban 0.12 --inflow 0.5 --out NAME]

Physics (Bates et al. 2010, LISFLOOD-FP "local inertial"), per face between two cells:
    hf = max(etaL, etaR) - max(zL, zR)                       flow depth at the face
    q  = (q - g hf dt (etaR - etaL)/dx) / (1 + g n^2 dt |q| / hf^(7/3))      discharge per metre width (m2/s)
    dt = 0.7 dx / sqrt(g max(h))                              stability (CFL)
Outgoing volume is limited to what a cell holds (no negative depths, no water created).
Inputs:
- terrain: FABDEM v1.2 on 75 m (v2-basin.json.gz); OSM rivers and canals burned in as channels (an uncertain
  parameter, not bathymetry): U-Tapao and R.1 2.5 m, other canals and rivers 1.2 m, streams 0.5 m
- rain: IMERG V07 hourly (v2-basin-rain.json), bilinear to the grid, times a bias factor (IMERG under-reads
  intense storms: stations recorded ~630 mm in 19-21 Nov), losses by SCS curve number (wet antecedent, AMC III)
  from ESA WorldCover land cover
- friction: Manning n by land cover; built-up cells carry the buildings' drag
- city drains: up to 5 mm/h in built-up cells while the canal is below its bank; they back up and stop as the
  canal tops it (gauge X.44 above 7.4 m)
- upstream: the Sadao wave enters where U-Tapao crosses the south edge, a share of the X.44 flow led by 12 h
  (reconstructed: the real inflow was not measured at the edge)
- downstream: the north edge and Songkhla lake hold the water surface at the lake level
Outputs hourly depth frames (uint8, 4 cm steps, max 10.2 m) for the display window over the city, the modelled
water level at gauge X.44 for comparison with the real one, and a water budget.
"""

from __future__ import annotations

import argparse
import gzip
import json
import math
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "data" / "hy-2025-11"
TZ = timezone(timedelta(hours=7))
START = datetime(2025, 11, 19, 0, tzinfo=TZ)   # rain starts
HOURS = 228                                     # to 28 Nov 12:00
G = 9.81
GAUGE_LONLAT = (100.452, 7.004)                 # X.44 Ban Hat Yai Nai: by Wat Hat Yai Nai (OSM 7.0036, 100.4536), approximate
LAKE_M = 1.0
BED0_M = -0.5     # U-Tapao bed at the gauge (m above sea level)
BED_SLOPE = 0.35  # bed rise upstream, m per km
VIEW = [100.426, 6.985, 100.509, 7.051]         # the city display window (same as v2-terrain)
STEP_M = 0.04
CFL = 0.5
FROUDE = 1.0

# ESA WorldCover classes -> Manning n and SCS curve number (AMC II)
LC = {10: (0.10, 70), 20: (0.07, 74), 30: (0.05, 79), 40: (0.06, 81), 50: (0.12, 95), 60: (0.035, 86),
      70: (0.03, 98), 80: (0.03, 100), 90: (0.06, 90), 95: (0.08, 90), 100: (0.05, 80), 0: (0.05, 80)}


def load(coarsen: int = 1):
    with gzip.open(PKG / "v2-basin.json.gz", "rt") as fh:
        b = json.load(fh)
    z = np.array([[np.nan if v is None else v for v in r] for r in b["z"]], dtype=np.float64)
    lc = np.array(b["landcover"], dtype=np.int32)
    if coarsen > 1:
        k = coarsen
        R, C = (z.shape[0] // k) * k, (z.shape[1] // k) * k
        w, s, e, n = b["bbox"]
        e2 = w + (e - w) * C / z.shape[1]
        s2 = n - (n - s) * R / z.shape[0]
        zz = z[:R, :C].reshape(R // k, k, C // k, k)
        z = np.nanmean(zz, axis=(1, 3))
        ll = lc[:R, :C].reshape(R // k, k, C // k, k).transpose(0, 2, 1, 3).reshape(R // k, C // k, k * k)
        lc = np.apply_along_axis(lambda v: np.bincount(v).argmax(), 2, ll)
        b = {**b, "bbox": [w, s2, e2, n], "cellM": b["cellM"] * k, "rows": R // k, "cols": C // k}
    return b, z, lc


def lonlat_grid(b):
    w, s, e, n = b["bbox"]
    R, C = b["rows"], b["cols"]
    lat = n - (np.arange(R) + 0.5) * (n - s) / R
    lon = w + (np.arange(C) + 0.5) * (e - w) / C
    return lon, lat


def burn_channels(b, z):
    """Rasterise OSM rivers and canals; returns burn depth per cell and a mask of the main U-Tapao."""
    w, s, e, n = b["bbox"]
    R, C = b["rows"], b["cols"]
    depth = np.zeros_like(z)
    utapao = np.zeros(z.shape, dtype=bool)
    lines = json.loads((PKG / "v2-basin-lines.geojson").read_text())["features"]
    for f in lines:
        p = f["properties"]
        kind, name = p["kind"], (p.get("name") or "") + (p.get("nameTh") or "")
        if kind not in ("river", "canal", "stream", "drain"):
            continue
        main = "อู่ตะเภา" in name or "U-Tapao" in name or "U Taphao" in name
        d = 2.5 if (main or "ร.1" in name) else (1.2 if kind in ("river", "canal") else 0.5)
        pts = f["geometry"]["coordinates"]
        for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
            steps = max(2, int(math.hypot((x2 - x1) * 110_000, (y2 - y1) * 110_000) / 25))
            for k in range(steps + 1):
                x, y = x1 + (x2 - x1) * k / steps, y1 + (y2 - y1) * k / steps
                i, j = int((n - y) / (n - s) * R), int((x - w) / (e - w) * C)
                if 0 <= i < R and 0 <= j < C:
                    depth[i, j] = max(depth[i, j], d)
                    if main:
                        utapao[i, j] = True
    return depth, utapao


def rain_field(b, factor):
    """mm per hour on the grid for each hour from START, bilinear from the IMERG cells, times the bias factor."""
    r = json.loads((PKG / "v2-basin-rain.json").read_text())
    r0 = datetime.fromisoformat(r["start"])
    off = int((START - r0).total_seconds() // 3600)
    cells = r["cells"]
    xs = sorted({c["lon"] for c in cells})
    ys = sorted({c["lat"] for c in cells})
    cube = np.zeros((len(ys), len(xs), HOURS))
    for c in cells:
        mm = c["mm"][off:off + HOURS]
        cube[ys.index(c["lat"]), xs.index(c["lon"]), :len(mm)] = mm
    lon, lat = lonlat_grid(b)
    fx = np.clip(np.interp(lon, xs, np.arange(len(xs))), 0, len(xs) - 1)
    fy = np.clip(np.interp(lat, ys, np.arange(len(ys))), 0, len(ys) - 1)
    x0, y0 = np.floor(fx).astype(int), np.floor(fy).astype(int)
    x1, y1 = np.minimum(x0 + 1, len(xs) - 1), np.minimum(y0 + 1, len(ys) - 1)
    ax, ay = fx - x0, fy - y0
    out = np.zeros((HOURS, len(lat), len(lon)), dtype=np.float32)
    for h in range(HOURS):
        g = cube[:, :, h]
        top = g[y0][:, x0] * (1 - ax) + g[y0][:, x1] * ax
        bot = g[y1][:, x0] * (1 - ax) + g[y1][:, x1] * ax
        out[h] = (top * (1 - ay)[:, None] + bot * ay[:, None]) * factor
    return out


def gauge_series():
    g = json.loads((PKG / "gauge-x44.json").read_text())
    pts = sorted(((datetime.fromisoformat(r["at"]) - START).total_seconds() / 3600, r["levelM"], r.get("flowM3s") or 0)
                 for r in g["readings"])
    return pts


def interp(pts, h, k):
    xs = [p[0] for p in pts]
    return float(np.interp(h, xs, [p[k] for p in pts]))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--member", default="base")
    ap.add_argument("--rain", type=float, default=1.9)
    ap.add_argument("--n-urban", type=float, default=0.12)
    ap.add_argument("--inflow", type=float, default=0.5)
    ap.add_argument("--drain", type=float, default=5.0, help="city drain capacity, mm/h")
    ap.add_argument("--hours", type=int, default=HOURS)
    ap.add_argument("--out", default=None)
    ap.add_argument("--coarsen", type=int, default=2, help="1 = 75 m, 2 = 150 m")
    ap.add_argument("--urban-dem", type=float, default=0.0, help="lower built-up ground by this much (FABDEM keeps some building height in dense blocks)")
    ap.add_argument("--channel-width-exp", type=float, default=0.6, help="how much a narrow channel's friction is raised")
    args = ap.parse_args()
    t0 = time.time()

    b, z, lc = load(args.coarsen)
    R, C = z.shape
    dx = float(b["cellM"])
    nodata = np.isnan(z)
    z = np.where(nodata, LAKE_M - 0.5, z)
    lake = ((lc == 80) & (z < 2.5)) | nodata
    z = np.where(lake, np.maximum(z, LAKE_M - 1.0), z)
    burn, utapao = burn_channels(b, z)
    zc = z - burn
    # The U-Tapao and R.1 beds: near sea level at the gauge (its low flow stands at ~0.7 m), rising gently upstream.
    # A coarse cell's ground is the average of the banks, far above the real bed, so the bed is set, not burned.
    lon, lat = lonlat_grid(b)
    km_south = np.maximum(0.0, (GAUGE_LONLAT[1] - lat) * 110.574)[:, None] * np.ones((1, len(lon)))
    main_bed = BED0_M + BED_SLOPE * km_south
    main = burn >= 2.5
    zc = np.where(main, np.minimum(zc, main_bed), zc)
    n = np.vectorize(lambda c: LC.get(int(c), LC[0])[0])(lc).astype(np.float64)
    # a channel narrower than the cell: raise its friction so the cell carries what the real channel carries
    width = np.where(main, 45.0, np.where(burn >= 1.2, 20.0, 8.0))
    n[burn > 0] = (0.035 / np.clip(width / float(b["cellM"]), 0.05, 1.0) ** args.channel_width_exp)[burn > 0]
    zc = np.where((lc == 50) & ~(burn > 0), zc - args.urban_dem, zc)
    n[lc == 50] = args.n_urban
    cn2 = np.vectorize(lambda c: LC.get(int(c), LC[0])[1])(lc).astype(np.float64)
    cn = 23 * cn2 / (10 + 0.13 * cn2)                  # wet antecedent conditions (AMC III)
    S = 25400 / np.maximum(cn, 1) - 254                 # potential retention, mm
    built = lc == 50
    rain = rain_field(b, args.rain)
    gauge = gauge_series()
    w, s, e, nn = b["bbox"]
    gi, gj = int((nn - GAUGE_LONLAT[1]) / (nn - s) * R), int((GAUGE_LONLAT[0] - w) / (e - w) * C)
    # snap the gauge to the nearest U-Tapao cell
    ii, jj = np.nonzero(utapao)
    k = int(np.argmin((ii - gi) ** 2 + (jj - gj) ** 2))
    gi, gj = int(ii[k]), int(jj[k])
    # the inflow cell: the U-Tapao cell nearest the south edge
    k = int(np.argmax(ii))
    ini, inj = int(ii[k]), int(jj[k])

    zc = zc.astype(np.float32)
    n = n.astype(np.float32)
    S = S.astype(np.float32)
    h = np.where(lake, np.maximum(0.0, LAKE_M - zc), 0.0).astype(np.float32)
    qx = np.zeros((R, C - 1), np.float32)
    qy = np.zeros((R - 1, C), np.float32)
    cum_p = np.zeros((R, C), np.float32)
    cum_q = np.zeros((R, C), np.float32)
    # display window frames
    vi0, vi1 = int((nn - VIEW[3]) / (nn - s) * R), int((nn - VIEW[1]) / (nn - s) * R)
    vj0, vj1 = int((VIEW[0] - w) / (e - w) * C), int((VIEW[2] - w) / (e - w) * C)
    frames = np.zeros((args.hours + 1, vi1 - vi0, vj1 - vj0), dtype=np.uint8)
    stage = []
    budget = {"rain_m3": 0.0, "excess_m3": 0.0, "inflow_m3": 0.0, "drain_m3": 0.0, "boundary_m3": 0.0}
    area = dx * dx
    tsim = 0.0
    hour = 0
    n2 = n * n
    nx2 = np.maximum(n2[:, :-1], n2[:, 1:])
    ny2 = np.maximum(n2[:-1, :], n2[1:, :])
    zx = np.maximum(zc[:, :-1], zc[:, 1:])
    zy = np.maximum(zc[:-1, :], zc[1:, :])
    edge = np.zeros((R, C), dtype=bool)
    edge[0, :] = True
    fixed = lake | edge

    def snapshot(hh):
        frames[hh] = np.clip(np.round(h[vi0:vi1, vj0:vj1] / STEP_M), 0, 255).astype(np.uint8)
        stage.append([hh, round(float(zc[gi, gj] + h[gi, gj]), 2)])

    snapshot(0)
    while hour < args.hours:
        hmax = float(h[~fixed].max())
        dt = min(30.0, CFL * dx / math.sqrt(G * max(hmax, 0.05)))
        t_next = (hour + 1) * 3600.0
        dt = min(dt, t_next - tsim)
        eta = zc + h
        # faces in x
        hf = np.maximum(np.maximum(eta[:, :-1], eta[:, 1:]) - zx, 0.0)
        wet = hf > 1e-3
        slope = (eta[:, 1:] - eta[:, :-1]) / dx
        qx = np.where(wet, (qx - G * hf * dt * slope) / (1 + G * nx2 * dt * np.abs(qx) / np.maximum(hf, 1e-3) ** (7 / 3)), 0.0)
        cap = FROUDE * hf * np.sqrt(G * hf)  # no faster than critical flow (keeps steep slopes stable)
        qx = np.clip(qx, -cap, cap)
        hf = np.maximum(np.maximum(eta[:-1, :], eta[1:, :]) - zy, 0.0)
        wet = hf > 1e-3
        slope = (eta[1:, :] - eta[:-1, :]) / dx
        qy = np.where(wet, (qy - G * hf * dt * slope) / (1 + G * ny2 * dt * np.abs(qy) / np.maximum(hf, 1e-3) ** (7 / 3)), 0.0)
        cap = FROUDE * hf * np.sqrt(G * hf)
        qy = np.clip(qy, -cap, cap)
        # limit outgoing volume to what each cell holds
        out = np.zeros((R, C), np.float32)
        out[:, :-1] += np.maximum(qx, 0)
        out[:, 1:] += np.maximum(-qx, 0)
        out[:-1, :] += np.maximum(qy, 0)
        out[1:, :] += np.maximum(-qy, 0)
        need = out * dt / dx
        scale = np.where(need > h, h / np.maximum(need, 1e-12), 1.0)
        qx = np.where(qx > 0, qx * scale[:, :-1], qx * scale[:, 1:])
        qy = np.where(qy > 0, qy * scale[:-1, :], qy * scale[1:, :])
        dh = np.zeros((R, C), np.float32)
        dh[:, :-1] -= qx
        dh[:, 1:] += qx
        dh[:-1, :] -= qy
        dh[1:, :] += qy
        h += dh * dt / dx
        # rain excess (SCS-CN, cumulative)
        p = rain[hour] * dt / 3600.0  # mm in this step
        cum_p += p
        pe = np.where(cum_p > 0.2 * S, (cum_p - 0.2 * S) ** 2 / (cum_p + 0.8 * S), 0.0)
        excess = np.maximum(pe - cum_q, 0.0)
        cum_q = pe
        h += excess / 1000.0
        budget["rain_m3"] += float(p.sum()) / 1000 * area
        budget["excess_m3"] += float(excess.sum()) / 1000 * area
        # city drains back up as the canal tops its bank
        g_now = interp(gauge, tsim / 3600, 1)
        cap = args.drain * max(0.0, min(1.0, (7.4 - g_now) / 0.6)) / 1000 * dt / 3600
        if cap > 0:
            d = np.where(built, np.minimum(h, cap), 0.0)
            h -= d
            budget["drain_m3"] += float(d.sum()) * area
        # the Sadao wave entering at the south edge
        q_in = args.inflow * interp(gauge, tsim / 3600 + 12, 2)
        h[ini, inj] += q_in * dt / area
        budget["inflow_m3"] += q_in * dt
        # lake and north edge hold the lake level
        before = float(h[fixed].sum())
        h[fixed] = np.maximum(0.0, LAKE_M - zc[fixed])
        budget["boundary_m3"] += (before - float(h[fixed].sum())) * area
        tsim += dt
        if tsim >= t_next - 1e-6:
            hour += 1
            snapshot(hour)
            if hour % 24 == 0:
                vw = h[vi0:vi1, vj0:vj1]
                print(f"[{args.member}] {START + timedelta(hours=hour):%d %b %H:%M}: dt {dt:.1f}s, city wet>0.1m "
                      f"{(vw > 0.1).mean() * 100:.0f}%, max {vw.max():.1f} m, stage at X.44 {stage[-1][1]:.2f} m "
                      f"(real {interp(gauge, hour, 1):.2f}), {time.time() - t0:.0f}s", flush=True)

    name = args.out or f"v2-basin-sim-{args.member}"
    with gzip.open(PKG / ".." / ".cache" / f"{name}.bin.gz", "wb", compresslevel=6) as fh:
        fh.write(frames.tobytes())
    meta = {"package": "hy-2025-11", "member": args.member, "start": START.isoformat(), "hours": args.hours,
            "rows": int(vi1 - vi0), "cols": int(vj1 - vj0),
            "bbox": [float(w + vj0 * (e - w) / C), float(nn - vi1 * (nn - s) / R), float(w + vj1 * (e - w) / C), float(nn - vi0 * (nn - s) / R)],
            "cellM": dx, "stepM": STEP_M, "frameBytes": int((vi1 - vi0) * (vj1 - vj0)),
            "params": {"rain": args.rain, "nUrban": args.n_urban, "inflow": args.inflow, "drainMmH": args.drain,
                       "urbanDemM": args.urban_dem, "channelWidthExp": args.channel_width_exp},
            "zView": np.round(zc[vi0:vi1, vj0:vj1], 2).tolist(), "builtView": built[vi0:vi1, vj0:vj1].astype(int).tolist(),
            "gaugeCell": [gi, gj], "inflowCell": [ini, inj], "stageX44": stage, "budget": budget,
            "model": "local-inertial shallow water (Bates et al. 2010) on FABDEM 75 m; IMERG x bias, SCS-CN AMC III; "
                     "Manning n by WorldCover; channels burned from OSM; drains back up above the bank; Sadao inflow "
                     "reconstructed from X.44 flow; lake level 1.0 m",
            "seconds": round(time.time() - t0)}
    (PKG / ".." / ".cache" / f"{name}.json").write_text(json.dumps(meta))
    print("done", name, round(time.time() - t0), "s; budget", {k: f"{v / 1e6:.1f} Mm3" for k, v in budget.items()})


if __name__ == "__main__":
    main()
