"""CP3 S1 failure, including the pack's negative controls. All records are synthetic; no AI calls."""

import copy
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

import api.main as main
from api.server.memory import Clock, MemoryStore, Refused
from api.views.briefing import area_briefing
from api.views.resident import resident_status
from api.views.team import team_missions

NOW = "2026-10-11T03:32:00Z"
UPDATE = "2026-10-11T04:00:00Z"


@pytest.fixture
def m():
    m = MemoryStore(clock=Clock(start=datetime(2026, 10, 11, 3, 32, tzinfo=timezone.utc)))
    # PL-A and M-M are in the scene, not in the starter seed. Keep them separate from transport.
    m.store.seed["plans"] = [{"planId": "PL-A", "areaId": "P-A", "state": "draft", "packs": 30}]
    m.store.seed["missions"] = [{"missionId": "M-M", "state": "offered", "type": "medical"}]
    m.store.seed["statusTokens"] = {"synthetic-c01": {"reportId": "CALL-01", "caseId": "C-01"}}
    for lid, rev, gids in (("L-C01-EVAC", 2, ["L-C01-EVAC-G1"]),
                          ("L-C06-EVAC", 1, ["L-C06-EVAC-G1", "L-C06-EVAC-G2"]),
                          ("L-C02-EVAC", 1, ["L-C02-EVAC-G1"])):
        aid = m.write(None, lambda: m.claim(lid, "T-S", gids, rev))["value"]["allocationId"]
        m.write(None, lambda: m.set_window(aid, "2026-10-11T06:00:00Z", "2026-10-11T07:00:00Z"))
    # Completed groups must stay completed and cannot be taken twice.
    completed = m.store.seed["allocations"][-1]
    m.write(None, lambda: m.close(completed["allocationId"], "done"))
    # Same case, and even the same resource ID: medical is still an independent mission.
    m.store.seed["allocations"].append({"allocationId": "M-M", "listingId": "L-C01-MED", "teamId": "T-M",
                                        "resourceId": "S1", "groupIds": [], "seatUnits": 0,
                                        "state": "taken", "window": None, "acceptedAt": NOW})
    return m


def fail(m, sub="S1-REVIEW"):
    return m.write(sub, lambda: m.resource_unavailable("S1", "Boat engine trouble", UPDATE))


def test_hold_owner_history_and_brief(m):
    _, need = m._need("L-C01-EVAC")
    need.setdefault("reasons", []).append("Back from T-R: earlier access problem")
    before = copy.deepcopy(m.store.seed["allocations"])
    result = fail(m)["value"]
    assert len(result["heldAllocationIds"]) == 2
    assert len(m.store.seed["allocations"]) == len(before)
    for a in m.store.seed["allocations"][1:3]:
        assert a["state"] == "held" and a["owner"] == "coordinator"
        assert a["nextStatusUpdate"] == {"at": UPDATE, "by": "coordinator"}
        assert a["briefRevision"] == 2 and a["briefAcknowledged"] is False
    h = m.store.seed["history"][-1]
    assert h["by"] == "coordinator" and h["before"]["allocations"] == before[1:3]
    assert h["after"]["allocations"] == m.store.seed["allocations"][1:3]
    assert "Back from T-R: earlier access problem" in need["reasons"]


def test_unfinished_groups_relist_in_existing_priority_order(m):
    order = [r["listingId"] for r in team_missions(m.store, "T-R", NOW)["open"]]
    fail(m)
    v = team_missions(m.store, "T-R", NOW)
    assert [r["listingId"] for r in v["open"]] == order
    rows = {r["listingId"]: r for r in v["open"]}
    assert all(g["state"] == "open" for g in rows["L-C01-EVAC"]["groups"])
    assert all(g["state"] == "open" for g in rows["L-C06-EVAC"]["groups"])
    assert rows["L-C02-EVAC"]["groups"][0]["state"] == "taken"
    available = [r for r in v["open"] if any(g["state"] == "open" for g in r["groups"])]
    assert available[0]["listingId"] == "L-C01-EVAC" and available[0]["colour"] == "red"
    assert "S1 unavailable" in " ".join(rows["L-C06-EVAC"]["reasons"])


def test_withdrawn_window_is_retained_but_not_shown_as_current(m):
    fail(m)
    a = m.store.seed["allocations"][1]
    assert a["window"]["state"] == "withdrawn" and a["window"]["start"] == "2026-10-11T06:00:00Z"
    j = team_missions(m.store, "T-S", NOW)["jobs"][0]
    assert j["window"] is None and j["withdrawnWindow"] == a["window"]
    line = resident_status(m.store, "synthetic-c01", NOW)["lines"][0]
    assert line["state"] == "held"
    assert line["text"] == ("Transport: on hold; new time not known; earlier 13:00–14:00 estimate withdrawn. "
                            "Next update 11:00 from the coordinator desk (status update, not arrival).")
    assert "expects to reach" not in line["text"]


@pytest.mark.parametrize("state", ["taken", "on_the_way", "on_scene"])
def test_each_unfinished_state_is_held(m, state):
    m.store.seed["allocations"][1]["state"] = state
    fail(m)
    assert m.store.seed["allocations"][1]["state"] == "held"


def test_failure_without_an_old_window_never_invents_one(m):
    m.store.seed["allocations"][1]["window"] = None
    fail(m)
    line = resident_status(m.store, "synthetic-c01", NOW)["lines"][0]
    assert "new time not known" in line["text"] and "arrival time not confirmed" in line["text"]
    assert "estimate withdrawn" not in line["text"]


def test_completed_job_and_its_window_are_kept(m):
    a = copy.deepcopy(m.store.seed["allocations"][3])
    fail(m)
    assert m.store.seed["allocations"][3] == a and a["state"] == "closed"


def test_capacity_drops_to_zero_without_changing_demand(m):
    before = {f["key"]: f for f in area_briefing(m.store, "P-B", NOW)["facts"]}
    assert before["conditionalCapacity"]["value"] == 12
    fail(m)
    after = {f["key"]: f for f in area_briefing(m.store, "P-B", NOW)["facts"]}
    assert after["conditionalCapacity"]["value"] == 0
    assert "S1 unavailable" in after["conditionalCapacity"]["basis"]
    assert after["knownGap"]["value"] == 24
    assert after["reviewedDemand"] == before["reviewedDemand"]


def test_negative_control_draft_is_unchanged(m):
    before = copy.deepcopy(m.store.seed["plans"])
    fail(m)
    assert m.store.seed["plans"] == before == [{"planId": "PL-A", "areaId": "P-A", "state": "draft", "packs": 30}]


def test_negative_control_other_area_counts_and_jobs_are_unchanged(m):
    before = {area: area_briefing(m.store, area, NOW) for area in ("P-A", "P-C")}
    other_job = copy.deepcopy(m.store.seed["allocations"][0])
    other_team = copy.deepcopy(m.store.team("T-R"))
    fail(m)
    assert {area: area_briefing(m.store, area, NOW) for area in before} == before
    facts = {f["key"]: f["value"] for f in before["P-A"]["facts"]}
    assert facts["suppliesRemaining"] == 60 and facts["suppliesUnassigned"] == 30
    assert m.store.seed["allocations"][0] == other_job and m.store.team("T-R") == other_team


def test_negative_control_medical_missions_and_needs_are_unchanged(m):
    before = copy.deepcopy(m.store.seed["missions"])
    medical = copy.deepcopy(m.store.seed["allocations"][-1])
    needs = copy.deepcopy(m.store.needs("medical"))
    fail(m)
    assert m.store.seed["missions"] == before and before[0]["state"] == "offered"
    assert m.store.seed["allocations"][-1] == medical and medical["state"] == "taken"
    # The parent case's transport need changes, so compare only medical need records.
    assert [n for _, n in m.store.needs("medical")] == [n for _, n in needs]


def test_safe_retry_and_second_review_do_not_duplicate_history(m):
    first = fail(m)
    seed = copy.deepcopy(m.store.seed)
    assert fail(m) == first and m.store.seed == seed
    assert fail(m, "NEW-SUB")["value"]["alreadyUnavailable"]
    assert m.store.seed == seed


@pytest.mark.parametrize("action", ["window", "progress", "close", "hand-back"])
def test_held_job_cannot_resume_close_or_be_deleted(m, action):
    fail(m)
    aid = m.store.seed["allocations"][1]["allocationId"]
    f = {"window": lambda: m.set_window(aid, "2026-10-11T07:00:00Z", "2026-10-11T08:00:00Z"),
         "progress": lambda: m.progress(aid, "on_the_way"), "close": lambda: m.close(aid, "done"),
         "hand-back": lambda: m.hand_back(aid, "again")}[action]
    before = copy.deepcopy(m.store.seed)
    with pytest.raises(Refused, match="on hold"):
        m.write(None, f)
    assert m.store.seed == before


def test_unavailable_resource_cannot_take_another_job(m):
    fail(m)
    m.write(None, lambda: m.team_status("T-S", "available", None, None))
    with pytest.raises(Refused, match="resource is unavailable"):
        m.write(None, lambda: m.claim("L-C01-EVAC", "T-S", ["L-C01-EVAC-G1"], 2))
    assert team_missions(m.store, "T-S", NOW)["team"]["resource"]["seatUnitsLeft"] == 0


def test_replacement_claim_supersedes_the_held_status_without_inventing_a_time(m):
    fail(m)
    aid = m.write(None, lambda: m.claim("L-C01-EVAC", "T-R", ["L-C01-EVAC-G1"], 2))["value"]["allocationId"]
    line = resident_status(m.store, "synthetic-c01", NOW)["lines"][0]
    assert line["state"] == "taken" and "haven't set a time yet" in line["text"]
    m.write(None, lambda: m.set_window(aid, "2026-10-11T07:00:00Z", "2026-10-11T08:00:00Z"))
    assert "14:00–15:00" in resident_status(m.store, "synthetic-c01", NOW)["lines"][0]["text"]


@pytest.mark.parametrize("reason,update", [(" ", UPDATE), ("broken", "no-time"),
                                          ("broken", "2026-10-11T04:00:00"), ("broken", NOW)])
def test_invalid_review_changes_nothing(m, reason, update):
    before = copy.deepcopy(m.store.seed)
    with pytest.raises(Refused):
        m.write("BAD", lambda: m.resource_unavailable("S1", reason, update))
    assert m.store.seed == before and "BAD" not in m.done


def test_failure_mid_write_rolls_back_and_can_be_retried(m, monkeypatch):
    before = copy.deepcopy(m.store.seed)
    original = m._summarise
    monkeypatch.setattr(m, "_summarise", lambda _: (_ for _ in ()).throw(RuntimeError("synthetic failure")))
    with pytest.raises(RuntimeError):
        fail(m)
    assert m.store.seed == before and "S1-REVIEW" not in m.done
    monkeypatch.setattr(m, "_summarise", original)
    assert fail(m)["ok"]


def test_http_review_and_safe_retry(m, monkeypatch):
    monkeypatch.setattr(main, "memory", m)
    c = TestClient(main.app)
    body = {"submissionId": "HTTP-S1", "reason": "Boat engine trouble", "nextStatusUpdate": UPDATE}
    first = c.post("/api/resources/S1/unavailable", json=body)
    assert first.status_code == 200
    assert c.post("/api/resources/S1/unavailable", json=body).json() == first.json()
    assert c.get("/api/status/synthetic-c01").json()["lines"][0]["state"] == "held"
    assert c.post("/api/resources/UNKNOWN/unavailable", json={**body, "submissionId": "UNKNOWN"}).status_code == 404
    assert c.post("/api/resources/S1/unavailable", json={"reason": "Broken", "nextStatusUpdate": UPDATE}).status_code == 422
