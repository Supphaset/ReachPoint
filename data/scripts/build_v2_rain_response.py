"""How much the water at each place rises per millimetre of extra rain, and how soon: the difference between the
published flood model and the same model with 60 mm more rain over the whole basin in 6 hours from 24 Nov 00:00
(build_v2_basin_sim.py --extra-mm 60, published with --prefix=v2-sim-rain60). Treated as a linear response for
the rain warning: rise(x) ~ response(x) * forecast mm, reached about lag(x) hours after the rain starts.

    python data/scripts/build_v2_rain_response.py

Writes data/hy-2025-11/v2-rain-response.json (30 m grid, mm of rise per 10 mm of rain, and the lag in hours).
"""

from __future__ import annotations

import gzip
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "data" / "hy-2025-11"
CACHE = ROOT / "data" / ".cache"
EXTRA_MM = 60.0
START_H = 66          # scenario hour of 24 Nov 00:00 (scenario starts 21 Nov 06:00)
LAGS = range(1, 19)


def frames(prefix: Path):
    m = json.loads(Path(str(prefix) + ".json").read_text())
    with gzip.open(str(prefix) + ".bin.gz", "rb") as fh:
        a = np.frombuffer(fh.read(), np.uint8).reshape(m["hours"] + 1, m["rows"], m["cols"]).astype(np.float32) * m["stepM"]
    return m, a


def main() -> None:
    m, base = frames(PKG / "v2-sim")
    _, rain = frames(CACHE / "v2-sim-rain60")
    d = np.stack([rain[START_H + L] - base[START_H + L] for L in LAGS])        # rise at each lag
    d = np.maximum(d, 0.0)
    peak = d.max(axis=0)
    lag = np.array(list(LAGS))[d.argmax(axis=0)]
    per10 = np.clip(np.round(peak / EXTRA_MM * 10 * 1000), 0, 255).astype(int)  # mm of rise per 10 mm of rain
    out = {"package": "hy-2025-11", "rows": m["rows"], "cols": m["cols"], "bbox": m["bbox"], "extraMm": EXTRA_MM,
           "startH": START_H, "units": "mm of rise per 10 mm of rain; lag in hours after the rain starts",
           "per10mm": per10.ravel().tolist(), "lagH": np.where(per10 > 0, lag, 0).ravel().astype(int).tolist(),
           "method": "difference of the published flood model and the same run with 60 mm extra basin rain in 6 h"}
    (PKG / "v2-rain-response.json").write_text(json.dumps(out, separators=(",", ":")))
    wet = per10 > 0
    print("cells responding", int(wet.sum()), "of", wet.size, "; median rise per 10 mm",
          float(np.median(per10[wet])) if wet.any() else 0, "mm; median lag", float(np.median(lag[wet])) if wet.any() else 0, "h")


if __name__ == "__main__":
    main()
