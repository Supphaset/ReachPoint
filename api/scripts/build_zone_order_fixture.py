"""Write the desk's zone order fixture (C12) from the rule: python api/scripts/build_zone_order_fixture.py

contract/fixtures/zoneOrder.hy-2025-11.json is what `tiers.zone_order` returns for every zone in the three area
briefings, the register counts and the RED listings of the demo snapshot, at 10:16 Bangkok. The friend's desk
shows it (suggested checks: publish / dismiss). api/tests/test_zone_order.py fails if the file and the rule drift.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from api.rules.tiers import PriorityColour, TierInput, ZoneInput, colour, register_counts, zone_order  # noqa: E402

FIXTURES = ROOT / "contract" / "fixtures"
AS_OF = datetime(2026, 10, 11, 3, 16, tzinfo=timezone.utc)  # demo clock 10:16 Bangkok


def inputs():
    reg = register_counts(json.loads((FIXTURES / "register.hy-2025-11.json").read_text()))
    zones = [ZoneInput.from_briefing(z, reg)
             for a in ("P-A", "P-B", "P-C")
             for z in json.loads((FIXTURES / f"areaBriefing.{a}.json").read_text())["zones"]]
    needs = json.loads((FIXTURES / "allocationInput.cp3.json").read_text())["needs"]
    red = [t for t in map(TierInput.from_listing, needs) if colour(t) is PriorityColour.RED]
    return zones, red


def build():
    zones, red = inputs()
    return {"dataMode": "synthetic", "label": "Desk zone order and suggested checks at 10:16 (C12). Counts only; register details stay with the coordinator",
            **zone_order(zones, red, AS_OF)}


if __name__ == "__main__":
    (FIXTURES / "zoneOrder.hy-2025-11.json").write_text(json.dumps(build(), ensure_ascii=False, indent=1) + "\n")
    print("  zoneOrder.hy-2025-11.json")
