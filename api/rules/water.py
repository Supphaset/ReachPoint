"""Local observation estimates, not a flood surface or access/safety assessment.

Version 1: same reported site, street-ground reference, latest 30 minute window; at least two numeric
source references. Union uncertainty envelope (floor 0.15 m), never a precision gain from message count.
Distinct source references do not prove independent observers. Bands never become numeric measurements.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from statistics import median

VERSION = "local-envelope-v1"
WINDOW = timedelta(minutes=30)
STALE = timedelta(hours=6)
FLOOR_M = 0.15


def timestamp(value: str) -> datetime:
    t = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if t.tzinfo is None:
        raise ValueError("Time must include a timezone")
    return t


def estimate(observations: list[dict], at: str) -> dict:
    now = timestamp(at)
    base = {"method": VERSION, "rangeM": None, "centralM": None, "status": "insufficient_evidence",
            "latestAt": None, "evidenceIds": [], "sourceReferences": 0, "independence": "unknown",
            "bands": sorted({o["band"] for o in observations if o.get("band")}),
            "trends": sorted({o["trend"] for o in observations if o.get("trend", "unknown") != "unknown"}),
            "reasons": [], "observationCount": len(observations)}
    dated = [o for o in observations if o.get("observedAt") and timestamp(o["observedAt"]) <= now]
    if not dated:
        return {**base, "reasons": ["Observation time unknown or in the future; no current estimate"]}
    latest = max(timestamp(o["observedAt"]) for o in dated)
    recent = [o for o in dated if latest - timestamp(o["observedAt"]) <= WINDOW]
    base.update(latestAt=latest.isoformat().replace("+00:00", "Z"), evidenceIds=[o["observationId"] for o in recent],
                bands=sorted({o["band"] for o in recent if o.get("band")}),
                trends=sorted({o["trend"] for o in recent if o.get("trend", "unknown") != "unknown"}))
    if now - latest > STALE:
        return {**base, "status": "stale", "reasons": ["Newest dated observation is older than 6 hours"]}
    eligible = [o for o in recent if o.get("depthM") is not None and o.get("reference") == "street_ground"
                and o.get("evidenceRef")]
    # Same source can send updates; its newest numeric observation is the one retained for calculation.
    sources = {}
    for o in sorted(eligible, key=lambda x: (timestamp(x["observedAt"]), x["observationId"])):
        sources[o["evidenceRef"]] = o
    numeric = list(sources.values())
    base["sourceReferences"] = len(numeric)
    if len(numeric) < 2:
        return {**base, "status": "qualitative_only" if base["bands"] else "insufficient_evidence",
                "reasons": ["Need two numeric source references at the same reported site and street-ground reference",
                            "Body-level descriptions are not metre measurements"]}
    intervals = [(max(0, o["depthM"] - max(FLOOR_M, o["uncertaintyM"])),
                  o["depthM"] + max(FLOOR_M, o["uncertaintyM"])) for o in numeric]
    envelope = [round(min(a for a, _ in intervals), 2), round(max(b for _, b in intervals), 2)]
    conflict = max(a for a, _ in intervals) > min(b for _, b in intervals)
    return {**base, "status": "conflicting" if conflict else "available", "rangeM": envelope,
            "centralM": None if conflict else round(median(o["depthM"] for o in numeric), 2),
            "reasons": ["Numeric intervals disagree; inspect observations" if conflict else "Union of reported uncertainty intervals",
                        "Distinct source references do not establish independent observers",
                        "Local estimate only; no interpolation, route or access conclusion"]}


def local_estimates(observations: list[dict], at: str) -> list[dict]:
    sites = {}
    for o in observations:
        if o.get("review") in ("disputed", "superseded"):
            continue
        key = (o["segmentId"], o["siteId"])
        sites.setdefault(key, []).append(o)
    return [{"segmentId": seg, "siteId": site, **estimate(rows, at)}
            for (seg, site), rows in sorted(sites.items())]
