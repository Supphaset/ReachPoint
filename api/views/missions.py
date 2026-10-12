"""Zone missions and segments (D17b, D18, D20): what a team sees of published missions, and its segment jobs.

A team sees, per published zone mission, each segment with its state (open, taken by T-x, or its mark), the
register count (counts only, never details, D19), the people estimate (labelled) and the reviewed families located
there. A segment is taken by one team at a time. Marks follow FEMA-style building marks: Checked, Partly checked,
Couldn't reach; "Couldn't reach" never clears the zone.
"""

from __future__ import annotations

from api.rules.tiers import register_counts
from api.views.store import Store

MARKS = ("checked", "partly_checked", "could_not_reach")


def active_claim(store: Store, segment_id: str) -> dict | None:
    return next((c for c in store.seed.get("segmentClaims", []) if c["segmentId"] == segment_id and c["state"] == "taken"), None)


def _families(store: Store, segment_id: str) -> list[dict]:
    return [{"caseId": c["caseId"], "people": c["people"],
             "listingIds": [n["listingId"] for n in c["needs"] if n["review"] == "validated"]}
            for c in store.cases if c["segmentId"] == segment_id]


def segment_row(store: Store, zone: dict, seg: dict, reg: dict) -> dict:
    claim = active_claim(store, seg["id"])
    mark = store.seed["segmentMarks"].get(seg["id"])
    state = "taken" if claim else (mark["state"] if mark else "open")
    return {"segmentId": seg["id"], "label": seg["label"], "state": state,
            "takenBy": claim["teamId"] if claim else None, "claimId": claim["claimId"] if claim else None,
            "mark": mark, "registerCount": reg.get(seg["id"], 0),
            "estimate": {"everyone": seg["estimate"]["everyone"], "label": "people living here (estimate)"},
            "families": _families(store, seg["id"])}


def zone_missions(store: Store) -> list[dict]:
    reg = register_counts(store.register)
    zones = {z["id"]: z for z in store.catalogue["zones"]}
    out = []
    for m in store.seed.get("zoneMissions", []):
        z = zones[m["zoneId"]]
        out.append({**{k: m[k] for k in ("missionId", "zoneId", "publishedAt", "by", "reasons")},
                    "segments": [segment_row(store, z, s, reg) for s in z["segments"]]})
    return out


def segment_jobs(store: Store, team_id: str) -> list[dict]:
    """A team's segments: taken now, or marked by it today."""
    reg = register_counts(store.register)
    zones = {z["id"]: z for z in store.catalogue["zones"]}
    out = []
    for c in store.seed.get("segmentClaims", []):
        if c["teamId"] != team_id:
            continue
        z = zones[c["zoneId"]]
        seg = next(s for s in z["segments"] if s["id"] == c["segmentId"])
        out.append({"claimId": c["claimId"], "state": c["state"], "takenAt": c["takenAt"], "mark": c.get("mark"),
                    **{k: v for k, v in segment_row(store, z, seg, reg).items() if k not in ("state", "claimId", "takenBy")}})
    return out
