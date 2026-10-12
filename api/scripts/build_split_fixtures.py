"""Write the split panel fixtures (C4 view, C7): python api/scripts/build_split_fixtures.py

    splitPanel.cp3.json    what the coordinator's split panel shows at 10:25: the suggestion from the real solver,
                           labels for each need (case, landmark, family make-up), and a few precomputed What-if
                           scenarios (until the API serves What-if live: POST compare_scenarios)
    askTeams.ok.json       "Ask these N teams" accepted: one direct "Can you take this?" per team
    askTeams.stale.json    the needs or resources changed since the suggestion: VERSION_CONFLICT with the new one

All synthetic. Shapes are a draft until contract v1.0.
"""

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from api.rules.allocation import compare_scenarios, solve_split  # noqa: E402

FIXTURES = ROOT / "contract" / "fixtures"
BOAT = {"resourceId": "S2", "teamId": "T-X", "kind": "boat", "capabilities": ["evacuation_transport"], "areas": ["P-B"],
        "capacity": {"evacuation_transport": 12}, "capacityBasis": "a second boat, 12 seat units (what-if)"}
SCENARIOS = [
    ("whatif-boat", "One more boat (12 seats)", {"extra": [BOAT]}),
    ("whatif-no-s1", "S1 unavailable", {"drop": ["S1"]}),
    ("whatif-boat-no-s1", "S1 unavailable, one more boat", {"extra": [BOAT], "drop": ["S1"]}),
    ("whatif-supplies", "Supplies count double (w_supply 2.0)", {"weights": {"w_supply": 2.0}}),
]


def write(name, doc):
    (FIXTURES / name).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n")
    print(f"  {name}")


def main():
    snap = json.loads((FIXTURES / "allocationInput.cp3.json").read_text())
    marks = {l["id"]: l["label"] for l in json.loads((FIXTURES / "areas.hy-2025-11.json").read_text())["landmarks"]}
    needs = {n["listingId"]: {"caseId": n["caseId"], "areaId": n["areaId"], "assistanceType": n["assistanceType"],
                              "label": marks.get(n["pickup"].get("landmarkId"), n["areaId"]), "units": n["units"],
                              "unit": n["unit"], "party": n.get("party"), "note": n.get("note", "")}
             for n in snap["needs"]}
    base = solve_split(snap)
    scenarios = []
    for sid, label, opts in SCENARIOS:
        c = compare_scenarios(snap, **opts)
        scenarios.append({"id": sid, "label": label, "options": json.loads(json.dumps(opts)),
                          "diff": c["diff"], "suggestion": c["whatIf"]})
    resources = {r["resourceId"]: {"teamId": r["teamId"], "kind": r["kind"], "basis": r.get("capacityBasis", "")}
                 for r in snap["resources"] + [BOAT]}
    write("splitPanel.cp3.json", {
        "dataMode": "synthetic", "generatedAt": snap["snapshotAt"],
        "label": "Split panel at 10:25 (synthetic). A suggestion for the coordinator only; it writes nothing.",
        "whatIfLabel": "Simulation · nothing sent",
        "weights": {**snap["weights"], "setBy": "coordinator:demo-1", "setAt": "2026-10-11T03:00:00Z"},
        "needs": needs, "resources": resources, "suggestion": base, "scenarios": scenarios,
    })

    asked = sorted({a["teamId"] for a in base["assignments"] if not a["accepted"]})
    write("askTeams.ok.json", {"dataMode": "synthetic", "request": {
        "suggestionId": base["suggestionId"], "inputVersions": base["inputVersions"], "teamIds": asked,
        "submissionId": "SUB-ASK-0001"},
        "response": {"ok": True, "askedAt": "2026-10-11T03:26:00Z", "asks": [
            {"askId": f"ASK-{t}", "teamId": t, "listingIds": sorted({a["listingId"] for a in base["assignments"]
                                                                    if a["teamId"] == t and not a["accepted"]})}
            for t in asked],
            "note": "Each team sees a one-time 'Can you take this?'. They still take work through the normal claim."}})

    changed = copy.deepcopy(snap)
    next(r for r in changed["resources"] if r["resourceId"] == "S1")["available"] = False
    changed["inputVersions"] = {**changed["inputVersions"], "teams": changed["inputVersions"]["teams"] + 1}
    write("askTeams.stale.json", {"dataMode": "synthetic", "request": {
        "suggestionId": base["suggestionId"], "inputVersions": base["inputVersions"], "teamIds": asked,
        "submissionId": "SUB-ASK-0002"},
        "response": {"ok": False, "code": "VERSION_CONFLICT", "message": "Needs or resources changed",
                     "detail": {"why": "T-S reported S1 unavailable at 10:30", "current": solve_split(changed)}}})


if __name__ == "__main__":
    main()
