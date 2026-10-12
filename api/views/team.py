"""Team view (C5): `views/teamMissions/{teamId}`: the team, its seats, and the open listings it can take.

Order is `tiers.sort_key` from the team's landmark (colour → distance → waiting → ID). Landmark-level places only;
the exact point and medical notes come only in the team's own job, after taking it (D25, D38). Each listing says
why it's urgent from reviewed operational facts, never transcripts or medical narrative (D37, pack §4.1).
"""

from __future__ import annotations

from api.rules.tiers import TierInput, colour, distance_m, sort_key, tier
from api.views.briefing import caller_water
from api.views.store import Store

SEAT = {"adults": 1.0, "children": 0.5, "infants": 0.0, "stretcher": 3.0}
SEAT_LABEL = "Seats: adult 1, child under 12 half, baby on a lap 0, stretcher or wheelchair 3 (D33)"
BOAT_DEPTH_M = 1.2  # D32: "boat needed" at 1.2 m or more (or a fast current); otherwise wading may be possible
TITLE = {"red": "Why this is an emergency", "yellow": "Why it's urgent", "green": "Why it can wait"}
WITHHELD = "Medical details come with the job, for the team that takes it"
MEDICAL_CATEGORY = "Medical need: affects how to move them"
DESTINATIONS = {"D1": "D1 Shelter (high ground)", "H1": "H1 Hospital (synthetic)"}


def seats(p):
    return sum(p[k] * SEAT[k] for k in SEAT)


def nice_distance(m):
    return int(round(m / 50.0) * 50)


def party_text(p):
    names = {"adults": ("adult", "adults"), "children": ("child", "children"), "infants": ("baby", "babies"),
             "stretcher": ("stretcher case", "stretcher cases")}
    return ", ".join(f"{p[k]} {names[k][p[k] != 1]}" for k in names if p.get(k))


def listing_doc(case: dict, need: dict) -> dict:
    """The need in the listing shape `TierInput.from_listing` and the solver read."""
    return {"listingId": need["listingId"], "caseId": case["caseId"], "areaId": case["areaId"], "assistanceType": need["type"],
            "review": need["review"], "waitingSince": need["waitingSince"], "units": need["units"], "unit": need["unit"],
            "pickup": {"landmarkId": case["segmentId"], "at": None}, "qualifiedAssessment": need.get("qualifiedAssessment"),
            "urgentFlag": need.get("urgentFlag"), "party": case.get("party")}


def urgency(case: dict, need: dict, water: dict, colour_: str) -> dict:
    """What a team needs to know to judge and prepare. Each fact names its basis."""
    facts, kit = [], []
    flag = (need.get("urgentFlag") or {}).get("reason", "").strip()
    if (need.get("qualifiedAssessment") or {}).get("urgentMedical"):
        facts.append({"kind": "medical", "text": "A qualified review says someone here needs urgent medical help", "basis": "qualified review"})
    if flag:
        facts.append({"kind": "flag", "text": f"Coordinator flagged urgent: {flag}", "basis": "coordinator"})
    linked = [m for m in case["needs"] if m["listingId"] != need["listingId"] and m["type"] == "medical"
              and (m.get("qualifiedAssessment") or {}).get("urgentMedical")]
    if linked:
        facts.append({"kind": "medical", "text": f"{linked[0]['units']} person in this household needs urgent medical help; "
                      "the medical team is asked separately", "basis": "qualified review"})
    if need.get("medicalNotes") and not linked:
        facts.append({"kind": "medical_category", "text": MEDICAL_CATEGORY, "basis": "coordinator"})
    p = case["party"]
    facts.append({"kind": "people", "text": f"{need['units']} people: {party_text(p)}", "basis": "reviewed call"})
    if p["stretcher"]:
        facts.append({"kind": "mobility", "text": "Can't walk: must be carried", "basis": "reviewed call"})
        kit.append("Stretcher, and at least 2 people to carry")
    if p["children"] or p["infants"]:
        n = p["children"] + p["infants"]
        kit.append(f"Life jackets for {n} {'child' if n == 1 else 'children'}")
    w = water.get(case["segmentId"])
    if w:
        facts.append({"kind": "water", "text": f"{w['bandLabel']} (about {w['approxM']:g} m) at the landmark",
                      "basis": "callers", "at": w["latestAt"], "callers": w["callers"], "stale": w["stale"]})
        kit.insert(0, "Boat needed (water 1.2 m or more)" if w["approxM"] >= BOAT_DEPTH_M else "Wading may be possible; check on arrival")
    else:
        facts.append({"kind": "water", "text": "Water depth here: unknown (no reviewed report)", "basis": "none"})
    summary = next((f["text"] for k in ("flag", "medical", "mobility", "medical_category", "water") for f in facts if f["kind"] == k), "")
    return {"title": TITLE[colour_], "summary": summary, "facts": facts, "kit": kit,
            "withheld": WITHHELD if any(f["kind"] in ("medical", "medical_category") for f in facts) else None}


def destination(need: dict) -> dict:
    d = need.get("destination") or {"id": "D1", "reason": "Shelter"}
    return {"id": d["id"], "label": DESTINATIONS[d["id"]], "reason": d["reason"]}


def groups(need: dict) -> list[dict]:
    """Household groups, each taken whole. A taken listing's groups show who took them."""
    alloc = need["allocation"]
    state = "open" if alloc["state"] == "open" else "taken"
    out = []
    for i, g in enumerate(need["groups"]):
        row = {"groupId": f"{need['listingId']}-G{i + 1}", "label": g["label"], "people": sum(g["party"].values()),
               "party": g["party"], "seatUnits": seats(g["party"]), "state": state}
        if state == "taken" and alloc.get("teamId"):
            row["takenBy"] = alloc["teamId"]
        out.append(row)
    return out


def team_missions(store: Store, team_id: str, at: str, water_at: str | None = None) -> dict:
    """`water_at`: the time the caller-water view was generated (stale flags are computed against it)."""
    team = store.team(team_id)
    if team is None:
        raise KeyError(team_id)
    team_at = tuple(team["at"])
    landmarks = store.landmarks
    pb = {s["id"] for z in store.catalogue["zones"] for s in z["segments"]}
    water = {w["segmentId"]: w for w in caller_water(store, pb, water_at or at)}
    rows = []
    for case, need in store.needs():
        if need["type"] not in team["capabilities"] or need["review"] != "validated":
            continue
        assert sum(sum(g["party"].values()) for g in need["groups"]) == need["units"], need["listingId"]
        doc = listing_doc(case, need)
        doc["pickup"]["at"] = landmarks[case["segmentId"]]["at"]
        t = TierInput.from_listing(doc)
        c = colour(t).value
        flag = (need.get("urgentFlag") or {}).get("reason", "").strip()
        rows.append((sort_key(t, team_at), {
            "listingId": need["listingId"], "caseId": case["caseId"], "assistanceType": need["type"],
            "colour": c, "tier": tier(t).value, "needRevision": need["needRevision"],
            "zoneId": case["segmentId"].rsplit("-", 1)[0], "segmentId": case["segmentId"],
            "landmarkLabel": landmarks[case["segmentId"]]["label"],
            "distanceM": nice_distance(distance_m(team_at, tuple(doc["pickup"]["at"]))),
            "distanceBasis": "straight line from your landmark, not a route",
            "waitingSince": need["waitingSince"], "lastConfirmedAt": case["lastConfirmedAt"],
            "reasons": [f"Urgent: {flag}"] if flag else [],
            "urgency": urgency(case, need, water, c),
            "destination": destination(need),
            "people": need["units"],
            "groups": groups(need),
        }))
    rows.sort(key=lambda r: r[0])
    res = team["resource"]
    taken = sum(g["seatUnits"] for _, r in rows for g in r["groups"] if g.get("takenBy") == team_id)
    return {
        "teamId": team_id, "label": team["label"], "dataMode": store.seed["dataMode"], "generatedAt": at,
        "dataLabel": "Synthetic demo records at 10:16; order from api/rules/tiers.py (colour, distance, waiting)",
        "inputVersions": dict(store.seed["inputVersions"]),
        "team": {"status": team["status"], "statusSetAt": team["statusSetAt"], "reason": team["reason"], "backAbout": team["backAbout"],
                 "capabilities": team["capabilities"],
                 "location": {"landmarkId": team["landmarkId"], "label": landmarks[team["landmarkId"]]["label"], "at": team["at"]},
                 "resource": {"resourceId": res["resourceId"], "kind": res["kind"], "seatUnits": res["seatUnits"],
                              "seatUnitsLeft": res["seatUnits"] - taken, "basis": res["basis"]}},
        "seatUnits": {**SEAT, "label": SEAT_LABEL},
        "open": [r for _, r in rows],
        "jobs": [],
    }


def pickups(store: Store) -> dict:
    """Coordinator-side exact points (D25). A team gets one only in its own job, after taking it."""
    return {"label": "Coordinator-side exact pickup points (synthetic). A team sees one only in its own job, after taking it (D25).",
            "dataMode": store.seed["dataMode"],
            "pickups": {n["listingId"]: n["exactPickup"] for _, n in store.needs() if n.get("exactPickup")}}


def medical_notes(store: Store) -> dict:
    return {"label": "Coordinator-side medical notes (synthetic). A team sees one only in its own job after taking it, "
                     "and it is removed when the job closes (D38). Never on the shared list.",
            "dataMode": store.seed["dataMode"],
            "notes": {n["listingId"]: n["medicalNotes"] for _, n in store.needs() if n.get("medicalNotes")}}
