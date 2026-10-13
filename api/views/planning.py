"""Live solver adapter: whole unassigned family groups, residual capacity; no write or identity inference."""
from __future__ import annotations

import hashlib
import json

from api.rules.allocation import solve_split
from api.rules.water import timestamp
from api.views.team import groups, listing_doc, seats_used


def panel(store, at: str, area_id: str | None = None) -> dict:
    fingerprint = json.dumps({k: store.seed.get(k) for k in ("cases", "teams", "allocations")}, sort_keys=True)
    version = int(hashlib.sha256(fingerprint.encode()).hexdigest()[:12], 16)
    needs, labels, links = [], {}, {}
    for c, n in store.needs("evacuation_transport"):
        if n["review"] != "validated" or area_id and c["areaId"] != area_id:
            continue
        for g in groups(n, store):
            if g["state"] != "open":
                continue
            nid = g["groupId"]
            doc = listing_doc(c, n)
            doc.update(listingId=nid, party=g["party"], units=g["people"])
            needs.append(doc)
            labels[nid] = {"caseId": c["caseId"], "areaId": c["areaId"], "assistanceType": n["type"],
                           "label": store.landmarks[c["segmentId"]]["label"] + " · " + g["label"],
                           "units": g["people"], "unit": "people", "party": g["party"], "note": "Whole group; proximity is not a route"}
            links[nid] = {"listingId": n["listingId"], "groupId": nid, "expectedRevision": n["needRevision"]}
    resources = [{"resourceId": t["resource"]["resourceId"], "teamId": t["teamId"], "kind": t["resource"]["kind"],
                  "areas": t["areas"], "capabilities": ["evacuation_transport"],
                  "capacity": {"evacuation_transport": max(0, t["resource"]["seatUnits"] - seats_used(store, t["teamId"]))},
                  "available": t["status"] == "available" and t["resource"].get("status") != "unavailable"}
                 for t in store.seed["teams"] if "evacuation_transport" in t["capabilities"]]
    snapshot = {"snapshotAt": timestamp(at).replace(second=0, microsecond=0).isoformat().replace("+00:00", "Z"), "inputVersions": {"records": version}, "needs": needs,
                "resources": resources, "accepted": [], "weights": {"w_evac": 1.0, "w_supply": 1.0},
                "seatUnits": {"adults": 1, "children": 0.5, "infants": 0, "stretcher": 3}}
    suggestion = solve_split(snapshot, allow_splits=False)
    return {"dataMode": "synthetic", "generatedAt": at, "label": "Live transport plan: unassigned whole families, remaining capacity. Medical and supplies are separate.",
            "whatIfLabel": "Simulation · nothing sent", "weights": {**snapshot["weights"], "setBy": "demo rules"},
            "needs": labels, "groupLinks": links, "areaId": area_id, "suggestion": suggestion, "scenarios": [],
            "resources": {r["resourceId"]: {"teamId": r["teamId"], "kind": r["kind"],
                          "basis": "Remaining demo seats after existing commitments"} for r in resources}}
