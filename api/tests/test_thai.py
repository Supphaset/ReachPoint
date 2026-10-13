"""Thai twins for the lines the server writes on the victim and volunteer screens."""

import os

import pytest

os.environ["REACHPOINT_AI"] = "off"
pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

import api.main as main  # noqa: E402

THAI = range(0x0E00, 0x0E80)


def is_thai(s):
    return any(ord(ch) in THAI for ch in s)


@pytest.fixture
def c():
    main.USE_AI = False
    main.reset()
    return TestClient(main.app)


def test_family_status_has_thai_at_every_step_and_keeps_the_honest_wording(c):
    r = c.post("/api/intake/text", json={"text": "น้ำถึงอกแล้ว ยายเดินไม่ได้ ซอยหลังตลาด B-3", "submissionId": "TH-1"}).json()["value"]
    status = lambda: c.get(f"/api/status/{r['statusToken']}").json()["lines"]
    assert status()[0]["th"] == "เราได้รับคำขอของคุณแล้ว ผู้ประสานงานกำลังอ่านอยู่"
    a = c.post(f"/api/reports/{r['reportId']}/approve", json={
        "segmentId": "B-3-L2", "people": {"adults": 2, "children": 2, "infants": 0, "stretcher": 1},
        "needs": ["evacuation_transport"], "waterBand": "chest", "urgentReason": "Can't walk"}).json()["value"]
    line = status()[0]
    assert line["familyTh"] == "ครอบครัว 1" and "ยังไม่มีทีมรับงาน" in line["th"]
    lid = a["listingIds"][0]
    row = next(x for x in c.get("/api/views/teamMissions/T-S").json()["open"] if x["listingId"] == lid)
    u = row["urgency"]
    assert u["th"]["title"] == "ทำไมจึงเป็นเหตุฉุกเฉิน" and len(u["th"]["kit"]) == len(u["kit"])
    assert all(is_thai(f["th"]) for f in u["facts"])
    assert row["groups"][0]["labelTh"] == "ครอบครัว 1" and row["destination"]["th"]["label"].startswith("D1")
    al = c.post(f"/api/listings/{lid}/claim", json={"teamId": "T-S", "groupIds": [row["groups"][0]["groupId"]],
                                                    "expectedRevision": row["needRevision"], "submissionId": "TH-2"}).json()["value"]
    c.post(f"/api/allocations/{al['allocationId']}/window",
           json={"start": "2026-10-11T04:00:00Z", "end": "2026-10-11T05:00:00Z", "submissionId": "TH-3"})
    line = status()[0]
    assert line["text"].endswith("(team estimate, not a promise).")
    assert line["th"] == "ทีม T-S คาดว่าจะถึงประมาณ 11:00–12:00 (เป็นการประมาณของทีม ไม่ใช่คำสัญญา)"
    job = next(j for j in c.get("/api/views/teamMissions/T-S").json()["jobs"] if j["allocationId"] == al["allocationId"])
    assert job["pickup"]["at"] != [0, 0] and job["pickup"]["precision"] == "landmark"  # never a 0, 0 pickup


def test_typed_words_are_never_translated(c):
    r = c.post("/api/intake/text", json={"text": "Water at chest, B-3 market", "submissionId": "TH-4"}).json()["value"]
    a = c.post(f"/api/reports/{r['reportId']}/approve", json={
        "segmentId": "B-3-L2", "people": {"adults": 1, "children": 0, "infants": 0, "stretcher": 0},
        "needs": ["evacuation_transport"], "waterBand": "chest", "urgentReason": "Oxygen running out"}).json()["value"]
    row = next(x for x in c.get("/api/views/teamMissions/T-S").json()["open"] if x["listingId"] == a["listingIds"][0])
    flag = next(f for f in row["urgency"]["facts"] if f["kind"] == "flag")
    assert flag["th"] == "ผู้ประสานงานระบุว่าด่วน: Oxygen running out"
