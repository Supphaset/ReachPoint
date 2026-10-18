"""Synthetic outbound calls, with no model or microphone required."""
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from api.v2 import calls, intake as I, routes as R, geo as G
from api.v2.live import _config, _turn_in_room


@pytest.fixture
def family(monkeypatch):
    from api.main import app
    v = R.V2Room(now_h=200)
    s = I.new_session("en")
    v.sessions[s.id] = s
    monkeypatch.setattr(R, "room", lambda: v)
    occupied = R._state(v)["world"].by_building
    building = next(b for b in G.load().buildings.values() if b.zone_id == "D12" and b.id not in occupied)
    R.turn(s.id, "Water is up to my waist. I am with my mom who cannot walk. 2 people.", pin={"lon": building.lon, "lat": building.lat, "method": "map"})
    s.facts["address"] = {"value": "52/9 Phetkasem Soi 2", "quote": "52/9 Phetkasem Soi 2"}
    return TestClient(app), v, s


def test_safety_call_pending_and_status(family):
    c, v, s = family
    out = c.post(f"/api/v2/chat/sessions/{s.id}/simulate", json={"event": "safetyCall"})
    assert out.status_code == 200
    assert out.json()["incoming"]["kind"] == "safetyCheck"
    assert c.get(f"/api/v2/chat/sessions/{s.id}/status").json()["incoming"] == s.incoming
    assert c.get(f"/api/v2/me/{s.token}").json()["incoming"] == s.incoming


def test_opening_real_facts_and_one_question():
    s = I.new_session("en")
    s.facts = {"address": {"value": "52/9 Phetkasem Soi 2"}, "depthRange": {"quote": "water was at your waist"}}
    hh = SimpleNamespace(people=2, cannot_walk=1, last_heard_h=80)
    en = calls.opening(s, hh)
    assert all(word in en for word in ("52/9", "waist", "2 people", "cannot walk"))
    assert en.count("?") == 1
    assert "haven't heard" in calls.opening(s, hh, "lostContact")
    s.lang = "th"
    assert "ตอนนี้น้ำสูงขึ้นไหมคะ" in calls.opening(s, hh)
    assert "one question at a time" in str(_config("th", True).system_instruction)


def test_planner_lost_contact_then_answer_updates_board(family):
    c, v, s = family
    v.now_h += 25
    st = R.session_status(s.id)
    assert st["status"] == "lostContact" and st["incoming"]["kind"] == "lostContact"
    c.post(f"/api/v2/chat/sessions/{s.id}/incoming", json={"action": "answer"})
    out = _turn_in_room("main", s.id, "Water is at my chest. 2 people. Need help now", True)
    hh = R._state(v)["world"].households[s.household_id]
    assert hh.last_heard_h == v.now_h and hh.status == "open" and hh.urgent
    assert s.incoming is None
    assert any(f["field"] == "depthRange" for f in out["effects"]["facts"])
    assert out["effects"]["reader"].startswith("gemini-live")
    assert any("answered ReachPoint's safety call" in a["text"] for a in R._state(v)["world"].activity)


def test_decline_twice_counts_one_missed_check(family):
    c, v, s = family
    before = R._state(v)["world"].households[s.household_id].checks_unanswered
    for _ in range(2):
        c.post(f"/api/v2/chat/sessions/{s.id}/simulate", json={"event": "safetyCall"})
        assert c.post(f"/api/v2/chat/sessions/{s.id}/incoming", json={"action": "decline"}).status_code == 200
        assert s.incoming is None
    assert R._state(v)["world"].households[s.household_id].checks_unanswered == before + 1
    assert c.post(f"/api/v2/chat/sessions/{s.id}/incoming", json={"action": "answer"}).status_code == 409


def test_live_unavailable_sends_text_checkin(family):
    c, v, s = family
    c.post(f"/api/v2/chat/sessions/{s.id}/simulate", json={"event": "safetyCall"})
    with c.websocket_connect(f"/api/v2/chat/sessions/{s.id}/live?mode=outbound&kind=safetyCheck", headers={"origin": "http://localhost:5173"}) as ws:
        message = ws.receive_json()
        assert message["type"] == "fallback"
        assert "by text" in message["text"]
    assert s.transcript[-1]["kind"] == "checkin" and s.incoming is None
    assert s.follow == "checkin"
