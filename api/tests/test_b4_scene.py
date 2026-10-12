"""The B-4 scene (D20, CP3): a suggested check → mission → T-R takes B-4 · L5 → field report → RED case → T-S takes
it → "Partly checked · 1 household found". Run: python -m pytest api/tests -q (no network: AI stand-in)."""

import os

import pytest

os.environ["REACHPOINT_AI"] = "off"
pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

import api.main as main  # noqa: E402


@pytest.fixture
def c():
    main.USE_AI = False
    main.reset()
    return TestClient(main.app)


def test_b4_scene(c):
    zo = c.get("/api/views/zoneOrder").json()
    check = zo["suggestedChecks"][0]
    assert check["zoneId"] == "B-4"
    assert c.post("/api/segments/B-4-L5/take", json={"teamId": "T-R"}).json()["code"] == "ALLOCATION_CLOSED"  # not published yet
    c.post("/api/zone-missions", json={"zoneId": "B-4", "reasons": check["reasons"]})
    assert "B-4" not in {s["zoneId"] for s in c.get("/api/views/zoneOrder").json()["suggestedChecks"]}

    tr = c.get("/api/views/teamMissions/T-R").json()
    seg = next(s for m in tr["zoneMissions"] if m["zoneId"] == "B-4" for s in m["segments"] if s["segmentId"] == "B-4-L5")
    assert seg["state"] == "open" and seg["registerCount"] == 1 and "detail" not in str(seg)
    claim = c.post("/api/segments/B-4-L5/take", json={"teamId": "T-R"}).json()["value"]["claimId"]
    assert c.post("/api/segments/B-4-L5/take", json={"teamId": "T-S"}).json() == {
        "code": "ALREADY_TAKEN", "message": "Already taken by T-R", "detail": {"takenBy": "T-R"}}
    assert c.get("/api/views/teamMissions/T-R").json()["segmentJobs"][0]["segmentId"] == "B-4-L5"

    rep = c.post("/api/intake/text", json={"text": "Elderly couple on the 2nd floor, one bedridden, they never called",
                                            "segmentId": "B-4-L5", "teamId": "T-R"}).json()["value"]
    row = next(r for r in c.get("/api/views/reviewQueue").json()["reports"] if r["reportId"] == rep["reportId"])
    assert row["channel"] == "field" and row["suggestedSegment"]["segmentId"] == "B-4-L5" and row["prompts"][0]["kind"] == "field"
    case = c.post(f"/api/reports/{rep['reportId']}/approve", json={
        "segmentId": "B-4-L5", "people": {"adults": 1, "children": 0, "infants": 0, "stretcher": 1},
        "needs": ["evacuation_transport"], "waterBand": "second_floor", "urgentReason": "Bedridden, found by T-R, can't self-evacuate"}).json()["value"]
    ts = c.get("/api/views/teamMissions/T-S").json()
    red = [r["caseId"] for r in ts["open"] if r["colour"] == "red"]
    assert case["caseId"] in red
    lid = case["listingIds"][0]
    assert c.post(f"/api/listings/{lid}/claim", json={"teamId": "T-S", "groupIds": [f"{lid}-G1"], "expectedRevision": 1}).status_code == 200

    assert c.post(f"/api/segment-claims/{claim}/mark", json={"state": "partly_checked", "householdsFound": 1, "pickupsNeeded": 2}).json()["code"] == "INVALID"
    c.post(f"/api/segment-claims/{claim}/mark", json={"state": "partly_checked", "householdsFound": 1, "pickupsNeeded": 1})
    b4 = next(z for z in c.get("/api/views/areaBriefing/P-B").json()["zones"] if z["zoneId"] == "B-4")
    s = next(s for s in b4["segments"] if s["segmentId"] == "B-4-L5")
    assert s["check"] == {"state": "partly_checked", "at": s["check"]["at"], "teamId": "T-R", "householdsFound": 1, "pickupsNeeded": 1}
    assert any(x["caseId"] == case["caseId"] for x in b4["cases"])
    assert c.post(f"/api/segment-claims/{claim}/mark", json={"state": "checked"}).json()["code"] == "ALLOCATION_CLOSED"


def test_couldnt_reach_needs_a_reason_and_never_clears(c):
    c.post("/api/zone-missions", json={"zoneId": "B-7", "reasons": []})
    claim = c.post("/api/segments/B-7-L4/take", json={"teamId": "T-R"}).json()["value"]["claimId"]
    assert c.post(f"/api/segment-claims/{claim}/mark", json={"state": "could_not_reach"}).json()["code"] == "INVALID"
    c.post(f"/api/segment-claims/{claim}/mark", json={"state": "could_not_reach", "reason": "access blocked"})
    row = next(z for z in c.get("/api/views/zoneOrder").json()["zones"] if z["zoneId"] == "B-7")
    assert row["registerNotChecked"] == 1 and row["lastCheckAt"] is None  # still counts as not yet checked


def test_dismiss_needs_a_reason(c):
    assert c.post("/api/suggested-checks/B-8/dismiss", json={"reason": ""}).json()["code"] == "INVALID"
    c.post("/api/suggested-checks/B-8/dismiss", json={"reason": "Checked by the army this morning"})
    assert "B-8" not in {s["zoneId"] for s in c.get("/api/views/zoneOrder").json()["suggestedChecks"]}


def test_tr_has_a_view_and_its_c04_job(c):
    v = c.get("/api/views/teamMissions/T-R").json()
    assert v["label"] == "Team T-R (truck)" and [j["caseId"] for j in v["jobs"]] == ["C-04"]
    assert v["team"]["resource"]["seatUnitsLeft"] == 3
