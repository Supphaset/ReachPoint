"""Build the team view and claim-result fixtures (C5, C6) from the demo records.

    python api/scripts/build_team_fixtures.py

Writes, in contract/fixtures/:
    teamMissions.T-S.json   what team T-S (boat S1) sees at 10:16: its status, seats, and the open evacuation
                            listings in the shared order (tiers.sort_key from the team's landmark), each with its
                            household groups. Landmark-level locations only (D25).
    pickups.synthetic.json  exact pickup points, coordinator-side; a team gets one only in its own job, after
                            taking it (D25, C16).
    claim.<result>.json     one response per claimListing result, for both sides' contract tests (C6).

The views come from `api/views/team.py` on `contract/seed/demo.<package>.json`; the friend's API builds
`views/teamMissions/{teamId}` with the same function from Firestore. Field names are a draft until contract v1.0.
All records are synthetic.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from api.views import store as views_store  # noqa: E402
from api.views.team import medical_notes, pickups, team_missions  # noqa: E402

FIXTURES = ROOT / "contract" / "fixtures"
AT = "2026-10-11T03:16:00Z"  # 10:16 Bangkok, before T-S takes anything
BRIEFING_AT = "2026-10-11T03:15:00Z"  # the caller-water view the team sees was generated at 10:15


def main():
    st = views_store.load()
    view = team_missions(st, "T-S", AT, BRIEFING_AT)
    write("teamMissions.T-S.json", view)
    write("medicalNotes.synthetic.json", medical_notes(st))
    pk = pickups(st)
    write("pickups.synthetic.json", pk)
    notes = medical_notes(st)["notes"]

    c01 = next(r for r in view["open"] if r["listingId"] == "L-C01-EVAC")
    exact = pk["pickups"]["L-C01-EVAC"]
    results = {
        "accepted": {"ok": True, "allocation": {
            "allocationId": "AL-M01", "missionId": "M-01", "listingId": "L-C01-EVAC", "caseId": "C-01", "teamId": "T-S",
            "resourceId": "S1", "groupIds": [g["groupId"] for g in c01["groups"]], "seatUnits": 2.5, "state": "taken",
            "window": None, "acceptedAt": "2026-10-11T03:20:00Z", "needRevision": 2,
            "pickup": {"landmarkLabel": c01["landmarkLabel"], **exact}, "urgency": c01["urgency"],
            "destination": c01["destination"], "medical": notes["L-C01-EVAC"]}},
        "already-taken": {"ok": False, "code": "ALREADY_TAKEN", "message": "Already taken by T-R",
                          "detail": {"groupIds": ["L-C06-EVAC-G1"], "takenBy": "T-R"}},
        "not-enough-capacity": {"ok": False, "code": "NOT_ENOUGH_CAPACITY", "message": "Needs 5 seats, you have 4",
                                "detail": {"seatsNeeded": 5, "seatsLeft": 4}},
        "need-changed": {"ok": False, "code": "NEED_CHANGED", "message": "This case changed, please look again",
                         "detail": {"seenRevision": 1, "currentRevision": 2}},
        "allocation-closed": {"ok": False, "code": "ALLOCATION_CLOSED", "message": "This job is closed",
                              "detail": {"closedAt": "2026-10-11T05:40:00Z", "outcome": "done"}},
        "version-conflict": {"ok": False, "code": "VERSION_CONFLICT", "message": "Your screen was out of date; it has been refreshed",
                             "detail": {}},
    }
    for name, body in results.items():
        write(f"claim.{name}.json", {"dataMode": "synthetic", "request": {
            "listingId": "L-C01-EVAC", "groupIds": ["L-C01-EVAC-G1"], "expectedRevision": 2,
            "submissionId": f"SUB-CLAIM-{name.upper()}"}, "response": body})


def write(name, doc):
    (FIXTURES / name).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n")
    print(f"  {name}")


if __name__ == "__main__":
    main()
