"""Unreported model exposure stays separate from requests and boat passengers."""
from types import SimpleNamespace

import pytest

from api.v2 import board, copilot, sim


@pytest.fixture(scope="module")
def state():
    return board.state(96)


def test_flooded_zone_without_requests_has_unheard_streets(state):
    u = state["zones"]["B5"]["unheard"]
    assert u["notHeard"][1] > 0
    assert u["heardFrom"] == 0
    assert 0 < len(u["streets"]) <= 5
    assert u["atH"] == 96
    assert "not reports" in u["basis"]
    assert [r["floodedBuildings"] for r in u["streets"]] == sorted([r["floodedBuildings"] for r in u["streets"]], reverse=True)
    for r in u["streets"]:
        assert r["nameEn"] and r["depthM"] > 0
        assert sim.depth(r["lon"], r["lat"], 96) > 0
    assert copilot.get_zone(state, "B5")["unheard"] == u


def test_streets_follow_clock_and_exclude_any_reported_street(monkeypatch):
    buildings = [SimpleNamespace(id=str(i), lon=i, lat=0) for i in range(3)]
    g = SimpleNamespace(_unheard_streets={"X1": [(b, f"Street {b.id}", f"Street {b.id}") for b in buildings]})
    monkeypatch.setattr(sim, "depth", lambda lon, lat, hour: 0 if hour < 2 else 1 + lon)
    hh = [SimpleNamespace(building_id="0", lon=0, lat=0)]
    u = board.unheard_view(SimpleNamespace(now_h=1, quiet=set()), g, "X1", {"modelledFlooded": [27.2, 54.4]}, hh)
    assert u["streets"] == []
    u = board.unheard_view(SimpleNamespace(now_h=3, quiet={"X1"}), g, "X1", {"modelledFlooded": [27.2, 54.4]}, hh)
    assert u["estimatedHouseholds"] == [10, 20]
    assert u["notHeard"] == [9, 19] and u["quiet"]
    assert {r["name"] for r in u["streets"]} == {"Street 1", "Street 2"}


def test_plan_keeps_spare_seats_and_depth_order(state):
    p = copilot.draft_plan(state, "B5", 6)
    assert p["seatsKeptFree"] == 2
    assert p["unheard"]["notHeard"][1] > 0
    assert p["checkOnTheWay"]
    assert [r["depthM"] for r in p["checkOnTheWay"]] == sorted([r["depthM"] for r in p["checkOnTheWay"]], reverse=True)
    assert copilot.draft_plan(state, "B5", 4)["seatsKeptFree"] == 1


@pytest.mark.parametrize("people,free", [(3, 2), (6, 0)])
def test_requests_get_priority_over_spare_capacity(state, monkeypatch, people, free):
    family = {"id": "HH1", "people": people, "children": 0, "elderly": 0, "cannotWalk": 0, "urgent": True,
              "depth": {"m": 1}, "hoursSilent": 1, "firstHand": True, "priority": 100}
    monkeypatch.setattr(copilot, "_open", lambda *a: [family])
    p = copilot.draft_plan(state, "B5", 6)
    assert p["runs"][0]["people"] == people
    assert p["seatsKeptFree"] == free


def test_selected_zone_rules_answer_and_number_check(state, monkeypatch):
    monkeypatch.setenv("REACHPOINT_AI", "off")
    q = "I have one boat with 6 seats for zone B5. Who first, and who else may need us?"
    answer, calls, plan = copilot.rules_answer(state, q)
    assert plan["zone"] == "B5"
    assert "haven't asked" in answer and "keep 2 seats free" in answer
    assert all(r["nameEn"] in answer for r in plan["checkOnTheWay"])
    assert copilot.check(answer, [c["result"] for c in calls], q) is None
    assert copilot.check(answer + " There are 987654 households.", [c["result"] for c in calls], q)
    assert copilot.ask(state, q)["plan"]["zone"] == "B5"


def test_page_zone_takes_precedence_over_question(state, monkeypatch):
    from fastapi.testclient import TestClient
    from api.main import app
    from api.v2 import routes
    monkeypatch.setattr(routes, "_state", lambda *a: state)
    monkeypatch.setenv("REACHPOINT_AI", "off")
    result = TestClient(app).post("/api/v2/v/copilot", json={"zone": "B5", "question": "6 seats for zone D12"}, headers={"X-Demo-Room": "unheard-zone"})
    assert result.status_code == 200
    assert result.json()["plan"]["zone"] == "B5"


def test_check_rejects_spare_seats_even_if_number_exists_in_tools(state):
    p = copilot.draft_plan(state, "B5", 6)
    assert copilot.check("Keep 2 seats free.", [p], "6 seats") is None
    assert copilot.check("Keep 6 seats free.", [p], "6 seats") == "spare seats differ from plan"


def test_gemini_cannot_skip_unheard_guidance_or_switch_zones(state, monkeypatch):
    monkeypatch.setenv("REACHPOINT_AI", "on")
    p = copilot.draft_plan(state, "B5", 6)
    monkeypatch.setattr(copilot, "within", lambda *args: ("Go to [D12] first.", [{"result": p}], p, "gemini:test"))
    result = copilot.ask(state, "6 seats for zone B5")
    assert result["reader"] == "rules"
    assert result["plan"]["zone"] == "B5"
    assert "haven't asked" in result["answer"]
