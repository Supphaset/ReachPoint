"""HTTP layer of the starter server (contract/api.md). Needs fastapi + httpx (api/requirements*.txt)."""

import pytest

fastapi = pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

import api.main as main  # noqa: E402


@pytest.fixture
def client():
    main.reset()
    return TestClient(main.app)


def test_views_and_health(client):
    assert client.get("/api/health").json()["ok"]
    v = client.get("/api/views/teamMissions/T-S").json()
    assert v["open"][0]["listingId"] == "L-C01-EVAC"
    assert client.get("/api/views/areaBriefing/P-B").json()["areaId"] == "P-B"
    assert len(client.get("/api/views/risingWater/P-B").json()) == 15
    assert client.get("/api/views/zoneOrder").json()["suggestedChecks"][0]["zoneId"] == "B-4"
    assert client.get("/api/views/teamMissions/T-NOPE").status_code == 404


def test_claim_then_view_then_conflict(client):
    r = client.post("/api/listings/L-C01-EVAC/claim", json={"teamId": "T-S", "groupIds": ["L-C01-EVAC-G1"], "expectedRevision": 2, "submissionId": "SUB-A"})
    assert r.status_code == 200 and r.json()["value"]["pickup"]["precision"] == "building"
    again = client.post("/api/listings/L-C01-EVAC/claim", json={"teamId": "T-S", "groupIds": ["L-C01-EVAC-G1"], "expectedRevision": 2, "submissionId": "SUB-A"})
    assert again.json() == r.json()  # same submission: same answer, no second job
    assert len(client.get("/api/views/teamMissions/T-S").json()["jobs"]) == 1
    taken = client.post("/api/listings/L-C04-EVAC/claim", json={"teamId": "T-S", "groupIds": ["L-C04-EVAC-G1"], "expectedRevision": 1})
    assert taken.status_code == 409 and taken.json() == {"code": "ALREADY_TAKEN", "message": "Already taken by T-R",
                                                         "detail": {"groupIds": ["L-C04-EVAC-G1"], "takenBy": "T-R"}}
    assert client.post("/api/listings/L-C01-EVAC/claim", json={"teamId": "T-S"}).status_code == 422


def test_urgent_flag_and_ask(client):
    assert client.post("/api/listings/L-C08-EVAC/urgent-flag", json={"reason": " "}).json()["code"] == "INVALID"
    assert client.post("/api/listings/L-C08-EVAC/urgent-flag", json={"reason": "2nd floor", "confirmedNow": True}).status_code == 200
    reds = [r["caseId"] for r in client.get("/api/views/teamMissions/T-S").json()["open"] if r["colour"] == "red"]
    assert reds == ["C-01", "C-08"]
    assert client.post("/api/ask-teams", json={"suggestionId": "SUG-x", "teamIds": ["T-K"]}).json()["asks"][0]["teamId"] == "T-K"


def test_unknown_api_route_is_404_not_the_app(client):
    assert client.get("/api/nope").status_code == 404
