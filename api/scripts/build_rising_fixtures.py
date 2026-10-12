"""Write the water-rising view fixture (D42) from the rule: python api/scripts/build_rising_fixtures.py

contract/fixtures/risingWater.P-B.json holds `rising.rising_water` for P-B every 30 minutes of the demo day
(10:00–17:00 Bangkok): the X.44 gauge line, forecasts valid at that time, and the desk prompt with the waiting
families to re-confirm first (from teamMissions.T-S.json's open list, which holds every P-B evacuation listing).
X.44 is on the canal through the city centre, so only P-B gets the gauge. api/tests/test_rising.py fails if the
file and the rule drift.
"""

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from api.rules.rain import rain_status, series_from_file  # noqa: E402
from api.rules.rising import WaitingFamily, gauge_status, rising_water  # noqa: E402

FIXTURES = ROOT / "contract" / "fixtures"
START = datetime(2026, 10, 11, 3, 0, tzinfo=timezone.utc)  # 10:00 Bangkok
STEPS = 15  # to 17:00


def inputs():
    gauge = json.loads((ROOT / "data/hy-2025-11/gauge-x44.json").read_text())
    rain = series_from_file(json.loads((ROOT / "data/hy-2025-11/rain-imerg.json").read_text()), "P-B")
    pkg = json.loads((FIXTURES / "areas.hy-2025-11.json").read_text())
    ground = {s["id"]: s["depth"]["groundM"][1] for z in pkg["zones"] if z["areaId"] == "P-B" for s in z["segments"]}
    families = [WaitingFamily.from_listing(l) for l in json.loads((FIXTURES / "teamMissions.T-S.json").read_text())["open"]]
    return gauge, rain, ground, families


def snapshot(at, gauge, rain, ground, families):
    return rising_water("P-B", at, families, ground, gauge=gauge_status(gauge, at),
                        rain=rain_status("P-B", rain, at, [], ground))


def build():
    gauge, rain, ground, families = inputs()
    return {"dataMode": "replay", "areaId": "P-B",
            "label": "River gauge X.44 and rain replayed from 24 Nov 2025 on the demo clock (D42); families are synthetic",
            "station": {k: gauge["station"][k] for k in ("id", "name", "bankM", "warningM")},
            "snapshots": [snapshot(START + timedelta(minutes=30 * i), gauge, rain, ground, families) for i in range(STEPS)]}


if __name__ == "__main__":
    (FIXTURES / "risingWater.P-B.json").write_text(json.dumps(build(), ensure_ascii=False, indent=1) + "\n")
    print("  risingWater.P-B.json")
