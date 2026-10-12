"""Isolated map replay adapter: deterministic parsing, not Gemini, live calls or authoritative filing.

Only visible intake words are parsed. No generation truth, private household identity, clinical decisions,
assignment or state changes in the operational MemoryStore. The friend's worker can replace this adapter.
"""
from __future__ import annotations

import re

from api.rules.water import timestamp

MEASUREMENT = re.compile(r"measured water (\d+(?:\.\d+)?) m above street ground")
PARTY = re.compile(r"(\d+) adults and (\d+) children need (transport|supplies)")


def process(report: dict, landmarks: dict) -> dict:
    text = report["text"]
    ids = re.findall(r"\b[A-Z]-\d+-L\d+\b", text)
    seg = ids[0] if len(set(ids)) == 1 and ids[0] in landmarks else None
    measurement = MEASUREMENT.search(text)
    time = re.search(r"At (\d{2}:\d{2}) outside at landmark", text)
    observed = None
    if time:
        h, m = map(int, time[1].split(":"))
        if h < 24 and m < 60:
            day = timestamp(report["receivedAt"]).astimezone(timestamp("2026-01-01T00:00:00+07:00").tzinfo)
            observed = day.replace(hour=h, minute=m, second=0).astimezone(timestamp(report["receivedAt"]).tzinfo).isoformat().replace("+00:00", "Z")
    danger = "Someone is trapped." in text
    party = PARTY.search(text)
    reasons = []
    if not seg:
        reasons.append("Location needs clarification")
    if "earlier report" in text:
        reasons.append("Possible update; household identity needs review")
    if not party and not measurement:
        reasons.append("Assistance details need clarification")
    if danger:
        reasons.append("Reported trapped person; operational attention, not clinical assessment")
    result = {"reportId": report["reportId"], "receivedAt": report["receivedAt"], "channel": report["channel"],
              "segmentId": seg, "state": "exception" if reasons else "organized", "reasons": reasons,
              "urgent": danger, "assistance": None, "observation": None, "processingMode": "deterministic_simulation"}
    if party and seg:
        result["assistance"] = {"type": "evacuation_transport" if party[3] == "transport" else "supplies",
                                "people": int(party[1]) + int(party[2]), "review": "ai_read",
                                "quote": party[0], "identity": "unknown"}
    if measurement and seg and observed:
        result["observation"] = {"observationId": f"W-{report['reportId']}", "reportId": report["reportId"],
                                  "segmentId": seg, "siteId": seg, "evidenceRef": (re.search(r"Observation reference (OBS-\d+)", text)[1]
                                                  if re.search(r"Observation reference (OBS-\d+)", text) else report["reportId"]),
                                  "observedAt": observed, "receivedAt": report["receivedAt"],
                                  "reference": "street_ground", "depthM": float(measurement[1]), "uncertaintyM": 0.15,
                                  "band": None, "trend": "rising", "review": "ai_read", "source": report["channel"],
                                  "quote": measurement[0]}
    elif seg and ("chest-level" in text or "ถึงอก" in text):
        result["observation"] = {"observationId": f"W-{report['reportId']}", "reportId": report["reportId"],
                                  "segmentId": seg, "siteId": seg, "evidenceRef": report["reportId"],
                                  "observedAt": None, "receivedAt": report["receivedAt"],
                                  "reference": "unknown", "depthM": None, "uncertaintyM": None,
                                  "band": "chest", "trend": "unknown", "review": "ai_read", "source": report["channel"],
                                  "quote": "chest-level" if "chest-level" in text else "ถึงอก"}
    return result
