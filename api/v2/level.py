"""Many uncertain depth reports → the most likely water level in a zone, with a range, outliers and a trend.

Each observation is turned into a water-surface height (ground height from FABDEM + reported depth). Houses close
together share roughly one water surface even when their depths differ, so the zone's level is a weighted median
of those heights. Weights are confidence × freshness. A second pass drops observations far from the first estimate
and marks them doubtful; they are kept, never deleted. Depth at any building is then level − ground.
This is an estimate from reports and terrain, not a hydraulic model, and is labelled that way.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

HALF_LIFE_H = 3.0
OUTLIER_M = 0.5        # beyond the reported range plus the zone's spread, by this much, is doubtful
TREND_WINDOW_H = 6.0


@dataclass
class Obs:
    id: str
    at_h: float          # hours since the scenario start
    ground_m: float
    lo_m: float
    hi_m: float
    base_weight: float = 1.0

    @property
    def wse(self) -> float:
        return self.ground_m + (self.lo_m + self.hi_m) / 2

    @property
    def half_range(self) -> float:
        return (self.hi_m - self.lo_m) / 2


@dataclass
class Level:
    wse_m: float | None                 # most likely water-surface height (m above sea level)
    lo_m: float | None                  # 25th percentile
    hi_m: float | None                  # 75th percentile
    n: int = 0                          # observations used
    n_eff: float = 0.0                  # sum of weights
    doubtful: list[str] = field(default_factory=list)
    trend_cm_h: float | None = None
    certainty: float = 0.0              # 0..1

    def depth_at(self, ground_m: float) -> tuple[float, float, float] | None:
        """(most likely, low, high) depth at a building with this ground height."""
        if self.wse_m is None:
            return None
        f = lambda w: round(max(0.0, w - ground_m), 2)
        return f(self.wse_m), f(self.lo_m), f(self.hi_m)


def _weighted_quantile(values: list[float], weights: list[float], q: float) -> float:
    pairs = sorted(zip(values, weights))
    total = sum(w for _, w in pairs)
    acc = 0.0
    for v, w in pairs:
        acc += w
        if acc >= q * total:
            return v
    return pairs[-1][0]


def freshness(age_h: float) -> float:
    return 0.5 ** (max(0.0, age_h) / HALF_LIFE_H)


WINDOW_H = 12.0
CERTAINTY_HALF_LIFE_H = 12.0


def estimate(obs: list[Obs], now_h: float, exclude: set[str] | frozenset = frozenset()) -> Level:
    """The level at now_h from observations in the last WINDOW_H hours. `exclude` are already judged doubtful."""
    live = [o for o in obs if now_h - WINDOW_H <= o.at_h <= now_h and o.id not in exclude]
    if not live:
        return Level(None, None, None)
    w = [o.base_weight * freshness(now_h - o.at_h) for o in live]
    v = [o.wse for o in live]
    med = _weighted_quantile(v, w, 0.5)
    q1, q3 = _weighted_quantile(v, w, 0.25), _weighted_quantile(v, w, 0.75)
    spread = (q3 - q1) / 2
    doubtful = [o.id for o in live if len(live) >= 3 and abs(o.wse - med) > o.half_range + spread + OUTLIER_M]
    keep = [(o, wi) for o, wi in zip(live, w) if o.id not in doubtful]
    v2, w2 = [o.wse for o, _ in keep], [wi for _, wi in keep]
    med = _weighted_quantile(v2, w2, 0.5)
    q1, q3 = _weighted_quantile(v2, w2, 0.25), _weighted_quantile(v2, w2, 0.75)
    # keep the range at least as wide as a typical single report
    typical = sorted(o.half_range for o, _ in keep)[len(keep) // 2]
    lo, hi = min(q1, med - typical), max(q3, med + typical)
    n_eff = sum(w2)
    n_cert = sum(o.base_weight * 0.5 ** ((now_h - o.at_h) / CERTAINTY_HALF_LIFE_H) for o, _ in keep)
    certainty = (1 - math.exp(-n_cert / 4)) * (1 / (1 + max(0.0, (hi - lo) - 0.4)))
    return Level(round(med, 2), round(lo, 2), round(hi, 2), len(keep), round(n_eff, 2), doubtful,
                 trend(keep, now_h), round(certainty, 2))


def trend(keep: list[tuple[Obs, float]], now_h: float) -> float | None:
    """Weighted least-squares slope of water-surface height over the last few hours, in cm per hour."""
    pts = [(o.at_h, o.wse, wi) for o, wi in keep if now_h - o.at_h <= TREND_WINDOW_H]
    if len(pts) < 3:
        return None
    sw = sum(p[2] for p in pts)
    mt = sum(p[0] * p[2] for p in pts) / sw
    mv = sum(p[1] * p[2] for p in pts) / sw
    den = sum(p[2] * (p[0] - mt) ** 2 for p in pts)
    if den < 0.5:  # reports bunched within a short time: no trend
        return None
    slope = sum(p[2] * (p[0] - mt) * (p[1] - mv) for p in pts) / den
    return round(slope * 100, 1)
