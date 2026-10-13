"""Zone briefing text (C8): shown only when every number and place is in the facts and it makes no route, safety or
priority claim. Run: python -m pytest api/tests -q (no network)."""

import os
import time

import pytest

from api.ai import briefing_text as B
from api.views import store as S
from api.views.briefing import area_briefing

ZONES = {z["zoneId"]: z for z in area_briefing(S.load(), "P-B", "2026-10-11T03:15:00Z")["zones"]}
F = B.zone_facts(ZONES["B-6"])


def test_facts_are_the_zone_view_only():
    assert F["zone"] == "B-6" and F["segments not yet checked"] == "6 of 7"
    assert F["water reported by callers"] == ["Up to the 2nd floor at B-6 · L2 School"]
    assert "estimate" in next(k for k in F if k.startswith("people living"))
    assert "register" not in str(F).lower()  # teams read this text: no register details


@pytest.mark.parametrize("text, why", [
    ("Callers report water up to the 2nd floor at B-6 · L1 School.", "place"),
    ("8 of 7 segments are not yet checked.", "number"),
    ("About 9,500 people live in segments not yet checked (estimate).", "number"),
    ("The main road into B-6 is passable.", "route"),
    ("The area is dry now.", "dryness"),
    ("Teams should go to B-6 first.", "priority"),
    ("About two thousand people live here.", "number word"),
    ("Water at L2 is high.", "landmark code"),
    ("There are 6 reviewed evacuation requests.", "number with the wrong label"),  # 6 is unchecked segments
])
def test_blocked(text, why):
    assert B.validate(text, F), why


def test_allowed():
    ok = ("Reviewed calls report 3 people needing evacuation, and callers report water up to the 2nd floor at B-6 · L2 School. "
          "6 of 7 segments are not yet checked; an estimated 9,100–13,000 people live in them.")
    assert B.validate(ok, F) == []


def test_without_a_key_the_briefing_is_unavailable(monkeypatch):
    monkeypatch.setattr(B, "api_key", lambda: None)
    assert B.write(F) == {"state": "unavailable", "text": None, "reason": "no_ai_key"}


def test_server_writes_in_the_background_and_keeps_it(monkeypatch):
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient
    import api.main as main
    calls = []
    monkeypatch.setattr(main.briefing_text, "write", lambda facts: (calls.append(facts["zone"]),
                        {"state": "ready", "text": f"Zone {facts['zone']} facts only.", "source": "gemini:test"})[1])
    monkeypatch.setattr(main.time, "sleep", lambda s: None)
    monkeypatch.setattr(main, "USE_AI", True)
    main.BRIEFINGS.clear()
    main._pending.clear()
    c = TestClient(main.app)
    first = c.get("/api/views/areaBriefing/P-C").json()
    assert {z["briefing"]["state"] for z in first["zones"]} <= {"writing", "ready"}
    for _ in range(50):
        later = c.get("/api/views/areaBriefing/P-C").json()
        if all(z["briefing"]["state"] == "ready" for z in later["zones"]):
            break
        time.sleep(0.05)
    assert [z["briefing"]["text"] for z in later["zones"]] == ["Zone C-1 facts only.", "Zone C-2 facts only."]
    c.get("/api/views/areaBriefing/P-C")
    assert sorted(calls) == ["C-1", "C-2"]  # once per set of facts, not per view
    monkeypatch.setattr(main, "USE_AI", False)
