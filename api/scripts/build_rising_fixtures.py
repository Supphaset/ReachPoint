"""Write the water-rising view fixture (D42) from the rule: python api/scripts/build_rising_fixtures.py

contract/fixtures/risingWater.P-B.json holds `rising.rising_water` for P-B every 30 minutes of the demo day
(10:00–17:00 Bangkok): the X.44 gauge line, forecasts valid at that time, and the desk prompt with the waiting
families to re-confirm first (every reviewed evacuation listing, from `api/views/desk.waiting_families`).
X.44 is on the canal through the city centre, so only P-B gets the gauge. api/tests/test_rising.py fails if the
file and the rule drift.
"""

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from api.views import store as views_store  # noqa: E402
from api.views.desk import _gauge, rising_water_view  # noqa: E402

FIXTURES = ROOT / "contract" / "fixtures"
START = datetime(2026, 10, 11, 3, 0, tzinfo=timezone.utc)  # 10:00 Bangkok
STEPS = 15  # to 17:00
TEAM_AT, BRIEFING_AT = "2026-10-11T03:16:00Z", "2026-10-11T03:15:00Z"


def build():
    st, gauge = views_store.load(), _gauge()
    return {"dataMode": "replay", "areaId": "P-B",
            "label": "River gauge X.44 and rain replayed from 24 Nov 2025 on the demo clock (D42); families are synthetic",
            "station": {k: gauge["station"][k] for k in ("id", "name", "bankM", "warningM")},
            "snapshots": [rising_water_view(st, "P-B", START + timedelta(minutes=30 * i), TEAM_AT, BRIEFING_AT) for i in range(STEPS)]}


if __name__ == "__main__":
    (FIXTURES / "risingWater.P-B.json").write_text(json.dumps(build(), ensure_ascii=False, indent=1) + "\n")
    print("  risingWater.P-B.json")
