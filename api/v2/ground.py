"""Street-level ground for built-up areas.

FABDEM removes buildings from the Copernicus surface model, but in Hat Yai's densest blocks (the station, Kim Yong,
Niphat Uthit) it still keeps 2-5 m of rooftop and embankment height: the downtown shows up as an 11-16 m hill
between streets at 8 m. Downtown flooded 1-2 m on 23-24 Nov 2025 (and in 2000 and 2010), so it is not a hill.
In built-up cells the ground is taken as the low end (10th percentile) of the heights within ~360 m, the street
level around the block; elsewhere FABDEM is kept. This is the usual percentile filter for turning a surface
model into a ground model, applied only where buildings are.
"""

from __future__ import annotations

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

RADIUS_M = 360.0
PCT = 10


def street_level(z: np.ndarray, built: np.ndarray, cell_m: float, radius_m: float = RADIUS_M, pct: int = PCT) -> np.ndarray:
    r = max(1, int(round(radius_m / cell_m)))
    zp = np.pad(z, r, mode="edge")
    low = np.nanpercentile(sliding_window_view(zp, (2 * r + 1, 2 * r + 1)), pct, axis=(2, 3))
    return np.where(built & ~np.isnan(z), np.fmin(z, low), z)


def built_on(lc: np.ndarray, lc_bbox, bbox, rows: int, cols: int) -> np.ndarray:
    """WorldCover built-up (class 50) sampled onto another grid."""
    bw, bs, be, bn = lc_bbox
    w, s, e, n = bbox
    la = n - (np.arange(rows) + 0.5) * (n - s) / rows
    lo = w + (np.arange(cols) + 0.5) * (e - w) / cols
    bi = np.clip(((bn - la) / (bn - bs) * lc.shape[0]).astype(int), 0, lc.shape[0] - 1)
    bj = np.clip(((lo - bw) / (be - bw) * lc.shape[1]).astype(int), 0, lc.shape[1] - 1)
    return lc[bi][:, bj] == 50
