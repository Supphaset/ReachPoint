"""Team view (C5): `views/teamMissions/{teamId}`: the team, its seats, and the open listings it can take.

Order is `tiers.sort_key` from the team's landmark (colour → distance → waiting → ID). Landmark-level places only;
the exact point and medical notes come only in the team's own job, after taking it (D25, D38). Each listing says
why it's urgent from reviewed operational facts, never transcripts or medical narrative (D37, pack §4.1).
"""

from __future__ import annotations

from api.rules.tiers import TierInput, colour, distance_m, sort_key, tier
from api.views.briefing import caller_water
from api.views.missions import segment_jobs, zone_missions
from api.views import thai
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
        facts.append({"kind": "medical", "text": "A qualified review says someone here needs urgent medical help",
                      "th": thai.MEDICAL_URGENT, "basis": "qualified review"})
    if flag:
        facts.append({"kind": "flag", "text": f"Coordinator flagged urgent: {flag}", "th": f"ผู้ประสานงานระบุว่าด่วน: {flag}",
                      "basis": "coordinator"})
    linked = [m for m in case["needs"] if m["listingId"] != need["listingId"] and m["type"] == "medical"
              and (m.get("qualifiedAssessment") or {}).get("urgentMedical")]
    if linked:
        facts.append({"kind": "medical", "text": f"{linked[0]['units']} person in this household needs urgent medical help; "
                      "the medical team is asked separately",
                      "th": f"มีสมาชิกในบ้าน {linked[0]['units']} คนต้องการความช่วยเหลือทางการแพทย์ด่วน ทีมแพทย์ได้รับแจ้งแยกต่างหาก",
                      "basis": "qualified review"})
    if need.get("medicalNotes") and not linked:
        facts.append({"kind": "medical_category", "text": MEDICAL_CATEGORY, "th": thai.MEDICAL_CATEGORY, "basis": "coordinator"})
    p = case["party"]
    facts.append({"kind": "people", "text": f"{need['units']} people: {party_text(p)}",
                  "th": f"{need['units']} คน: {thai.party(p)}", "basis": "reviewed call"})
    kit_th = []
    if p["stretcher"]:
        facts.append({"kind": "mobility", "text": "Can't walk: must be carried", "th": thai.CANT_WALK, "basis": "reviewed call"})
        kit.append("Stretcher, and at least 2 people to carry")
        kit_th.append(thai.STRETCHER_KIT)
    if p["children"] or p["infants"]:
        n = p["children"] + p["infants"]
        kit.append(f"Life jackets for {n} {'child' if n == 1 else 'children'}")
        kit_th.append(f"เสื้อชูชีพสำหรับเด็ก {n} คน")
    w = water.get(case["segmentId"])
    if w:
        facts.append({"kind": "water", "text": f"{w['bandLabel']} (about {w['approxM']:g} m) at the landmark",
                      "th": f"{thai.BANDS[w['band']]} (ประมาณ {w['approxM']:g} ม.) ที่จุดสังเกต",
                      "basis": "callers", "at": w["latestAt"], "callers": w["callers"], "stale": w["stale"]})
        boat = w["approxM"] >= BOAT_DEPTH_M
        kit.insert(0, "Boat needed (water 1.2 m or more)" if boat else "Wading may be possible; check on arrival")
        kit_th.insert(0, thai.BOAT_KIT if boat else thai.WADE_KIT)
    else:
        facts.append({"kind": "water", "text": "Water depth here: unknown (no reviewed report)", "th": thai.WATER_UNKNOWN, "basis": "none"})
    lead = next((f for k in ("flag", "medical", "mobility", "medical_category", "water") for f in facts if f["kind"] == k), None)
    withheld = any(f["kind"] in ("medical", "medical_category") for f in facts)
    return {"title": TITLE[colour_], "summary": lead["text"] if lead else "", "facts": facts, "kit": kit,
            "withheld": WITHHELD if withheld else None,
            "th": {"title": thai.TITLE[colour_], "summary": lead["th"] if lead else "", "kit": kit_th,
                   "withheld": thai.WITHHELD if withheld else None}}


def destination(need: dict) -> dict:
    d = need.get("destination") or {"id": "D1", "reason": "Shelter"}
    return {"id": d["id"], "label": DESTINATIONS[d["id"]], "reason": d["reason"],
            "th": {"label": thai.DESTINATIONS[d["id"]], "reason": thai.DESTINATION_REASONS.get(d["reason"])}}


ACTIVE = ("taken", "on_the_way", "on_scene")


def allocations_for(store: Store, listing_id: str) -> list[dict]:
    return [a for a in store.seed.get("allocations", []) if a["listingId"] == listing_id]


def group_owner(store: Store, need: dict, group_id: str) -> str | None:
    """The team holding this group: an allocation record covering it (open, or closed with the family moved), or
    the need's stored allocation for records that predate group-level claims (C-04 in the demo seed). A summary the
    server wrote from allocation records (`fromAllocations`) is never read back as an owner."""
    for a in allocations_for(store, need["listingId"]):
        if group_id in a["groupIds"] and (a["state"] in ACTIVE or a.get("outcome") in ("done", "already_left", "not_found")):
            return a["teamId"]
    alloc = need["allocation"]
    if alloc["state"] != "open" and not alloc.get("fromAllocations"):
        return alloc.get("teamId") or "another team"
    return None


def groups(need: dict, store: Store | None = None) -> list[dict]:
    """Household groups, each taken whole. A taken group shows who took it."""
    out = []
    for i, g in enumerate(need["groups"]):
        gid = f"{need['listingId']}-G{i + 1}"
        owner = group_owner(store, need, gid) if store else (need["allocation"].get("teamId") if need["allocation"]["state"] != "open" else None)
        row = {"groupId": gid, "label": g["label"], "labelTh": thai.family(g["label"]), "people": sum(g["party"].values()), "party": g["party"],
               "seatUnits": seats(g["party"]), "state": "taken" if owner else "open"}
        if owner:
            row["takenBy"] = owner
        out.append(row)
    return out


def seats_used(store: Store, team_id: str) -> float:
    """Seats held by a team's jobs: open jobs, and closed ones whose family was moved (the trip used the seats)."""
    return sum(a["seatUnits"] for a in store.seed.get("allocations", [])
               if a["teamId"] == team_id and (a["state"] in ACTIVE or a.get("outcome") == "done"))


def job(store: Store, a: dict, row: dict, need: dict) -> dict:
    """The team's own job: the only place the exact point and medical notes appear (D25, D38)."""
    # No exact point was given (e.g. a new call): fall back to the landmark itself, labelled as such, never 0, 0.
    case = next(c for c in store.cases if any(n["listingId"] == need["listingId"] for n in c["needs"]))
    exact = need.get("exactPickup") or {"at": store.landmarks[case["segmentId"]]["at"], "precision": "landmark",
                                        "source": "landmark only (no exact point given)"}
    out = {"allocationId": a["allocationId"], "listingId": a["listingId"], "caseId": row["caseId"], "colour": row["colour"],
           "landmarkLabel": row["landmarkLabel"], "urgency": row["urgency"], "destination": row["destination"],
           "medical": need.get("medicalNotes") if a["state"] in ACTIVE else None,
           "groups": [g for g in row["groups"] if g["groupId"] in a["groupIds"]],
           "seatUnits": a["seatUnits"], "state": "closed" if a["state"] == "closed" else a["state"],
           "window": None if (a.get("window") or {}).get("state") == "withdrawn" else a.get("window"), "acceptedAt": a["acceptedAt"],
           "pickup": {"landmarkLabel": row["landmarkLabel"], **exact}}
    if (a.get("window") or {}).get("state") == "withdrawn":
        out["withdrawnWindow"] = dict(a["window"])
    for k in ("outcome", "closedAt", "medicalRemovedAt", "owner", "holdReason", "nextStatusUpdate", "briefRevision"):
        if a.get(k):
            out[k] = a[k]
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
            "reasons": ([f"Urgent: {flag}"] if flag else []) + list(need.get("reasons", [])),
            "urgency": urgency(case, need, water, c),
            "destination": destination(need),
            "people": need["units"],
            "groups": groups(need, store),
        }))
    rows.sort(key=lambda r: r[0])
    res = team["resource"]
    taken = seats_used(store, team_id)
    by_listing = {r["listingId"]: r for _, r in rows}
    needs = {n["listingId"]: n for _, n in store.needs()}
    for lid, r in by_listing.items():
        if needs[lid].get("reconfirmRequestedAt"):
            r["reconfirmRequestedAt"] = needs[lid]["reconfirmRequestedAt"]
    jobs = [job(store, a, by_listing[a["listingId"]], needs[a["listingId"]])
            for a in store.seed.get("allocations", []) if a["teamId"] == team_id and a["listingId"] in by_listing]
    return {
        "teamId": team_id, "label": team["label"], "dataMode": store.seed["dataMode"], "generatedAt": at,
        "dataLabel": "Synthetic demo records at 10:16; order from api/rules/tiers.py (colour, distance, waiting)",
        "inputVersions": dict(store.seed["inputVersions"]),
        "team": {"status": team["status"], "statusSetAt": team["statusSetAt"], "reason": team["reason"], "backAbout": team["backAbout"],
                 "capabilities": team["capabilities"],
                 "location": {"landmarkId": team["landmarkId"], "label": landmarks[team["landmarkId"]]["label"], "at": team["at"]},
                 "resource": {"resourceId": res["resourceId"], "kind": res["kind"], "seatUnits": res["seatUnits"],
                              "seatUnitsLeft": 0 if res.get("status") == "unavailable" else res["seatUnits"] - taken,
                              **({"status": "unavailable"} if res.get("status") == "unavailable" else {}), "basis": res["basis"]}},
        "seatUnits": {**SEAT, "label": SEAT_LABEL},
        "open": [r for _, r in rows],
        "jobs": jobs,
        **({"asks": [a for a in store.seed["teamAsks"] if a["teamId"] == team_id]} if "teamAsks" in store.seed else {}),
        **({"zoneMissions": zone_missions(store), "segmentJobs": segment_jobs(store, team_id)}
           if store.seed.get("zoneMissions") or store.seed.get("segmentClaims") else {}),
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
