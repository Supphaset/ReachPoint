"""Zone planning validates proposals against current room records; no paid calls."""
from collections import Counter
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.v2 import board, cases, geo, limits, routes, suggest

TEAM = {"team": "Demo boat", "vehicle": "boat", "seats": 6, "eta": "12:00", "lang": "en"}


@pytest.fixture(scope="module")
def state():
    return board.state(96)


@pytest.fixture
def ctx():
    def family(id, people=2, **kw):
        return {"id": id, "people": people, "children": 1, "elderly": 0, "cannotWalk": 0, "urgent": True,
                "depth": {"m": 1.2, "hi": 1.5}, "hoursSilent": 3, "texts": ["Please help my child"], "reachable": True, **kw}
    return {"team": TEAM, "otherTeams": [], "families": [family("HH1"), family("HH2"), family("HH3")], "reserveTarget": 2,
            "unheard": {"streets": [{"name": "ถนน", "nameEn": "Street", "floodedBuildings": 8}], "notHeard": [3, 6]}}


def test_rules_capacity_and_reserve(ctx):
    out = suggest.rules(ctx)
    loads = Counter()
    for v in out["order"]:
        loads[v["run"]] += 2
    assert out["spareSeats"] == 2 and max(loads.values()) <= 4
    assert {v["householdId"] for v in out["order"]} == {"HH1", "HH2", "HH3"}
    assert "child" in " ".join(out["bring"])


def test_bad_gemini_reply_drops_ids_quotes_streets_and_unfounded_numbers(ctx):
    raw = suggest.rules(ctx)
    raw["order"] += [{"householdId": "invented", "run": 1, "reason": "Urgent", "quote": "fake"}]
    raw["order"][0].update(quote="invented quote", reason="987654 people")
    raw["checkStreets"] += [{"name": "Invented road", "why": "help"}]
    raw["summary"] = "987654 households waiting"
    out = suggest.validate(raw, ctx)
    assert all(v["householdId"] in {"HH1", "HH2", "HH3"} for v in out["order"])
    assert out["order"][0]["quote"] == ""
    assert out["order"][1]["quote"] == "Please help my child"
    assert "987654" not in str(out)
    assert [s["name"] for s in out["checkStreets"]] == ["Street"]


def test_model_cannot_overload_runs_or_split_households(ctx):
    raw = suggest.rules(ctx)
    for v in raw["order"]:
        v["run"] = 1
    ctx["families"][0]["people"] = 5
    out = suggest.validate(raw, ctx)
    assert [v["householdId"] for v in out["order"]] == ["HH1"]
    assert out["spareSeats"] == 1
    assert len(out["warnings"]) == 2


@pytest.mark.parametrize("vehicle,hi,walk,expected", [("truck", 1.1, 0, False), ("truck", .9, 0, True), ("foot", .4, 0, False), ("foot", .1, 1, False), ("boat", 3, 1, True), ("truck", None, 0, False)])
def test_vehicle_access(vehicle, hi, walk, expected):
    assert suggest.reachable({"depth": {"hi": hi}, "cannotWalk": walk}, vehicle) == expected


def test_unreachable_and_unknown_sizes_are_warnings(ctx):
    ctx["families"][0]["reachable"] = False
    ctx["families"][1]["people"] = None
    raw = suggest.rules(ctx)
    assert [v["householdId"] for v in raw["order"]] == ["HH3"]
    assert any("HH1: needs a boat" == w for w in raw["warnings"])
    assert any("size" in w for w in raw["warnings"])


def test_real_context_only_contains_current_zone_waiting_households(state):
    ctx = suggest.context(state, "D12", TEAM, [])
    ids = {r["id"] for r in cases._rows(state, "D12") if r["status"] not in cases.CLOSED}
    assert {r["id"] for r in ctx["families"]} == ids
    assert all("texts" in h and "depth" in h for h in ctx["families"])
    assert "water" in ctx and "shelters" in ctx and "otherTeams" in ctx


@pytest.mark.parametrize("model_result", [None, ({"invalid": True}, "gemini:test"), ({"order": [], "spareSeats": 0, "bring": [], "checkStreets": [], "warnings": [], "summary": ""}, "gemini:test")])
def test_fallback_when_model_unavailable_or_nothing_valid(monkeypatch, state, model_result):
    monkeypatch.setenv("REACHPOINT_AI", "on")
    monkeypatch.setattr(suggest, "within", lambda *a: model_result)
    out = suggest.suggest(state, "D12", TEAM, [])
    assert out["reader"] == "rules" and out["context"]["waiting"] > 0


def test_model_call_is_structured_and_delimits_user_data(monkeypatch, ctx):
    from api.ai import gemini
    monkeypatch.setattr(gemini, "available", lambda: True)
    monkeypatch.setattr(gemini, "models", lambda _: ["test"])
    seen = []
    raw = suggest.rules(ctx)
    def post(model, body, timeout):
        seen.append(body)
        import json
        return SimpleNamespace(raise_for_status=lambda: None, json=lambda: {"candidates": [{"content": {"parts": [{"text": json.dumps(raw)}]}}]})
    monkeypatch.setattr(gemini, "post", post)
    assert suggest._gemini(ctx)[1] == "gemini:test"
    assert len(seen) == 1
    assert seen[0]["generationConfig"]["responseMimeType"] == "application/json"
    assert seen[0]["generationConfig"]["responseSchema"]["type"] == "OBJECT"
    assert "<zone_context_json>" in seen[0]["contents"][0]["parts"][0]["text"]


def test_suggest_shares_copilot_limit_keys(monkeypatch):
    monkeypatch.setattr(limits, "limits", limits.Limits(clock=lambda: 0))
    for _ in range(7):
        assert not limits.http_limit("POST", "/api/v2/v/copilot", "ip", "room", {})
    assert not limits.http_limit("POST", "/api/v2/v/zones/B5/suggest", "ip", "room", {})
    assert limits.http_limit("POST", "/api/v2/v/copilot", "ip", "room", {}) > 0


@pytest.fixture
def client():
    return TestClient(app), {"X-Demo-Room": "pytest-suggest-" + uuid4().hex[:12]}


def test_posted_order_is_persisted_and_visible_to_own_team_only(client):
    c, headers = client
    zone = c.get("/api/v2/v/zones/D12", headers=headers).json()
    order = [r["id"] for r in zone["households"] if r["status"] not in cases.CLOSED][:3][::-1]
    assert len(order) > 1
    result = c.post("/api/v2/plans", headers=headers, json={"text": "Demo boat 6 seats zone D12 around 12:00", "team": "Demo boat", "zone": "D12", "order": order})
    assert result.status_code == 200, result.text
    assert result.json()["plan"]["order"] == order
    assert result.json()["plan"]["told"] == len(order)
    mission = c.get("/api/v2/v/zones/D12?team=Demo%20boat", headers=headers).json()
    assert mission["plan"]["order"] == order
    assert c.get("/api/v2/v/zones/D12?team=Other", headers=headers).json()["plan"] is None
    for invalid in (["invented"], [order[0], order[0]]):
        assert c.post("/api/v2/plans", headers=headers, json={"text": "Boat to zone B5", "zone": "B5", "order": invalid}).status_code == 422


@pytest.mark.parametrize("override", [{"seats": 0}, {"seats": 21}, {"vehicle": "plane"}, {"eta": "25:00"}, {"team": "x" * 81}, {"people": 999}])
def test_input_validation(client, override):
    c, headers = client
    assert c.post("/api/v2/v/zones/B5/suggest", headers=headers, json={**TEAM, **override}).status_code == 422


def test_report_in_b5_then_real_suggest_endpoint(client):
    c, headers = client
    b = next(b for b in geo.load().buildings.values() if b.zone_id == "B5")
    created = c.post("/api/v2/chat/sessions?lang=en", headers=headers)
    headers["X-Demo-Room"] = created.headers["X-Demo-Room"]
    sid = created.json()["id"]
    report = c.post(f"/api/v2/chat/sessions/{sid}/turn", headers=headers, json={"text": "Water at my waist. We are 2 people. My mother cannot walk. Please help.", "pin": {"lon": b.lon, "lat": b.lat, "method": "map"}})
    assert report.status_code == 200, report.text
    zone = c.get("/api/v2/v/zones/B5", headers=headers).json()
    assert zone["totals"]["open"] > 0
    out = c.post("/api/v2/v/zones/B5/suggest", headers=headers, json=TEAM)
    assert out.status_code == 200, out.text
    out = out.json()
    assert out["reader"] == "rules" and out["order"]
    assert {v["householdId"] for v in out["order"]} <= {r["id"] for r in zone["households"]}
    assert out["context"]["waiting"] == zone["totals"]["open"]


def test_capped_model_falls_back_without_network(monkeypatch, state):
    from api.ai import gemini
    from api.ai.usage import BudgetExceeded
    monkeypatch.setenv("REACHPOINT_AI", "on")
    monkeypatch.setattr(gemini, "available", lambda: True)
    monkeypatch.setattr(gemini, "models", lambda _: ["test"])
    def capped(*a, **kw):
        raise BudgetExceeded("cap")
    monkeypatch.setattr(gemini, "post", capped)
    assert suggest.suggest(state, "B5", TEAM, [])["reader"] == "rules"


def test_valid_model_reply_is_labelled_and_checked(monkeypatch, ctx):
    monkeypatch.setenv("REACHPOINT_AI", "on")
    raw = suggest.rules(ctx)
    monkeypatch.setattr(suggest, "within", lambda *a: (raw, "gemini:test"))
    out = suggest.answer(ctx)
    assert out["reader"] == "gemini:test"
    assert out["spareSeats"] == 2
    assert len(out["order"]) == 3
