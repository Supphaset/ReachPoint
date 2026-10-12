"""Checks for the split panel and askTeams fixtures (C4 view, C7; build_split_fixtures.py)."""

import json
from pathlib import Path

from api.rules.allocation import solve_split

F = Path(__file__).resolve().parents[2] / "contract" / "fixtures"
panel = json.loads((F / "splitPanel.cp3.json").read_text())
ok = json.loads((F / "askTeams.ok.json").read_text())
stale = json.loads((F / "askTeams.stale.json").read_text())


def test_panel_shows_the_real_solver_answer():
    snap = json.loads((F / "allocationInput.cp3.json").read_text())
    assert panel["suggestion"] == json.loads(json.dumps(solve_split(snap))), "rebuild: api/scripts/build_split_fixtures.py"
    assert set(panel["needs"]) == {n["listingId"] for n in snap["needs"]}


def test_what_if_is_always_a_simulation():
    assert panel["whatIfLabel"] == "Simulation · nothing sent"
    for s in panel["scenarios"]:
        assert s["suggestion"]["simulation"] is True
        assert s["suggestion"]["suggestionId"] != panel["suggestion"]["suggestionId"]


def test_ask_goes_only_to_teams_with_new_work():
    accepted = {a["listingId"] for a in panel["suggestion"]["assignments"] if a["accepted"]}
    for ask in ok["response"]["asks"]:
        assert not accepted & set(ask["listingIds"]), ask
    assert ok["request"]["suggestionId"] == panel["suggestion"]["suggestionId"]


def test_stale_ask_returns_the_new_suggestion():
    r = stale["response"]
    assert r["code"] == "VERSION_CONFLICT" and r["message"] == "Needs or resources changed"
    assert r["detail"]["current"]["inputVersions"] != stale["request"]["inputVersions"]
