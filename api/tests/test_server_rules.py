"""Starter server rules (C6, C7, D42) on the in-memory store. Run: python -m pytest api/tests -q

The same results the browser's fixture-mode store gives (web/src/data/teamStore.ts), so the screens behave the
same in both modes; the friend's Firestore version must pass these too.
"""

from datetime import datetime, timezone

import pytest

from api.server.memory import Clock, MemoryStore, NotFound, Refused
from api.views.briefing import briefing_cases
from api.views.team import team_missions


@pytest.fixture
def m():
    return MemoryStore(clock=Clock(start=datetime(2026, 10, 11, 3, 20, tzinfo=timezone.utc)))


def view(m, team="T-S"):
    return team_missions(m.store, team, m.clock.iso())


def listing(m, lid):
    return next(r for r in view(m)["open"] if r["listingId"] == lid)


def claim(m, lid, rev=1, groups=None, team="T-S", sub=None):
    groups = groups or [g["groupId"] for g in listing(m, lid)["groups"]]
    return m.write(sub, lambda: m.claim(lid, team, groups, rev))


def code(fn):
    with pytest.raises(Refused) as e:
        fn()
    return e.value.code, e.value.message


def test_take_a_family_then_the_job_has_the_exact_point_and_notes(m):
    r = claim(m, "L-C01-EVAC", 2)
    v = view(m)
    assert v["team"]["resource"]["seatUnitsLeft"] == 9.5
    job = v["jobs"][0]
    assert job["allocationId"] == r["value"]["allocationId"] and job["state"] == "taken"
    assert job["pickup"]["precision"] == "building" and job["medical"]["consent"] == "given"
    assert all(g["state"] == "taken" and g["takenBy"] == "T-S" for g in listing(m, "L-C01-EVAC")["groups"])
    assert next(c for c in briefing_cases(m.store) if c["caseId"] == "C-01")["assistance"][0]["allocation"] == "taken"


def test_claim_refusals_match_the_screens(m):
    assert code(lambda: claim(m, "L-C04-EVAC")) == ("ALREADY_TAKEN", "Already taken by T-R")
    assert code(lambda: claim(m, "L-C01-EVAC", 1))[0] == "NEED_CHANGED"
    for lid in ("L-C02-EVAC", "L-C03-EVAC", "L-C06-EVAC"):
        claim(m, lid)
    assert code(lambda: claim(m, "L-C05-EVAC")) == ("NOT_ENOUGH_CAPACITY", "Needs 5 seats, you have 3")
    m.write(None, lambda: m.team_status("T-S", "busy", "Refuelling", "2026-10-11T04:30:00Z"))
    assert code(lambda: claim(m, "L-C01-EVAC", 2))[0] == "NOT_AVAILABLE"


def test_part_of_a_household_and_the_rest_stays_open(m):
    claim(m, "L-C06-EVAC", groups=["L-C06-EVAC-G1", "L-C06-EVAC-G2"])
    states = [g["state"] for g in listing(m, "L-C06-EVAC")["groups"]]
    assert states == ["taken", "taken", "open"]
    assert next(c for c in briefing_cases(m.store) if c["caseId"] == "C-06")["assistance"][0]["allocation"] == "open"


def test_same_submission_twice_changes_nothing(m):
    a = claim(m, "L-C02-EVAC", sub="SUB-1")
    b = claim(m, "L-C02-EVAC", sub="SUB-1")
    assert a == b and len(view(m)["jobs"]) == 1


def test_a_refused_write_leaves_everything_as_it_was(m):
    before = view(m)
    code(lambda: claim(m, "L-C05-EVAC", groups=["L-C05-EVAC-G1", "nope"]))
    assert view(m) == before


def test_window_progress_close_and_medical_notes_leave(m):
    aid = claim(m, "L-C05-EVAC")["value"]["allocationId"]
    m.write(None, lambda: m.set_window(aid, "2026-10-11T06:00:00Z", "2026-10-11T07:00:00Z"))
    m.write(None, lambda: m.progress(aid, "on_the_way"))
    assert view(m)["jobs"][0]["medical"] is not None
    m.write(None, lambda: m.close(aid, "done"))
    j = view(m)["jobs"][0]
    assert j["state"] == "closed" and j["medical"] is None and j["medicalRemovedAt"] == j["closedAt"]
    assert code(lambda: m.write(None, lambda: m.progress(aid, "on_scene")))[0] == "ALLOCATION_CLOSED"
    assert view(m)["team"]["resource"]["seatUnitsLeft"] == 7  # the trip used the seats


def test_hand_back_and_needs_more_help_reopen_with_a_reason(m):
    aid = claim(m, "L-C02-EVAC")["value"]["allocationId"]
    m.write(None, lambda: m.hand_back(aid, "Boat engine trouble"))
    l = listing(m, "L-C02-EVAC")
    assert all(g["state"] == "open" for g in l["groups"]) and "Back from T-S: Boat engine trouble" in l["reasons"]
    assert view(m)["team"]["resource"]["seatUnitsLeft"] == 12
    aid = claim(m, "L-C03-EVAC")["value"]["allocationId"]
    m.write(None, lambda: m.close(aid, "needs_more_help"))
    assert all(g["state"] == "open" for g in listing(m, "L-C03-EVAC")["groups"])


def test_urgent_flag_turns_red_everywhere(m):
    assert code(lambda: m.write(None, lambda: m.urgent_flag("L-C08-EVAC", " ", False)))[0] == "INVALID"
    m.write(None, lambda: m.urgent_flag("L-C08-EVAC", "Callback: water at the 2nd floor, 2 children", True))
    l = listing(m, "L-C08-EVAC")
    assert l["colour"] == "red" and l["needRevision"] == 2 and l["lastConfirmedAt"] == "2026-10-11T03:20:00Z"
    assert [r["caseId"] for r in view(m)["open"] if r["colour"] == "red"] == ["C-01", "C-08"]
    assert next(c for c in briefing_cases(m.store) if c["caseId"] == "C-08")["assistance"][0]["priority"] == "red"


def test_unknown_ids_are_not_found(m):
    with pytest.raises(NotFound):
        m.write(None, lambda: m.claim("L-NOPE", "T-S", ["x"], 1))
    with pytest.raises(NotFound):
        m.write(None, lambda: m.set_window("AL-NOPE", "a", "b"))


def test_status_clears_reason_on_available_and_reconfirm_shows(m):
    m.write(None, lambda: m.team_status("T-S", "busy", "Rest", "2026-10-11T05:00:00Z"))
    m.write(None, lambda: m.team_status("T-S", "available", "ignored", "ignored"))
    t = view(m)["team"]
    assert (t["status"], t["reason"], t["backAbout"]) == ("available", None, None)
    m.write(None, lambda: m.reconfirm("L-C03-EVAC", "T-S"))
    assert listing(m, "L-C03-EVAC")["reconfirmRequestedAt"] == "2026-10-11T03:20:00Z"


def test_ask_teams(m):
    ok = m.ask_teams("SUG-67bc730722", ["T-K"])
    assert ok["ok"]
    fresh = m.ask_teams("SG-other", ["T-K", "T-R"])
    assert [a["teamId"] for a in fresh["asks"]] == ["T-K", "T-R"]


def test_fixtures_are_untouched_by_the_server_store(m):
    # The server works on a copy: the seed the fixtures come from stays as it was.
    claim(m, "L-C01-EVAC", 2)
    from api.views import store as S
    assert not S.load().seed.get("allocations")
