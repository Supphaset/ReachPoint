"""Write the split suggestion fixture (C4) from the solver: python api/scripts/build_suggestion_fixture.py

contract/fixtures/allocationSuggestion.cp3.json is what `solve_split(allocationInput.cp3.json)` returns, plus a
What-if with one extra boat. The friend's API stores it and the split panel shows it. Rebuild after model changes;
api/tests/test_allocation.py fails if the file and the solver drift apart.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from api.rules.allocation import compare_scenarios, solve_split  # noqa: E402

FIXTURES = ROOT / "contract" / "fixtures"
EXTRA_BOAT = {"resourceId": "S2", "teamId": "T-X", "kind": "boat", "capabilities": ["evacuation_transport"],
              "areas": ["P-B"], "capacity": {"evacuation_transport": 12}, "capacityBasis": "what-if: a second boat"}


def build():
    snap = json.loads((FIXTURES / "allocationInput.cp3.json").read_text())
    what_if = compare_scenarios(snap, extra=[EXTRA_BOAT])
    return {"dataMode": "synthetic", "label": "Split suggestion for the demo snapshot at 10:25 (C4); a suggestion only, it writes nothing",
            "suggestion": solve_split(snap),
            "whatIfExtraBoat": {"label": what_if["label"], "diff": what_if["diff"], "suggestion": what_if["whatIf"]}}


if __name__ == "__main__":
    (FIXTURES / "allocationSuggestion.cp3.json").write_text(json.dumps(build(), ensure_ascii=False, indent=1) + "\n")
    print("  allocationSuggestion.cp3.json")
