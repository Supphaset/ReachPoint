"""V2 rooms isolate sessions and reset only the current visitor's state."""

from fastapi.testclient import TestClient

import api.main as main
from api.server.rooms import Rooms

A, B = {"X-Demo-Room": "judge-aaaa"}, {"X-Demo-Room": "judge-bbbb"}


def test_rooms_are_separate_and_reset_only_your_own():
    c = TestClient(main.app)
    session = c.post("/api/v2/chat/sessions", headers=A, json={"lang": "en"}).json()
    path = f"/api/v2/chat/sessions/{session['id']}/status"
    assert c.get(path, headers=A).status_code == 200
    assert c.get(path, headers=B).status_code == 404
    assert c.post("/api/v2/clock", headers=B, json={"action": "reset"}).status_code == 200
    assert c.get(path, headers=A).status_code == 200
    assert c.post("/api/v2/clock", headers=A, json={"action": "reset"}).status_code == 200
    assert c.get(path, headers=A).status_code == 404


def test_bad_room_ids_use_the_main_room_and_the_cap_drops_the_oldest():
    assert Rooms.clean("../../etc") == "main" and Rooms.clean(None) == "main" and Rooms.clean("AB12CD") == "AB12CD"
    r = Rooms(cap=3)
    for i in range(5):
        r.get(f"room-{i}")
    assert len(r) == 3 and {x.id for x in r.all()} == {"room-2", "room-3", "room-4"}
