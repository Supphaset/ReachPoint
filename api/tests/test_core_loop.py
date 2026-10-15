"""The core loop on the starter server: request → AI proposal → desk review → listing → team takes → family status.
Run: python -m pytest api/tests -q. The AI is replaced by the keyword stand-in here (REACHPOINT_AI=off), so the
tests make no network calls; test_extract.py checks the quote rule the real model must pass."""

import os

import pytest

os.environ["REACHPOINT_AI"] = "off"
fastapi = pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

import api.main as main  # noqa: E402

TEXT = "บ้านอยู่แถวโรงเรียน B-4 น้ำถึงอกแล้ว ยายป่วยติดเตียง ช่วยด้วยค่ะ"


@pytest.fixture
def c():
    main.USE_AI = False
    main.reset()
    return TestClient(main.app)


def test_request_to_listing_to_take_to_family_status(c):
    r = c.post("/api/intake/text", json={"text": TEXT, "submissionId": "SUB-I1"}).json()["value"]
    token, rid = r["statusToken"], r["reportId"]
    assert r["statusUrl"] == f"/status/{token}" and r["aiSource"] == "stand-in" and len(token) >= 22
    assert c.get(f"/api/status/{token}").json()["lines"][0]["text"] == "We received your request. A coordinator is reading it now."

    q = c.get("/api/views/reviewQueue").json()
    row = next(x for x in q["reports"] if x["reportId"] == rid)
    assert row["text"] == TEXT and row["suggestedSegment"]["segmentId"] == "B-4-L5"
    assert row["proposal"]["facts"]["water"] == {"band": "chest", "quote": "ถึงอก"}
    assert not any(l["segmentId"] in ("D1", "H1") for l in q["landmarks"])

    before = {l["listingId"] for l in c.get("/api/views/teamMissions/T-S").json()["open"]}
    a = c.post(f"/api/reports/{rid}/approve", json={
        "segmentId": "B-4-L5", "people": {"adults": 2, "children": 0, "infants": 0, "stretcher": 1},
        "needs": ["evacuation_transport"], "waterBand": "chest", "urgentReason": "Bedridden, can't self-evacuate"}).json()["value"]
    assert a == {"caseId": "C-09", "listingIds": ["L-C09-EVAC"]}
    open_ = c.get("/api/views/teamMissions/T-S").json()["open"]
    new = next(l for l in open_ if l["listingId"] == "L-C09-EVAC")
    assert {l["listingId"] for l in open_} - before == {"L-C09-EVAC"}
    assert new["colour"] == "red" and new["landmarkLabel"] == "B-4 · L5 School"
    assert [f["text"] for f in new["urgency"]["facts"] if f["kind"] == "water"] == ["Chest deep (about 1.3 m) at the landmark"]
    assert TEXT not in str(open_)  # teams never see the caller's own words

    brief = c.get("/api/views/areaBriefing/P-B").json()
    assert any(x["caseId"] == "C-09" for z in brief["zones"] for x in z["cases"])
    assert c.get(f"/api/status/{token}").json()["lines"][0]["text"].startswith("On the list. No team has taken it yet.")

    job = c.post("/api/listings/L-C09-EVAC/claim", json={"teamId": "T-S", "groupIds": ["L-C09-EVAC-G1"], "expectedRevision": 1}).json()["value"]
    assert c.get(f"/api/status/{token}").json()["lines"][0]["text"] == "Team T-S has taken your request. They haven't set a time yet."
    c.post(f"/api/allocations/{job['allocationId']}/window", json={"start": "2026-10-11T06:00:00Z", "end": "2026-10-11T07:00:00Z"})
    assert c.get(f"/api/status/{token}").json()["lines"][0]["text"] == \
        "Team T-S expects to reach you about 13:00–14:00 (team estimate, not a promise)."
    c.post(f"/api/allocations/{job['allocationId']}/close", json={"outcome": "done"})
    assert c.get(f"/api/status/{token}").json()["lines"][0]["text"].startswith("Picked up by Team T-S at ")


def test_review_rules(c):
    rid = c.post("/api/intake/text", json={"text": "help, water at the waist near the temple"}).json()["value"]["reportId"]
    bad = c.post(f"/api/reports/{rid}/approve", json={"segmentId": "D1", "people": {"adults": 1}, "needs": ["evacuation_transport"]})
    assert bad.status_code == 409 and bad.json()["code"] == "INVALID"
    assert c.post(f"/api/reports/{rid}/approve", json={"segmentId": "B-3-L1", "people": {}, "needs": ["evacuation_transport"]}).json()["code"] == "INVALID"
    assert c.post(f"/api/reports/{rid}/approve", json={"segmentId": "B-3-L1", "people": {"adults": 1}, "needs": []}).json()["code"] == "INVALID"
    assert c.post(f"/api/reports/{rid}/reject", json={"reason": " "}).json()["code"] == "INVALID"
    assert c.post(f"/api/reports/{rid}/reject", json={"reason": "Duplicate of C-03"}).status_code == 200
    assert c.post(f"/api/reports/{rid}/reject", json={"reason": "again"}).json()["code"] == "ALLOCATION_CLOSED"
    assert rid not in {r["reportId"] for r in c.get("/api/views/reviewQueue").json()["reports"]}


def test_status_link_is_private_and_unguessable(c):
    assert c.get("/api/status/not-a-real-token").status_code == 404
    v = c.post("/api/intake/text", json={"text": "need food and drinking water, 3 people"}).json()["value"]
    s = c.get(f"/api/status/{v['statusToken']}").json()
    assert set(s) <= {"reportId", "generatedAt", "label", "state", "lines", "caseId", "lastConfirmedAt", "receipt", "completedAt"}


def test_empty_request_refused(c):
    assert c.post("/api/intake/text", json={"text": ""}).status_code == 422
    assert c.post("/api/intake/text", json={"text": "   "}).json()["code"] == "INVALID"
