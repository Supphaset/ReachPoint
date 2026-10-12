"""Write the desk's zone order fixture (C12) from the rule: python api/scripts/build_zone_order_fixture.py

contract/fixtures/zoneOrder.hy-2025-11.json is `api/views/desk.zone_order_view` on the demo records: every zone of
the three area briefings, the register counts and the open RED listings, at 10:16 Bangkok. The friend's desk
shows it (suggested checks: publish / dismiss). api/tests/test_zone_order.py fails if the file and the rule drift.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from api.views import store as views_store  # noqa: E402
from api.views.desk import zone_order_view  # noqa: E402

FIXTURES = ROOT / "contract" / "fixtures"
AS_OF = datetime(2026, 10, 11, 3, 16, tzinfo=timezone.utc)  # demo clock 10:16
BRIEFING_AT = "2026-10-11T03:15:00Z"


def build():
    return {"dataMode": "synthetic", "label": "Desk zone order and suggested checks at 10:16 (C12). Counts only; register details stay with the coordinator",
            **zone_order_view(views_store.load(), AS_OF, BRIEFING_AT)}


if __name__ == "__main__":
    (FIXTURES / "zoneOrder.hy-2025-11.json").write_text(json.dumps(build(), ensure_ascii=False, indent=1) + "\n")
    print("  zoneOrder.hy-2025-11.json")
