"""Write the rain view fixture (D41) from the rule: python api/scripts/build_rain_fixtures.py

contract/fixtures/rainStatus.hy-2025-11.json holds `rain.rain_status` for each area every 30 minutes of the demo
day (10:00–17:00 Bangkok), from the replayed satellite rain and the zones' check state at 10:16. The area briefing
shows the newest snapshot at or before the demo clock; the desk shows the prompt. The friend's backend regenerates
the same view on a schedule or after each `markSegment`. api/tests/test_rain.py fails if file and rule drift.
"""

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from api.views import store as views_store  # noqa: E402
from api.views.desk import rain_view  # noqa: E402

FIXTURES = ROOT / "contract" / "fixtures"
START = datetime(2026, 10, 11, 3, 0, tzinfo=timezone.utc)  # 10:00 Bangkok
STEPS = 15  # to 17:00
BRIEFING_AT = "2026-10-11T03:15:00Z"


def build():
    st = views_store.load()
    out = {a: [rain_view(st, a, START + timedelta(minutes=30 * i), BRIEFING_AT) for i in range(STEPS)] for a in ("P-A", "P-B", "P-C")}
    return {"dataMode": "replay", "label": "Satellite rain replayed from 24 Nov 2025 on the demo clock (D41). Not water depth",
            "snapshots": out}


if __name__ == "__main__":
    (FIXTURES / "rainStatus.hy-2025-11.json").write_text(json.dumps(build(), ensure_ascii=False, indent=1) + "\n")
    print("  rainStatus.hy-2025-11.json")
