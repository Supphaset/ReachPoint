"""Area and zone briefing view (C2): `views/areaBriefing/{areaId}`.

Every number a team sees is either a reviewed count or a labelled estimate, and estimates never add to counts.
Unknown is null with a reason, never 0. Priorities come from `api/rules/tiers.py`, so the map, the lists and the
solver agree.
"""

from __future__ import annotations

import copy
import math
from datetime import datetime

from api.rules.tiers import TierInput, colour
from api.views.store import Store

BANDS = {"knee": ("Knee deep", 0.5), "waist": ("Waist deep", 1.0), "chest": ("Chest deep", 1.3),
         "over_head": ("Over head height", 2.0), "second_floor": ("Up to the 2nd floor", 3.0)}
STALE_HOURS = 6


def nice(x, up):
    """Round outwards to 2 significant figures (10 below 1,000), so a range never looks precise."""
    if x <= 0:
        return 0
    step = 10 if x < 1000 else 10 ** (len(str(int(x))) - 2)
    return int(math.ceil(x / step) * step) if up else int(math.floor(x / step) * step)


def span(*values):
    return [nice(min(values), False), nice(max(values), True)]


def _ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def need_colour(case: dict, need: dict) -> str | None:
    """Colour of one need from the shared tiers; None while not yet reviewed."""
    if need["review"] != "validated":
        return None
    return colour(TierInput.from_listing({
        "listingId": need["listingId"], "assistanceType": need["type"], "review": need["review"],
        "waitingSince": need["waitingSince"], "qualifiedAssessment": need.get("qualifiedAssessment"),
        "urgentFlag": need.get("urgentFlag"), "pickup": {}})).value


def briefing_cases(store: Store) -> list[dict]:
    """Cases as a team leader may see them: landmark-level, no names or phones, a priority per need."""
    out = []
    for c in store.cases:
        assistance = []
        for n in c["needs"]:
            a = {"type": n["type"], "priority": need_colour(c, n), "review": n["review"], "allocation": n["allocation"]["state"]}
            if n["allocation"].get("teamId"):
                a["teamId"] = n["allocation"]["teamId"]
            if n.get("deskNote"):
                a["note"] = n["deskNote"]
            assistance.append(a)
        out.append({"caseId": c["caseId"], "segmentId": c["segmentId"], "people": c["people"],
                    "lastConfirmedAt": c["lastConfirmedAt"], "assistance": assistance})
    return out


def caller_water(store: Store, seg_ids, at):
    """Reviewed water reports per segment: newest band, number of callers, stale after 6 h (D32)."""
    now, landmarks, out = _ts(at), store.landmarks, {}
    for w in store.seed["waterReports"]:
        if w["review"] != "validated" or w["segmentId"] not in seg_ids:
            continue
        cur = out.get(w["segmentId"])
        if cur is None or w["at"] > cur["latestAt"]:
            label, m = BANDS[w["band"]]
            out[w["segmentId"]] = {**(cur or {"callers": 0}), "segmentId": w["segmentId"],
                                   "landmarkLabel": landmarks[w["segmentId"]]["label"], "at": landmarks[w["segmentId"]]["at"],
                                   "band": w["band"], "bandLabel": label, "approxM": m, "latestAt": w["at"]}
        out[w["segmentId"]]["callers"] += 1
    for v in out.values():
        v["stale"] = (now - _ts(v["latestAt"])).total_seconds() / 3600 > STALE_HOURS
    return sorted(out.values(), key=lambda v: v["segmentId"])


def _people(seg_ids, raw, rate):
    if not seg_ids:
        return [0, 0]
    return span(sum(raw[s]["wp"] for s in seg_ids), sum(raw[s]["bld"] for s in seg_ids) * rate)


def _depth_band(segments):
    bands = [s["depth"]["modelledM"] for s in segments if s["depth"]["modelledM"]]
    if not bands:
        return None
    return {"modelledM": [min(b[0] for b in bands), max(b[1] for b in bands)], "source": "model",
            "label": "Modelled from reported depths and ground height (D31), not measured"}


def _zone(zone, area, cases, unreviewed, marks, reports, raw, rate, water):
    segs = []
    for s in zone["segments"]:
        est = dict(s["estimate"])
        if est["basis"] == "satellite" and any(w["segmentId"] == s["id"] for w in water):
            est["basis"] = "callers"  # D28: flooding reported by callers; estimate covers the whole segment
        segs.append({"segmentId": s["id"], "label": s["label"], "check": marks.get(s["id"], {"state": "not_checked"}),
                     "estimate": est, "depth": s["depth"], "noSatelliteDataShare": s["noSatelliteDataShare"],
                     "cases": sum(c["segmentId"] == s["id"] for c in cases)})
    zcases = [c for c in cases if c["segmentId"].rsplit("-", 1)[0] == zone["id"]]
    zun = [u for u in unreviewed if u["segmentId"].rsplit("-", 1)[0] == zone["id"]]
    evac = sum(c["people"] for c in zcases if any(a["type"] == "evacuation_transport" for a in c["assistance"]))
    urgent = sum(a["priority"] == "red" for c in zcases for a in c["assistance"])
    not_checked = sum(s["check"]["state"] == "not_checked" for s in segs)
    partly = sum(s["check"]["state"] == "partly_checked" for s in segs)
    unknown = []
    if not_checked or partly:
        parts = [f"{not_checked} of {len(segs)} segments not checked"] if not_checked else []
        parts += [f"{partly} partly checked"] if partly else []
        unknown.append({"key": "peopleNotChecked", "text": "Who needs help: " + ", ".join(parts)})
    for u in zun:
        unknown.append({"key": "unreviewed", "text": u["text"], "ref": u["reportId"]})
    for s in segs:
        if s["check"]["state"] == "could_not_reach":
            unknown.append({"key": "couldNotReach", "ref": s["segmentId"], "text": f"{s['label']}: couldn't reach ({s['check']['reason']})"})
    if area["id"] == "P-B":
        unknown.append({"key": "depthMeasured", "text": "Water depth: no team measurement yet"})
    return {
        "zoneId": zone["id"], "areaId": area["id"], "district": zone["district"],
        "badge": {"urgent": urgent, "unreviewed": len(zun)},
        "status": "no_reports" if not zcases and not zun else "has_reports",
        "facts": [
            {"key": "reviewedEvacuation", "label": "Reported needing evacuation (reviewed)", "value": evac, "unit": "people"},
            {"key": "cases", "label": "Reviewed cases", "value": len(zcases), "unit": "cases"},
            {"key": "segmentsNotChecked", "label": "Segments not checked", "value": not_checked, "of": len(segs), "unit": "segments"},
            {"key": "reportedFloodingPoints", "label": "Cited flood reports in this zone", "value": reports, "unit": "reports"},
        ],
        "unknown": unknown,
        "estimate": {**zone["estimate"], "notYetChecked": _people([s["segmentId"] for s in segs if s["check"]["state"] != "checked"], raw, rate)},
        "depth": _depth_band(zone["segments"]),
        "cases": [{"caseId": c["caseId"], "segmentId": c["segmentId"], "people": c["people"],
                   "lastConfirmedAt": c["lastConfirmedAt"], "assistance": c["assistance"]} for c in zcases],
        "segments": segs,
        "callerWater": water,
        "briefing": {"state": "unavailable", "text": None, "reason": "briefing_text_not_built_yet"},
    }


def area_facts(store: Store, area_id: str, cases: list[dict]) -> list[dict]:
    """Evacuation areas: computed from the cases and team seats. Others: stored scenario facts (see seed note)."""
    stored = store.seed.get("areaFacts", {})
    if area_id in stored:
        return copy.deepcopy(stored[area_id])
    zones = {z["id"] for z in store.catalogue["zones"] if z["areaId"] == area_id}
    mine = [c for c in cases if c["segmentId"].rsplit("-", 1)[0] in zones]
    demand = sum(c["people"] for c in mine if any(a["type"] == "evacuation_transport" and a["review"] == "validated" for a in c["assistance"]))
    serving = [t for t in store.seed["teams"] if "evacuation_transport" in t["capabilities"] and area_id in t.get("areas", [area_id])]
    seats = [t["resource"] for t in serving if t["resource"].get("status") != "unavailable"]
    offered = sum(r["seatUnits"] for r in seats if not r.get("confirmed"))
    confirmed = sum(r["seatUnits"] for r in seats if r.get("confirmed"))
    medical = sum(1 for c in mine if any(a["type"] == "medical" and a["review"] == "validated" for a in c["assistance"]))
    basis = " + ".join(f"{t['teamId']} {t['resource']['kind']} {t['resource']['resourceId']} (conditional)"
                       for t in serving if not t["resource"].get("confirmed") and t["resource"].get("status") != "unavailable") or "none"
    unavailable = [t["resource"]["resourceId"] for t in serving if t["resource"].get("status") == "unavailable"]
    if unavailable:
        basis += "; " + ", ".join(unavailable) + " unavailable (coordinator reviewed)"
    return [
        {"key": "reviewedDemand", "label": "People needing evacuation (reviewed)", "value": demand, "unit": "people", "basis": "reviewed cases"},
        {"key": "conditionalCapacity", "label": "Seats offered, not yet confirmed", "value": offered, "unit": "seats", "basis": basis},
        {"key": "knownGap", "label": "Still without a confirmed seat", "value": max(0, demand - confirmed), "unit": "people",
         "basis": "reviewed demand minus confirmed seats"},
        {"key": "medicalUnderReview", "label": "Medical needs under qualified review", "value": medical, "unit": "cases", "basis": "reviewed cases"},
    ]


def area_briefing(store: Store, area_id: str, at: str) -> dict:
    cat = store.catalogue
    area = next(a for a in cat["areas"] if a["id"] == area_id)
    raw, rate = store.exposure["segments"], cat["estimate"]["peoplePerBuilding"]
    cases, unreviewed, marks = briefing_cases(store), store.seed["unreviewed"], store.seed["segmentMarks"]
    reports = store.seed["reportedFloodingByZone"]
    zones = [z for z in cat["zones"] if z["areaId"] == area_id]
    water_all = caller_water(store, {s["id"] for z in zones for s in z["segments"]}, at) if cases else []
    zviews = [_zone(z, area, cases, unreviewed, marks, reports.get(z["id"], 0), raw, rate,
                    [w for w in water_all if w["segmentId"].rsplit("-", 1)[0] == z["id"]]) for z in zones]
    seg_ids = [s["segmentId"] for z in zviews for s in z["segments"]]
    open_ids = [s["segmentId"] for z in zviews for s in z["segments"] if s["check"]["state"] != "checked"]
    return {
        "areaId": area_id, "label": area["label"], "need": area["need"], "description": area["description"],
        "dataMode": store.seed["dataMode"], "package": cat["package"], "generatedAt": at,
        "inputVersions": {"geography": cat["version"], "cases": len(cases)},
        "dataLabel": "Synthetic demo records; geography and estimates from the C1 fixture",
        "badge": {"urgent": sum(z["badge"]["urgent"] for z in zviews), "unreviewed": sum(z["badge"]["unreviewed"] for z in zviews)},
        "facts": area_facts(store, area_id, cases),
        "estimate": {"label": cat["estimate"]["label"], "modelLabel": cat["estimate"]["modelLabel"],
                     "everyone": _people(seg_ids, raw, rate), "notYetChecked": _people(open_ids, raw, rate)},
        "layers": copy.deepcopy(store.seed["layers"]),
        "callerWater": water_all,
        "callerWaterLabel": "Water reported by callers (reviewed requests only), at the landmark of their segment; older than 6 h shown as stale",
        "zones": zviews,
    }
