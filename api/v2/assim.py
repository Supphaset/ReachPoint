"""Combine reports with the flood model: local optimal interpolation of report-minus-model differences.

The model (api/v2/sim.py) is the first guess everywhere. Each report is an observation of the water depth at its
place and time, with an error that depends on how it was said and who said it. Their differences from the model
(innovations) are spread to nearby places and times with a covariance
    C(d, t) = SB^2 * exp(-d / L - |t| / T)
and the analysis is   depth_a(x) = depth_model(x) + C_xo (C_oo + R)^-1 (obs - model_at_obs),
with its uncertainty  var_a(x)   = SB^2 - C_xo (C_oo + R)^-1 C_ox.
Only past reports are used for "now". A report that the others contradict strongly is marked doubtful and gets a
much larger error (it still shows; it is never deleted). Dry reports count as "under 5 cm". Urgent requests are
never held back by any of this.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

L_M = 300.0       # how far one report's information spreads
T_H = 12.0        # how long it stays relevant (floodwater stayed for days; check-ins come every 12 h)
CHECK_H = 8.0     # the doubtful check compares reports within this many hours
SB = 0.75         # how wrong the model may be (m)
SOURCE_MULT = {"self": 1.0, "reply": 1.0, "neighbour": 1.5, "relative": 1.5, "post": 2.0}
MAX_NEAR = 25


@dataclass
class Ob:
    id: str
    x: float
    y: float
    t: float
    lo: float
    hi: float
    source: str
    prior: float          # model depth there and then
    doubtful: bool = False

    @property
    def mid(self) -> float:
        return (self.lo + self.hi) / 2

    @property
    def sigma(self) -> float:
        # wording: knee ~0.30, waist ~0.38, chest ~0.44 m, plus the stated range; then who said it
        s = max(0.15, 0.2 + 0.18 * self.mid, (self.hi - self.lo) / 2)
        return s * SOURCE_MULT.get(self.source, 2.0) * (4.0 if self.doubtful else 1.0)


def _cov(dx, dt):
    return SB * SB * np.exp(-dx / L_M - np.abs(dt) / T_H)


class Index:
    """Reports bucketed by place, so each point only looks at reports that can matter to it."""

    def __init__(self, obs: list[Ob]):
        self.obs = obs
        self.b: dict = {}
        for o in obs:
            self.b.setdefault((int(o.x // L_M), int(o.y // L_M)), []).append(o)

    def near(self, x: float, y: float) -> list[Ob]:
        cx, cy = int(x // L_M), int(y // L_M)
        out = []
        for i in range(cx - 3, cx + 4):
            for j in range(cy - 3, cy + 4):
                out += self.b.get((i, j), ())
        return out


def analyse(obs, x: float, y: float, t: float, prior: float) -> tuple[float, float, int]:
    """(analysis depth, standard deviation, reports used) at one point and time, from past reports only."""
    pool = obs.near(x, y) if isinstance(obs, Index) else obs
    near = [o for o in pool if o.t <= t + 1e-6 and t - o.t <= 2 * T_H and (o.x - x) ** 2 + (o.y - y) ** 2 <= (3 * L_M) ** 2]
    if not near:
        return max(0.0, prior), SB, 0
    near.sort(key=lambda o: (o.x - x) ** 2 + (o.y - y) ** 2 + ((t - o.t) * 100) ** 2)
    near = near[:MAX_NEAR]
    ox = np.array([o.x for o in near])
    oy = np.array([o.y for o in near])
    ot = np.array([o.t for o in near])
    d_oo = np.hypot(ox[:, None] - ox[None, :], oy[:, None] - oy[None, :])
    coo = _cov(d_oo, ot[:, None] - ot[None, :]) + np.diag([o.sigma ** 2 for o in near])
    cxo = _cov(np.hypot(ox - x, oy - y), t - ot)
    innov = np.array([o.mid - o.prior for o in near])
    wgt = np.linalg.solve(coo, innov)
    inc = float(cxo @ wgt)
    var = SB * SB - float(cxo @ np.linalg.solve(coo, cxo))
    return max(0.0, prior + inc), math.sqrt(max(var, 0.0)), len(near)


def check(obs: list[Ob], z_limit: float = 2.0, known: dict | None = None) -> dict:
    """Leave-one-out: each report against what the model and the other reports around it say (up to a few hours
    either side). Marks doubtful in place and returns, per report, the expectation from the others."""
    idx = Index(obs)
    expect = {}
    for o in obs:
        if known and o.id in known:
            o.doubtful, expect[o.id] = known[o.id]
            continue
        others = [q for q in idx.near(o.x, o.y) if q is not o and abs(q.t - o.t) <= CHECK_H
                  and (q.x - o.x) ** 2 + (q.y - o.y) ** 2 <= (3 * L_M) ** 2]
        # the others, shifted to this report's time so reports either side count
        shifted = [Ob(q.id, q.x, q.y, o.t - abs(q.t - o.t), q.lo, q.hi, q.source, q.prior, q.doubtful) for q in others]
        a, sd, n = analyse(shifted, o.x, o.y, o.t, o.prior)
        expect[o.id] = (a, sd, n)
        resid = abs(o.mid - a)
        # the error expected at the depth the others point to (an exaggerated report must not widen its own margin)
        s_exp = max(0.15, 0.2 + 0.18 * a, (o.hi - o.lo) / 2) * SOURCE_MULT.get(o.source, 2.0)
        if n >= 2 and resid > 0.5 and resid > z_limit * math.sqrt(sd ** 2 + s_exp ** 2):
            o.doubtful = True
        # consensus: this report's difference from the model against the typical difference of its close neighbours
        close = [q for q in idx.near(o.x, o.y) if q is not o and (q.x - o.x) ** 2 + (q.y - o.y) ** 2 <= 600 ** 2 and abs(q.t - o.t) <= 6]
        if len(close) >= 3:
            gaps = sorted(q.mid - q.prior for q in close)
            med = gaps[len(gaps) // 2]
            mad = sorted(abs(g - med) for g in gaps)[len(gaps) // 2]
            if abs((o.mid - o.prior) - med) > (o.hi - o.lo) / 2 + mad + 0.45:
                o.doubtful = True
    return expect


def field(obs: list[Ob], grounds: list[float], bbox: list[float], rows: int, cols: int, t: float, to_m) -> dict:
    """Corrections on a coarse lattice for the map, from the reports of the last few hours:
    - inc: depth to add to the model where it has water (m);
    - wse: the water surface the reports point to, for places the model leaves dry (m above sea level);
    - support: how much the reports inform each point (0..1)."""
    use = [(o, g) for o, g in zip(obs, grounds) if t - 2 * T_H <= o.t <= t + 1e-6]
    if not use:
        return {"inc": [0] * (rows * cols), "wse": [0] * (rows * cols), "support": [0] * (rows * cols)}
    use = use[-300:]
    ox = np.array([o.x for o, _ in use])
    oy = np.array([o.y for o, _ in use])
    ot = np.array([o.t for o, _ in use])
    coo = _cov(np.hypot(ox[:, None] - ox[None, :], oy[:, None] - oy[None, :]), ot[:, None] - ot[None, :]) + \
        np.diag([o.sigma ** 2 for o, _ in use])
    w_inc = np.linalg.solve(coo, np.array([o.mid - o.prior for o, _ in use]))
    wse_obs = np.array([g + o.mid for o, g in use])
    w0, s0, e0, n0 = bbox
    lat = n0 - (np.arange(rows) + 0.5) * (n0 - s0) / rows
    lon = w0 + (np.arange(cols) + 0.5) * (e0 - w0) / cols
    LON, LAT = np.meshgrid(lon, lat)
    gx, gy = to_m(LON.ravel(), LAT.ravel())
    d = np.hypot(gx[:, None] - ox[None, :], gy[:, None] - oy[None, :])
    cgo = _cov(d, t - ot[None, :])
    inc = cgo @ w_inc
    wts = np.exp(-d / L_M - np.abs(t - ot)[None, :] / T_H)
    support = 1 - np.exp(-wts.sum(axis=1) * 2)
    wse = (wts @ wse_obs) / np.maximum(wts.sum(axis=1), 1e-9)
    return {"inc": np.round(inc / 0.05).astype(int).clip(-127, 127).tolist(),
            "wse": np.round(np.where(support > 0.2, wse, 0) * 10).astype(int).tolist(),
            "support": np.round(support * 100).astype(int).tolist()}
