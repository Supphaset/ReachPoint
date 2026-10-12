"""Build the area briefing fixtures (C2): `contract/fixtures/areaBriefing.<area>.json`.

    python data/scripts/build_briefing_fixtures.py hy-2025-11

The friend's rules engine will regenerate `views/areaBriefing/{areaId}` from Firestore with the same
shape; until then the app and the friend's contract tests read these files. Geography, estimates and
depth come from the C1 fixture (`areas.<package>.json`); the operational records below are synthetic and
match the demo scenario at 10:15 Bangkok (pack §7 step 3: C-01 approved, P-B reviewed demand still 24).

Variants of P-B, for the screen states in the design doc:
    areaBriefing.P-B.empty.json          no reports or cases yet: every zone "No reports yet · not checked"
    areaBriefing.P-B.stale.json          generated 2 h 40 min earlier (the app also shows its own offline state)
    areaBriefing.P-B.layer-missing.json  flood extent unavailable: nothing may be shaded as dry

Conventions (pack §3): unknown is `null` with a `…Reason`, never 0; every number a team sees is either a
reviewed count or a labelled estimate, and estimates never add to counts. Stdlib + shapely.
"""

import copy
import json
import sys
from pathlib import Path

from shapely.geometry import Point, shape

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_geography import span  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "contract" / "fixtures"

AT = "2026-10-11T03:15:00Z"  # 10:15 Bangkok, after the coordinator approved C-01
STALE_AT = "2026-10-11T00:35:00Z"  # 07:35 Bangkok

# Reviewed cases, as a team leader may see them: landmark-level location only (D25), no names or phones.
# P-B evacuation people add up to the scenario's reviewed demand of 24 (C-01's 3 included once).
CASES = [
    {"caseId": "C-01", "segmentId": "B-3-L3", "people": 3, "lastConfirmedAt": "2026-10-11T03:15:00Z",
     "assistance": [
         {"type": "evacuation_transport", "priority": "yellow", "review": "validated", "allocation": "open"},
         {"type": "medical", "priority": "red", "review": "validated", "allocation": "open",
          "note": "Needs qualified review"}]},
    {"caseId": "C-02", "segmentId": "B-3-L5", "people": 4, "lastConfirmedAt": "2026-10-11T02:40:00Z",
     "assistance": [{"type": "evacuation_transport", "priority": "yellow", "review": "validated", "allocation": "open"}]},
    {"caseId": "C-03", "segmentId": "B-3-L1", "people": 2, "lastConfirmedAt": "2026-10-11T01:05:00Z",
     "assistance": [{"type": "evacuation_transport", "priority": "green", "review": "validated", "allocation": "open"}]},
    {"caseId": "C-04", "segmentId": "B-2-L3", "people": 5, "lastConfirmedAt": "2026-10-11T02:10:00Z",
     "assistance": [{"type": "evacuation_transport", "priority": "yellow", "review": "validated", "allocation": "taken",
                     "teamId": "T-R"}]},
    {"caseId": "C-05", "segmentId": "B-1-L2", "people": 3, "lastConfirmedAt": "2026-10-11T00:50:00Z",
     "assistance": [{"type": "evacuation_transport", "priority": "green", "review": "validated", "allocation": "open"},
                    {"type": "supplies", "priority": "green", "review": "validated", "allocation": "open"}]},
    {"caseId": "C-06", "segmentId": "B-5-L1", "people": 4, "lastConfirmedAt": "2026-10-11T02:55:00Z",
     "assistance": [{"type": "evacuation_transport", "priority": "yellow", "review": "validated", "allocation": "open"}]},
    {"caseId": "C-08", "segmentId": "B-6-L2", "people": 3, "lastConfirmedAt": "2026-10-11T01:30:00Z",
     "assistance": [{"type": "evacuation_transport", "priority": "yellow", "review": "validated", "allocation": "open"}]},
]

# Reports still waiting for the coordinator (counted in badges, never in demand).
UNREVIEWED = [
    {"reportId": "CALL-01/PE-05", "segmentId": "B-3-L3", "kind": "neighbour_report",
     "text": "A neighbour stayed at B-3 · L3; identity unknown"},
]

# Segment marks by teams (D17b). Everything else is "not_checked".
MARKS = {
    "B-2-L1": {"state": "checked", "at": "2026-10-11T02:20:00Z", "teamId": "T-R", "householdsFound": 3, "pickupsNeeded": 0},
    "B-6-L1": {"state": "could_not_reach", "at": "2026-10-11T01:50:00Z", "teamId": "T-R", "reason": "access blocked"},
    "B-3-L3": {"state": "partly_checked", "at": "2026-10-11T03:05:00Z", "teamId": "T-S", "householdsFound": 2, "pickupsNeeded": 1},
}

# Area-level facts from the scenario (pack §7). Values a team can't know are null with a reason.
AREA_FACTS = {
    "P-B": [
        {"key": "reviewedDemand", "label": "People needing evacuation (reviewed)", "value": 24, "unit": "people",
         "basis": "reviewed cases"},
        {"key": "conditionalCapacity", "label": "Seats offered, not yet confirmed", "value": 12, "unit": "seats",
         "basis": "T-S boat S1 (conditional)"},
        {"key": "knownGap", "label": "Still without a confirmed seat", "value": 24, "unit": "people",
         "basis": "reviewed demand minus confirmed seats"},
        {"key": "medicalUnderReview", "label": "Medical needs under qualified review", "value": 1, "unit": "cases",
         "basis": "reviewed cases"},
    ],
    "P-A": [
        {"key": "suppliesNeeded", "label": "Food packs needed", "value": 80, "unit": "packs", "basis": "reviewed requests"},
        {"key": "suppliesDelivered", "label": "Delivered", "value": 20, "unit": "packs", "basis": "team reports"},
        {"key": "suppliesRemaining", "label": "Still needed", "value": 60, "unit": "packs", "basis": "needed minus delivered"},
        {"key": "suppliesUnassigned", "label": "Not yet in a plan", "value": 30, "unit": "packs", "basis": "remaining minus plan PL-A"},
    ],
    "P-C": [
        {"key": "reviewedDemand", "label": "Reviewed needs", "value": None, "valueReason": "no_recent_assessment",
         "unit": "people", "basis": "no assessment since the water rose"},
    ],
}

LAYERS = {
    "floodExtent": {"state": "available", "id": "s1-2025-11-24",
                    "label": "Flood extent on 24 Nov 2025 06:03 Bangkok (Sentinel-1) · urban areas may be under-detected"},
    "noSatelliteData": {"state": "available", "label": "No satellite data · never means dry"},
    "reportedFlooding": {"state": "available", "label": "Reported flooding (official and news reports)"},
}


def people(seg_ids, raw, rate):
    """Everyone living in these segments, from the summed raw counts (rounded once, like the zone range)."""
    if not seg_ids:
        return [0, 0]
    return span(sum(raw[s]["wp"] for s in seg_ids), sum(raw[s]["bld"] for s in seg_ids) * rate)


def depth_band(segments):
    bands = [s["depth"]["modelledM"] for s in segments if s["depth"]["modelledM"]]
    if not bands:
        return None
    return {"modelledM": [min(b[0] for b in bands), max(b[1] for b in bands)], "source": "model",
            "label": "Modelled from reported depths and ground height (D31), not measured"}


def zone_view(zone, area, cases, unreviewed, marks, reports, raw, rate):
    segs = []
    for s in zone["segments"]:
        mark = marks.get(s["id"], {"state": "not_checked"})
        segs.append({
            "segmentId": s["id"], "label": s["label"], "check": mark,
            "estimate": s["estimate"], "depth": s["depth"],
            "noSatelliteDataShare": s["noSatelliteDataShare"],
            "cases": sum(c["segmentId"] == s["id"] for c in cases),
        })
    zcases = [c for c in cases if c["segmentId"].rsplit("-", 1)[0] == zone["id"]]
    zun = [u for u in unreviewed if u["segmentId"].rsplit("-", 1)[0] == zone["id"]]
    evac = sum(c["people"] for c in zcases if any(a["type"] == "evacuation_transport" for a in c["assistance"]))
    urgent = sum(a["priority"] == "red" for c in zcases for a in c["assistance"])
    open_segs = [s for s in segs if s["check"]["state"] != "checked"]
    not_checked = sum(s["check"]["state"] == "not_checked" for s in segs)
    unchecked = people([s["segmentId"] for s in open_segs], raw, rate)

    unknown = []
    partly = sum(s["check"]["state"] == "partly_checked" for s in segs)
    if not_checked or partly:
        parts = [f"{not_checked} of {len(segs)} segments not checked"] if not_checked else []
        parts += [f"{partly} partly checked"] if partly else []
        unknown.append({"key": "peopleNotChecked", "text": "Who needs help: " + ", ".join(parts)})
    for u in zun:
        unknown.append({"key": "unreviewed", "text": u["text"], "ref": u["reportId"]})
    for s in segs:
        if s["check"]["state"] == "could_not_reach":
            unknown.append({"key": "couldNotReach", "ref": s["segmentId"],
                            "text": f"{s['label']}: couldn't reach ({s['check']['reason']})"})
    if area["id"] == "P-B":
        unknown.append({"key": "depthMeasured", "text": "Water depth: no team measurement yet"})

    return {
        "zoneId": zone["id"], "areaId": area["id"], "district": zone["district"],
        "badge": {"urgent": urgent, "unreviewed": len(zun)},
        "status": "no_reports" if not zcases and not zun else "has_reports",
        "facts": [
            {"key": "reviewedEvacuation", "label": "Reported needing evacuation (reviewed)", "value": evac, "unit": "people"},
            {"key": "cases", "label": "Reviewed cases", "value": len(zcases), "unit": "cases"},
            {"key": "segmentsNotChecked", "label": "Segments not checked", "value": not_checked, "of": len(segs),
             "unit": "segments"},
            {"key": "reportedFloodingPoints", "label": "Cited flood reports in this zone", "value": reports,
             "unit": "reports"},
        ],
        "unknown": unknown,
        "estimate": {**zone["estimate"], "notYetChecked": unchecked},
        "depth": depth_band(zone["segments"]),
        "cases": [{"caseId": c["caseId"], "segmentId": c["segmentId"], "people": c["people"],
                   "lastConfirmedAt": c["lastConfirmedAt"], "assistance": c["assistance"]} for c in zcases],
        "segments": segs,
        "briefing": {"state": "unavailable", "text": None, "reason": "briefing_text_not_built_yet"},
    }


def area_view(area, cat, cases, unreviewed, marks, reports_in, at):
    raw = json.loads((ROOT / "data" / cat["package"] / "exposure.json").read_text())["segments"]
    rate = cat["estimate"]["peoplePerBuilding"]
    zones = [z for z in cat["zones"] if z["areaId"] == area["id"]]
    zviews = [zone_view(z, area, cases, unreviewed, marks, reports_in.get(z["id"], 0), raw, rate) for z in zones]
    seg_ids = [s["segmentId"] for z in zviews for s in z["segments"]]
    open_ids = [s["segmentId"] for z in zviews for s in z["segments"] if s["check"]["state"] != "checked"]
    return {
        "areaId": area["id"], "label": area["label"], "need": area["need"], "description": area["description"],
        "dataMode": "synthetic", "package": cat["package"], "generatedAt": at,
        "inputVersions": {"geography": cat["version"], "cases": len(cases)},
        "dataLabel": "Synthetic demo records; geography and estimates from the C1 fixture",
        "badge": {"urgent": sum(z["badge"]["urgent"] for z in zviews),
                  "unreviewed": sum(z["badge"]["unreviewed"] for z in zviews)},
        "facts": copy.deepcopy(AREA_FACTS[area["id"]]),
        "estimate": {"label": cat["estimate"]["label"], "modelLabel": cat["estimate"]["modelLabel"],
                     "everyone": people(seg_ids, raw, rate), "notYetChecked": people(open_ids, raw, rate)},
        "layers": copy.deepcopy(LAYERS),
        "zones": zviews,
    }


def reported_counts(package, cat):
    pkg = ROOT / "data" / package
    zones = {f["properties"]["id"]: shape(f["geometry"]) for f in json.loads((pkg / "zones.geojson").read_text())["features"]}
    pts = [Point(f["geometry"]["coordinates"]) for f in json.loads((pkg / "reported-flooding.geojson").read_text())["features"]]
    return {zid: sum(g.contains(p) for p in pts) for zid, g in zones.items()}


def write(name, doc):
    (FIXTURES / name).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n")
    print(f"  {name}")


def main(package):
    cat = json.loads((FIXTURES / f"areas.{package}.json").read_text())
    seg_ids = {s["id"] for z in cat["zones"] for s in z["segments"]}
    for c in CASES + UNREVIEWED:
        assert c["segmentId"] in seg_ids, c
    assert set(MARKS) <= seg_ids
    reports_in = reported_counts(package, cat)

    print("Writing:")
    for area in cat["areas"]:
        write(f"areaBriefing.{area['id']}.json", area_view(area, cat, CASES, UNREVIEWED, MARKS, reports_in, AT))
    pb = next(a for a in cat["areas"] if a["id"] == "P-B")

    empty = area_view(pb, cat, [], [], {}, reports_in, AT)
    for f in empty["facts"]:
        if f["key"] in ("reviewedDemand", "knownGap", "medicalUnderReview"):
            f["value"] = 0
        if f["key"] == "conditionalCapacity":
            f["value"], f["valueReason"] = None, "no_team_available_yet"
    write("areaBriefing.P-B.empty.json", empty)

    stale = area_view(pb, cat, CASES, UNREVIEWED, MARKS, reports_in, STALE_AT)
    write("areaBriefing.P-B.stale.json", stale)

    missing = area_view(pb, cat, CASES, UNREVIEWED, MARKS, reports_in, AT)
    missing["layers"]["floodExtent"] = {"state": "unavailable", "id": None, "label": "Flood extent unavailable"}
    write("areaBriefing.P-B.layer-missing.json", missing)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "hy-2025-11")
