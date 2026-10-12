"""Reviewed resource failure: hold transport jobs, keep their history and withdraw estimates.

Only unfinished transport allocations using the failed resource are affected. Medical work is separate.
The write wrapper owns the transaction; the usual group-owner and priority rules rebuild the open list.
"""

from __future__ import annotations

import copy
from datetime import datetime


def hold_transport(seed: dict, resource_id: str, reason: str, next_update: str, now: str) -> dict:
    resources = [t["resource"] for t in seed["teams"] if t["resource"]["resourceId"] == resource_id]
    if not resources:
        raise KeyError(resource_id)
    if not reason.strip():
        raise ValueError("Say why the resource is unavailable")
    try:
        update = datetime.fromisoformat(next_update.replace("Z", "+00:00"))
        current = datetime.fromisoformat(now.replace("Z", "+00:00"))
        if update.utcoffset() is None or update <= current:
            raise ValueError
    except (ValueError, TypeError):
        raise ValueError("Set a future next status update with a timezone") from None
    if all(r.get("status") == "unavailable" for r in resources):
        return {"resourceId": resource_id, "heldAllocationIds": [], "alreadyUnavailable": True}
    needs = {n["listingId"]: n for c in seed["cases"] for n in c["needs"]}
    affected = [a for a in seed.get("allocations", []) if a["resourceId"] == resource_id
                and a["state"] in ("taken", "on_the_way", "on_scene")
                and needs[a["listingId"]]["type"] == "evacuation_transport"]
    before = {"resources": copy.deepcopy(resources), "allocations": copy.deepcopy(affected)}
    for r in resources:
        r.update(status="unavailable", reason=reason.strip(), reviewedAt=now, reviewedBy="coordinator")
    for a in affected:
        a.update(state="held", owner="coordinator", heldAt=now, holdReason=reason.strip(),
                 nextStatusUpdate={"at": next_update, "by": "coordinator"})
        if a.get("window"):
            a["window"].update(state="withdrawn", withdrawnAt=now, withdrawnBy="coordinator")
        a["briefRevision"] = a.get("briefRevision", 1) + 1
        a["briefAcknowledged"] = False
    seed.setdefault("history", []).append({"event": "resource_unavailable", "resourceId": resource_id,
                                            "at": now, "by": "coordinator", "reason": reason.strip(),
                                            "before": before,
                                            "after": {"resources": copy.deepcopy(resources),
                                                      "allocations": copy.deepcopy(affected)}})
    return {"resourceId": resource_id, "heldAllocationIds": [a["allocationId"] for a in affected]}
