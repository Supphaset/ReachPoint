import threading

from api.ai.budget import within


def test_optional_read_has_a_wall_clock_budget():
    release = threading.Event()
    try:
        assert within(0.01, release.wait, 2) is None
    finally:
        release.set()
    assert within(1, lambda: "done") == "done"


def test_copilot_falls_back_when_its_model_budget_expires(monkeypatch):
    from api.v2 import copilot
    monkeypatch.setenv("REACHPOINT_AI", "on")
    monkeypatch.setattr(copilot, "within", lambda seconds, call, *args: None)
    monkeypatch.setattr(copilot, "rules_answer", lambda st, question: ("No families are waiting.", [], None))
    assert copilot.ask({}, "Where first?")["reader"] == "rules"


def test_plan_reader_falls_back_when_its_model_budget_expires(monkeypatch):
    from api.v2 import ai
    monkeypatch.setattr(ai, "within", lambda seconds, call, *args: None)
    plan = ai.read_plan("Rescue boat, 6 seats, D7, evacuation")
    assert plan["reader"] == "rules" and "D7" in plan["zones"]
