"""Build the area briefing fixtures (C2): `contract/fixtures/areaBriefing.<area>.json`.

    python data/scripts/build_briefing_fixtures.py hy-2025-11

The view is built by `api/views/briefing.py` from the demo records in `contract/seed/demo.<package>.json`;
the friend's API builds `views/areaBriefing/{areaId}` with the same function from Firestore, so both match.
Variants of P-B, for the screen states in the design doc:
    areaBriefing.P-B.empty.json          no reports or cases yet: every zone "No reports yet · not checked"
    areaBriefing.P-B.stale.json          generated 2 h 40 min earlier (the app also shows its own offline state)
    areaBriefing.P-B.layer-missing.json  flood extent unavailable: nothing may be shaded as dry
"""

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from api.views import store as views_store  # noqa: E402
from api.views.briefing import area_briefing  # noqa: E402

FIXTURES = ROOT / "contract" / "fixtures"
AT = "2026-10-11T03:15:00Z"  # 10:15 Bangkok, after the coordinator approved C-01
STALE_AT = "2026-10-11T00:35:00Z"  # 07:35 Bangkok


def write(name, doc):
    (FIXTURES / name).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n")
    print(f"  {name}")


def main(package):
    st = views_store.load(package)
    print("Writing:")
    for area in st.catalogue["areas"]:
        write(f"areaBriefing.{area['id']}.json", area_briefing(st, area["id"], AT))

    bare = copy.deepcopy(st.seed)
    bare.update(cases=[], unreviewed=[], segmentMarks={})
    empty = area_briefing(views_store.Store(bare, st.catalogue, st.exposure, st.register), "P-B", AT)
    for f in empty["facts"]:
        if f["key"] in ("reviewedDemand", "knownGap", "medicalUnderReview"):
            f["value"] = 0
        if f["key"] == "conditionalCapacity":
            f["value"], f["valueReason"] = None, "no_team_available_yet"
    write("areaBriefing.P-B.empty.json", empty)

    write("areaBriefing.P-B.stale.json", area_briefing(st, "P-B", STALE_AT))

    missing = area_briefing(st, "P-B", AT)
    missing["layers"]["floodExtent"] = {"state": "unavailable", "id": None, "label": "Flood extent unavailable"}
    write("areaBriefing.P-B.layer-missing.json", missing)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "hy-2025-11")
