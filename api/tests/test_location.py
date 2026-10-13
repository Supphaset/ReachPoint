"""Locating a request (D25): pins, GPS outside the area, addresses via Pinpoint or the stand-in, and privacy."""

import json
import os

import pytest

os.environ["REACHPOINT_AI"] = "off"
pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

import api.main as main  # noqa: E402
from api.location import pinpoint  # noqa: E402
from api.location.resolve import resolve  # noqa: E402

MARKET_PIN = {"kind": "pin", "lat": 7.0089, "lon": 100.4705, "method": "map"}
BANGKOK_GPS = {"kind": "pin", "lat": 13.7563, "lon": 100.5018, "method": "gps", "accuracyM": 12}


@pytest.fixture(autouse=True)
def no_pinpoint_key(monkeypatch):
    monkeypatch.setattr(pinpoint, "_config", lambda name: None)


@pytest.fixture
def c():
    main.USE_AI = False
    main.reset()
    return TestClient(main.app)


def test_map_pin_snaps_to_segment_and_landmark():
    loc = resolve(MARKET_PIN)
    assert loc["status"] == "located" and loc["segmentId"] == "B-3-L2" and loc["landmarkLabel"] == "B-3 · L2 Market"
    assert loc["source"] == "caller pin (map)" and loc["provider"] == "device"


def test_gps_outside_the_area_keeps_no_point():
    loc = resolve(BANGKOK_GPS)
    assert loc["status"] == "outside_area" and loc["at"] is None and "segmentId" not in loc


def test_gps_precision_follows_accuracy():
    assert resolve({**MARKET_PIN, "method": "gps", "accuracyM": 10})["precision"] == "house"
    assert resolve({**MARKET_PIN, "method": "gps", "accuracyM": 120})["precision"] == "street"


def test_address_stand_in_and_unlocated():
    hit = resolve({"kind": "address", "text": "12/3 ซอยหลังตลาดกิมหยง หาดใหญ่"})
    assert hit["status"] == "located" and hit["provider"] == "stand-in" and hit["segmentId"] == "B-3-L2"
    assert resolve({"kind": "address", "text": "near the B-3 market"})["precision"] == "landmark"
    miss = resolve({"kind": "address", "text": "nowhere road 99"})
    assert miss["status"] == "unlocated" and miss["at"] is None


def test_pinpoint_reply_is_parsed_and_a_failure_falls_back(monkeypatch):
    monkeypatch.setattr(pinpoint, "_config", lambda name: "test-key" if name == "PINPOINT_API_KEY" else None)
    monkeypatch.setattr(pinpoint, "_request", lambda text, key: [{"lat": 7.0089, "lng": 100.4705, "level": "house", "name": text}])
    loc = resolve({"kind": "address", "text": "123/4 ซอย 5 หาดใหญ่"})
    assert loc["provider"] == "pinpoint" and loc["source"] == "Pinpoint address match" and loc["segmentId"] == "B-3-L2"

    def boom(text, key):
        raise pinpoint.httpx.ConnectError("down")
    monkeypatch.setattr(pinpoint, "_request", boom)
    loc = resolve({"kind": "address", "text": "12/3 ซอยหลังตลาดกิมหยง"})
    assert loc["provider"] == "stand-in" and loc["status"] == "located"


def test_locate_route_is_read_only(c):
    before = json.dumps(main.memory.store.seed, sort_keys=True)
    r = c.post("/api/locate", json={"location": MARKET_PIN})
    assert r.status_code == 200 and r.json()["value"]["segmentId"] == "B-3-L2"
    assert c.post("/api/locate", json={"location": {"kind": "pin", "method": "map"}}).status_code == 422
    assert json.dumps(main.memory.store.seed, sort_keys=True) == before


def test_caller_pin_becomes_the_exact_pickup_only_for_the_desk_and_the_taking_team(c):
    r = c.post("/api/intake/text", json={"text": "น้ำถึงอก ยายเดินไม่ได้", "submissionId": "L-1", "location": MARKET_PIN}).json()["value"]
    row = next(x for x in c.get("/api/views/reviewQueue").json()["reports"] if x["reportId"] == r["reportId"])
    assert row["location"]["segmentId"] == "B-3-L2" and row["suggestedSegment"]["segmentId"] == "B-3-L2"
    a = c.post(f"/api/reports/{r['reportId']}/approve", json={
        "segmentId": "B-3-L2", "people": {"adults": 2, "children": 0, "infants": 0, "stretcher": 1},
        "needs": ["evacuation_transport"], "waterBand": "chest", "submissionId": "L-2"}).json()["value"]
    status = json.dumps(c.get(f"/api/status/{r['statusToken']}").json())
    assert "100.4705" not in status and "7.0089" not in status  # the family's page never shows a point
    open_row = next(x for x in c.get("/api/views/teamMissions/T-S").json()["open"] if x["listingId"] == a["listingIds"][0])
    assert "100.4705" not in json.dumps(open_row)  # not before a team takes it
    al = c.post(f"/api/listings/{open_row['listingId']}/claim", json={
        "teamId": "T-S", "groupIds": [open_row["groups"][0]["groupId"]], "expectedRevision": open_row["needRevision"],
        "submissionId": "L-3"}).json()["value"]
    job = next(j for j in c.get("/api/views/teamMissions/T-S").json()["jobs"] if j["allocationId"] == al["allocationId"])
    assert job["pickup"]["at"] == [100.4705, 7.0089] and job["pickup"]["source"] == "caller pin (map)"


def test_coordinator_address_from_a_phone_call_overrides(c):
    r = c.post("/api/intake/text", json={"text": "phone call: water rising fast", "channel": "phone", "submissionId": "L-4"}).json()["value"]
    a = c.post(f"/api/reports/{r['reportId']}/approve", json={
        "segmentId": "B-3-L5", "people": {"adults": 1, "children": 0, "infants": 0, "stretcher": 0},
        "needs": ["evacuation_transport"], "submissionId": "L-5",
        "location": {"kind": "address", "text": "45 ถนนนิพัทธ์อุทิศ 2"}}).json()["value"]
    need = next(n for cse in main.memory.store.cases if cse["caseId"] == a["caseId"] for n in cse["needs"])
    assert need["exactPickup"]["source"] == "demo address list (Pinpoint stand-in)" and need["exactPickup"]["precision"] == "house"
