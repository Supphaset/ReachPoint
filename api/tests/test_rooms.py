"""Demo rooms: two visitors never see or undo each other's work; a family link works from any device."""

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

import api.main as main  # noqa: E402
from api.server.rooms import Rooms  # noqa: E402

A, B = {"X-Demo-Room": "judge-aaaa"}, {"X-Demo-Room": "judge-bbbb"}


def _queue(c, h):
    return [r["reportId"] for r in c.get("/api/views/reviewQueue", headers=h).json()["reports"]]


def test_rooms_are_separate_and_reset_only_your_own(monkeypatch):
    monkeypatch.setattr(main, "USE_AI", False)
    c = TestClient(main.app)
    before_b = _queue(c, B)
    sent = c.post("/api/intake/text", headers=A, json={"text": "B-3 temple, water at the chest, 2 adults", "channel": "text"}).json()["value"]
    assert sent["reportId"] in _queue(c, A) and sent["reportId"] not in _queue(c, B)
    assert _queue(c, B) == before_b
    # the family opens the link on another phone, with no room: it still works
    assert c.get(f"/api/status/{sent['statusToken']}").status_code == 200
    c.post("/api/demo/reset", headers=B)
    assert sent["reportId"] in _queue(c, A)  # B's reset left A alone
    c.post("/api/demo/reset", headers=A)
    assert sent["reportId"] not in _queue(c, A)


def test_bad_room_ids_use_the_main_room_and_the_cap_drops_the_oldest():
    assert Rooms.clean("../../etc") == "main" and Rooms.clean(None) == "main" and Rooms.clean("AB12CD") == "AB12CD"
    r = Rooms(cap=3)
    for i in range(5):
        r.get(f"room-{i}")
    assert len(r) == 3 and {x.id for x in r.all()} == {"room-2", "room-3", "room-4"}
