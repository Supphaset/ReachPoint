"""Desk review queue (T3): requests waiting for a person, with the AI's proposed facts and suggestions.

Coordinator only: it holds the caller's own words. Suggestions are suggestions: the landmark the text seems to
name, an urgent-flag prompt when the AI saw a danger sign, and a stretcher prompt when someone can't walk (D36).
Nothing here becomes a fact until the coordinator approves it.
"""

from __future__ import annotations

import re

from api.views.store import Store

LANDMARK_WORDS = {
    "School": ("school", "โรงเรียน"), "Temple": ("temple", "วัด"), "Market": ("market", "ตลาด"),
    "Mosque": ("mosque", "มัสยิด"), "Shrine": ("shrine", "ศาลเจ้า"),
    "Health centre": ("health centre", "health center", "clinic", "อนามัย", "สถานีอนามัย", "รพ.สต."),
    "Community building": ("community", "ชุมชน", "ศาลา"),
}


def suggest_segment(store: Store, text: str) -> dict | None:
    """The landmark a request seems to name: a zone ID in the text plus a landmark kind. Coordinator confirms."""
    low = text.lower()
    zones = re.findall(r"\b([ABC])\s*-?\s*(\d{1,2})\b", text.upper())
    kinds = [k for k, words in LANDMARK_WORDS.items() if any(w in low for w in words)]
    for prefix, num in zones:
        zid = f"{prefix}-{int(num)}"
        for lm in store.catalogue["landmarks"]:
            if lm["id"].startswith(zid + "-") and any(lm["label"].endswith(k) for k in kinds):
                return {"segmentId": lm["id"], "label": lm["label"], "why": f"the text names {zid} and a {kinds[0].lower()}"}
    if zones:
        zid = f"{zones[0][0]}-{int(zones[0][1])}"
        if any(z["id"] == zid for z in store.catalogue["zones"]):
            return {"segmentId": None, "zoneId": zid, "label": zid, "why": f"the text names {zid}; pick the landmark"}
    return None


def review_queue(store: Store) -> dict:
    rows = []
    for r in store.seed.get("reports", []):
        if r["status"] != "proposed":
            continue
        f = r["proposal"]["facts"]
        prompts = []
        if f["dangerSigns"]:
            prompts.append({"kind": "urgent_flag", "text": "Danger sign: " + "; ".join(d["text"] for d in f["dangerSigns"]) +
                            ". Flag urgent with a reason if a callback or the words confirm it."})
        if f["cantWalk"] or (f["people"] and f["people"]["stretcher"]):
            prompts.append({"kind": "stretcher", "text": "Someone can't walk: consider an urgent flag (\"bedridden, can't self-evacuate\", D36)."})
        if f["kind"] == "neighbour_report":
            prompts.append({"kind": "neighbour", "text": "A neighbour's report: counts are \"at least\", never added up (D29). Confirm with a callback."})
        if r.get("segmentId"):  # a field report from a team in its segment: that is the place
            lm = store.landmarks[r["segmentId"]]
            sugg = {"segmentId": r["segmentId"], "label": lm["label"], "why": f"field report from {r['teamId']} in this segment"}
            prompts.insert(0, {"kind": "field", "text": f"Field report from team {r['teamId']}: people found who hadn't called (D20)."})
        else:
            sugg = suggest_segment(store, r["text"])
        rows.append({"reportId": r["reportId"], "receivedAt": r["receivedAt"], "text": r["text"], "channel": r["channel"],
                     "proposal": r["proposal"], "suggestedSegment": sugg, "prompts": prompts,
                     **({"fromTeam": r["teamId"]} if r.get("teamId") else {})})
    return {"generatedAt": None, "label": "Requests waiting for review. The AI's reading is a proposal; only you make it a case.",
            "reports": rows,
            "landmarks": [{"segmentId": l["id"], "label": l["label"]} for l in store.catalogue["landmarks"] if l.get("zoneId")]}
