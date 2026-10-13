"""Privacy-preserving map projection: reported demand never becomes verified household counts."""
from __future__ import annotations

from api.rules.water import local_estimates
from api.views.team import ACTIVE, groups, seats_used


def flood_map(store, at: str, replay: dict | None = None) -> dict:
    landmarks = store.landmarks
    observations = list(store.seed.get("waterObservations", []))
    # Existing reviewed body bands remain qualitative; submitted time is not silently an observation time.
    for i, w in enumerate(store.seed.get("waterReports", [])):
        observations.append({"observationId": f"LEGACY-W-{i}", "reportId": w.get("caseId"), "segmentId": w["segmentId"],
                             "siteId": w["segmentId"], "evidenceRef": None, "observedAt": None, "receivedAt": w["at"],
                             "band": w["band"], "depthM": None, "reference": "unknown", "trend": "unknown",
                             "review": "verified" if w["review"] == "validated" else "ai_read", "source": "text"})
    by_seg = {}
    exceptions = []
    records = replay["records"] if replay else []
    if replay:
        at = replay["at"]
        observations = [r["observation"] for r in records if r["observation"]]
        exceptions = [{"reportId": r["reportId"], "segmentId": r["segmentId"], "urgent": r["urgent"],
                       "reasons": r["reasons"]} for r in records if r["state"] == "exception"]
    estimates = local_estimates(observations, at)
    for z in store.catalogue["zones"]:
        for s in z["segments"]:
            lm = landmarks[s["id"]]
            by_seg[s["id"]] = {"segmentId": s["id"], "zoneId": z["id"], "areaId": z["areaId"],
                               "label": lm["label"], "at": lm["at"], "noSatelliteDataShare": s["noSatelliteDataShare"],
                               "needs": {"reportedPeople": 0, "verifiedTransportUnassigned": 0, "urgentReports": 0, "urgentReviewedGroups": 0,
                                         "supplyReports": 0, "checkOnReports": 0}, "coverage": {"activeJobs": 0, "heldJobs": 0,
                                         "state": "not_checked"}, "estimates": [], "observations": []}
    for e in estimates:
        if e["segmentId"] in by_seg:
            by_seg[e["segmentId"]]["estimates"].append(e)
    for o in observations:
        if o["segmentId"] in by_seg:
            # Whitelist projection: original text, addresses and evidenceRefs never leave shared views.
            by_seg[o["segmentId"]]["observations"].append({k: o.get(k) for k in (
                "observationId", "reportId", "observedAt", "receivedAt", "reference", "source", "band", "depthM",
                "uncertaintyM", "trend", "review")})
    if replay:
        for r in records:
            if r["segmentId"] not in by_seg:
                continue
            n = by_seg[r["segmentId"]]["needs"]
            n["urgentReports"] += r["urgent"]
            if r["assistance"]:
                n["reportedPeople"] += r["assistance"]["people"]
                n["supplyReports"] += r["assistance"]["type"] == "supplies"
    else:
        for c, need in store.needs("evacuation_transport"):
            if c["segmentId"] not in by_seg or need["review"] != "validated":
                continue
            n = by_seg[c["segmentId"]]["needs"]
            open_groups = [g for g in groups(need, store) if g["state"] == "open"]
            n["verifiedTransportUnassigned"] += sum(g["people"] for g in open_groups)
            if (need.get("urgentFlag") or {}).get("reason") or (need.get("qualifiedAssessment") or {}).get("urgentMedical"):
                n["urgentReviewedGroups"] += len(open_groups)
        for a in store.seed.get("allocations", []):
            case = next((c for c in store.cases if any(n["listingId"] == a["listingId"] for n in c["needs"])), None)
            if case and case["segmentId"] in by_seg:
                v = by_seg[case["segmentId"]]["coverage"]
                v["activeJobs"] += a["state"] in ACTIVE
                v["heldJobs"] += a["state"] == "held"
        for sid, mark in store.seed.get("segmentMarks", {}).items():
            if sid in by_seg:
                by_seg[sid]["coverage"]["state"] = mark["state"]
    segments = list(by_seg.values())
    return {"dataMode": "synthetic", "source": "replay" if replay else "operations", "asOf": at,
            "replay": {k: v for k, v in replay.items() if k != "records"} if replay else None,
            "processingMode": "deterministic simulation · not live AI or live calls" if replay else "operational demo records",
            "counters": {"received": len(records), "organized": sum(r["state"] == "organized" for r in records),
                         "exceptions": len(exceptions), "urgentReports": sum(r["urgent"] for r in records),
                         "observations": len(observations), "numericEstimates": sum(e["status"] == "available" for e in estimates),
                         "conflicts": sum(e["status"] == "conflicting" for e in estimates),
                         "verifiedTransportUnassigned": sum(s["needs"]["verifiedTransportUnassigned"] for s in segments)},
            "segments": segments, "exceptions": exceptions[-100:], "exceptionsTotal": len(exceptions),
            "teams": [] if replay else [{"teamId": t["teamId"], "status": t["status"], "at": t["at"],
                       "areas": t["areas"], "capabilities": t["capabilities"], "resourceId": t["resource"]["resourceId"],
                       "resourceStatus": t["resource"].get("status", "available"), "statusSetAt": t["statusSetAt"],
                       "freeSeats": max(0, t["resource"]["seatUnits"] - seats_used(store, t["teamId"]))
                       if t["resource"].get("status") != "unavailable" else 0} for t in store.seed["teams"]],
            "note": "Reported people are summed reports, not distinct households or verified demand. No reports means unknown. No route safety inferred."}
