"""Build the team view and claim-result fixtures (C5, C6) from the solver snapshot.

    python api/scripts/build_team_fixtures.py

Writes, in contract/fixtures/:
    teamMissions.T-S.json   what team T-S (boat S1) sees at 10:16: its status, seats, and the open evacuation
                            listings in the shared order (tiers.sort_key from the team's landmark), each with its
                            household groups. Landmark-level locations only (D25).
    pickups.synthetic.json  exact pickup points, coordinator-side; a team gets one only in its own job, after
                            taking it (D25, C16).
    claim.<result>.json     one response per claimListing result, for both sides' contract tests (C6).

The friend's rules engine will produce `views/teamMissions/{teamId}` with the same shape; field names are a
draft until contract v1.0. All records are synthetic.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from api.rules.tiers import TierInput, colour, distance_m, sort_key, tier  # noqa: E402

FIXTURES = ROOT / "contract" / "fixtures"
AT = "2026-10-11T03:16:00Z"  # 10:16 Bangkok, before T-S takes anything

# Household groups per listing. A household from one call is one group; C-06 is three households at one house,
# so CP2's "take Families 1+2, Family 3 still looking" can be shown.
GROUPS = {
    "L-C06-EVAC": [("Family 1", {"adults": 2, "children": 0, "infants": 0, "stretcher": 0}),
                   ("Family 2", {"adults": 1, "children": 0, "infants": 0, "stretcher": 0}),
                   ("Family 3", {"adults": 1, "children": 0, "infants": 0, "stretcher": 0})],
}
LAST_CONFIRMED = {"C-01": "03:15", "C-02": "02:40", "C-03": "01:05", "C-04": "02:10", "C-05": "00:50",
                  "C-06": "02:55", "C-08": "01:30"}
REVISION = {"L-C01-EVAC": 2}
LANDMARK_LABEL = {"B-3-L3": "B-3 · L3 Community building", "B-3-L5": "B-3 · L5 School", "B-3-L1": "B-3 · L1 Temple",
                  "B-2-L3": "B-2 · L3 Community building", "B-1-L2": "B-1 · L2 Temple", "B-5-L1": "B-5 · L1 Health centre",
                  "B-6-L2": "B-6 · L2 School", "B-3-L6": "B-3 · L6 Health centre"}
TEAM_AT = [100.47337, 7.00049]  # T-S waits at B-3 · L6 Health centre

# Exact points (synthetic, a few tens of metres from the landmark), as the coordinator holds them.
EXACT = {
    "L-C01-EVAC": ([100.47471, 7.00951], "building", "caller described the building; desk confirmed"),
    "L-C02-EVAC": ([100.46990, 7.00241], "building", "caller pin"),
    "L-C03-EVAC": ([100.47781, 7.01570], "landmark", "landmark only; caller couldn't give more"),
    "L-C04-EVAC": ([100.46825, 7.01902], "building", "Google Places match, desk confirmed"),
    "L-C05-EVAC": ([100.50171, 7.03660], "rooftop", "caller pin"),
    "L-C06-EVAC": ([100.44395, 7.00032], "building", "Pinpoint address match"),
    "L-C08-EVAC": ([100.47540, 7.02889], "building", "caller pin"),
}

SEAT = {"adults": 1.0, "children": 0.5, "infants": 0.0, "stretcher": 3.0}


def seats(p):
    return sum(p[k] * SEAT[k] for k in SEAT)


def nice_distance(m):
    return int(round(m / 50.0) * 50)


def main():
    snap = json.loads((FIXTURES / "allocationInput.cp3.json").read_text())
    evac = [n for n in snap["needs"] if n["assistanceType"] == "evacuation_transport"]
    rows = []
    for n in evac:
        t = TierInput.from_listing(n)
        groups = GROUPS.get(n["listingId"], [("Family 1", n["party"])])
        assert sum(sum(p.values()) for _, p in groups) == n["units"], n["listingId"]
        case = n["caseId"]
        rows.append((sort_key(t, tuple(TEAM_AT)), {
            "listingId": n["listingId"], "caseId": case, "assistanceType": n["assistanceType"],
            "colour": colour(t).value, "tier": tier(t).value, "needRevision": REVISION.get(n["listingId"], 1),
            "zoneId": n["pickup"]["landmarkId"].rsplit("-", 1)[0], "segmentId": n["pickup"]["landmarkId"],
            "landmarkLabel": LANDMARK_LABEL[n["pickup"]["landmarkId"]],
            "distanceM": nice_distance(distance_m(tuple(TEAM_AT), tuple(n["pickup"]["at"]))),
            "distanceBasis": "straight line from your landmark, not a route",
            "waitingSince": n["waitingSince"], "lastConfirmedAt": f"2026-10-11T{LAST_CONFIRMED[case]}:00Z",
            "reasons": [f"Urgent: {n['urgentFlag']['reason']}"] if (n.get("urgentFlag") or {}).get("reason", "").strip() else [],
            "people": n["units"],
            "groups": [{"groupId": f"{n['listingId']}-G{i + 1}", "label": label, "people": sum(p.values()), "party": p,
                        "seatUnits": seats(p), "state": "open"} for i, (label, p) in enumerate(groups)],
        }))
    rows.sort(key=lambda r: r[0])
    view = {
        "teamId": "T-S", "label": "Team T-S (boat)", "dataMode": "synthetic", "generatedAt": AT,
        "dataLabel": "Synthetic demo records at 10:16; order from api/rules/tiers.py (colour, distance, waiting)",
        "inputVersions": {"listings": 3, "team": 4},
        "team": {"status": "available", "statusSetAt": "2026-10-11T03:00:00Z", "reason": None, "backAbout": None,
                 "capabilities": ["evacuation_transport"],
                 "location": {"landmarkId": "B-3-L6", "label": LANDMARK_LABEL["B-3-L6"], "at": TEAM_AT},
                 "resource": {"resourceId": "S1", "kind": "boat", "seatUnits": 12, "seatUnitsLeft": 12,
                              "basis": "6 seats × 2 trips today"}},
        "seatUnits": {**SEAT, "label": "Seats: adult 1, child under 12 half, baby on a lap 0, stretcher or wheelchair 3 (D33)"},
        "open": [r for _, r in rows],
        "jobs": [],
    }
    write("teamMissions.T-S.json", view)

    pickups = {"label": "Coordinator-side exact pickup points (synthetic). A team sees one only in its own job, after taking it (D25).",
               "dataMode": "synthetic",
               "pickups": {lid: {"at": at, "precision": prec, "source": src} for lid, (at, prec, src) in EXACT.items()}}
    write("pickups.synthetic.json", pickups)

    c01 = next(r for _, r in rows if r["listingId"] == "L-C01-EVAC")
    exact = pickups["pickups"]["L-C01-EVAC"]
    results = {
        "accepted": {"ok": True, "allocation": {
            "allocationId": "AL-M01", "missionId": "M-01", "listingId": "L-C01-EVAC", "caseId": "C-01", "teamId": "T-S",
            "resourceId": "S1", "groupIds": [g["groupId"] for g in c01["groups"]], "seatUnits": 2.5, "state": "taken",
            "window": None, "acceptedAt": "2026-10-11T03:20:00Z", "needRevision": 2,
            "pickup": {"landmarkLabel": c01["landmarkLabel"], **exact}}},
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
