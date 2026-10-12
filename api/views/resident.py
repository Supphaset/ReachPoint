"""The family's own status page (D6, 8A): `GET /api/status/{token}`. Only this request; no other family, no exact
points, no medical notes. Honest wording: a team's time is an estimate, never a promise; nothing promises a rescue
before a team has taken the family.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from api.views.store import Store
from api.views.team import allocations_for, group_owner

BANGKOK = timezone(timedelta(hours=7))


def _clock(iso: str) -> str:
    return datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(BANGKOK).strftime("%H:%M")


def _family_line(store: Store, need: dict, gid: str) -> dict:
    a = next((a for a in allocations_for(store, need["listingId"]) if gid in a["groupIds"]), None)
    owner = group_owner(store, need, gid)
    if a is None and not owner:
        return {"state": "waiting", "text": "On the list. No team has taken it yet. Call again if it becomes an emergency."}
    if a is None:
        return {"state": "taken", "text": f"Team {owner} is handling your request."}
    t = a["teamId"]
    if a["state"] == "closed":
        return {"state": a["outcome"], "text": {
            "done": f"Picked up by Team {t} at {_clock(a['closedAt'])}.",
            "already_left": f"Team {t} found the place empty at {_clock(a['closedAt'])}. If you still need help, call again.",
            "not_found": f"Team {t} couldn't find you at {_clock(a['closedAt'])}. Call again with a landmark near you.",
            "needs_more_help": "Back on the list: a team saw you need more help. Call again if it becomes an emergency.",
        }[a["outcome"]]}
    if a["state"] == "on_scene":
        return {"state": "on_scene", "text": f"Team {t} is at your place."}
    if a["state"] == "on_the_way":
        return {"state": "on_the_way", "text": f"Team {t} is on the way."}
    if a.get("window"):
        w = a["window"]
        return {"state": "window", "text": f"Team {t} expects to reach you about {_clock(w['start'])}–{_clock(w['end'])} "
                                           "(team estimate, not a promise)."}
    return {"state": "taken", "text": f"Team {t} has taken your request. They haven't set a time yet."}


def resident_status(store: Store, token: str, now: str) -> dict | None:
    ref = store.seed.get("statusTokens", {}).get(token)
    if ref is None:
        return None
    report = next((r for r in store.seed.get("reports", []) if r["reportId"] == ref["reportId"]), None)
    base = {"reportId": ref["reportId"], "generatedAt": now, "label": "Your request (ReachPoint demo, synthetic)"}
    if ref.get("caseId") is None:
        if report and report["status"] == "rejected":
            return {**base, "state": "closed", "lines": [{"state": "closed", "text": "A coordinator closed this request: " + report.get("rejectReason", "")
                                                          + ". Call again if you still need help."}]}
        return {**base, "state": "received", "lines": [{"state": "received", "text": "We received your request. A coordinator is reading it now."}]}
    case = next(c for c in store.cases if c["caseId"] == ref["caseId"])
    lines = []
    for n in case["needs"]:
        if n["type"] != "evacuation_transport":
            continue
        for i, g in enumerate(n["groups"]):
            lines.append({"family": g["label"], **_family_line(store, n, f"{n['listingId']}-G{i + 1}")})
    if not lines:
        lines.append({"state": "reviewed", "text": "Your request was reviewed and is on the list for supplies or medical help."})
    return {**base, "caseId": case["caseId"], "state": "reviewed", "lastConfirmedAt": case["lastConfirmedAt"], "lines": lines}
