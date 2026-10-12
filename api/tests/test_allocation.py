"""Tests for the split solver (C4) and the solver half of T15. Run: python -m pytest api/tests -q"""

import copy
import json
from pathlib import Path

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from api.rules.allocation import InvalidSnapshot, compare_scenarios, solve_split
from api.rules.tiers import TierInput, tier

SNAP = json.loads((Path(__file__).resolve().parents[2] / "contract/fixtures/allocationInput.cp3.json").read_text())
KINDS = ("adults", "children", "infants", "stretcher")
HALF = {"adults": 2, "children": 1, "infants": 0, "stretcher": 6}


def seats(part):
    return sum(part[k] * HALF[k] for k in KINDS) / 2


def got(s, listing_id):
    return {a["resourceId"]: a["units"] for a in s["assignments"] if a["listingId"] == listing_id}


# --- the demo snapshot (same answers as the notebook) ---

def test_base_split():
    s = solve_split(SNAP)
    assert sum(a["seatUnits"] for a in s["assignments"] if a["resourceId"] == "S1") <= 12
    assert sum(a["units"] for a in s["assignments"] if a["assistanceType"] == "evacuation_transport") == 16
    assert got(s, "L-C01-MED") == {"M1": 1}
    assert got(s, "L-C01-EVAC") == {"S1": 3}
    assert next(a for a in s["assignments"] if a["listingId"] == "L-C01-EVAC")["accepted"]
    assert {u["listingId"]: u["reason"] for u in s["unassigned"]}["L-C05-SUP"] == "no_capable_team"
    assert s["solver"]["optimal"] and not s["simulation"]


def test_every_split_is_safe_and_flagged():
    s = solve_split(SNAP)
    for row in s["assignments"] + s["unassigned"]:
        if row["part"]:
            p = row["part"]
            assert p["adults"] >= 1 or not (p["children"] or p["infants"] or p["stretcher"]), row
        assert row["needsCoordinatorApproval"] == row["split"]
    assert any(r["split"] for r in s["assignments"])  # the demo has one: C-02's mother and children go


def test_deterministic_and_identified():
    a, b = solve_split(SNAP), solve_split(SNAP)
    assert a == b
    other = copy.deepcopy(SNAP)
    other["inputVersions"]["listings"] += 1
    assert solve_split(other)["suggestionId"] != a["suggestionId"]


def test_s1_breaks_down():
    s = solve_split(SNAP, drop={"S1"})
    evac = [u for u in s["unassigned"] if u["assistanceType"] == "evacuation_transport"]
    assert sum(u["units"] for u in evac) == 24 and all(u["reason"] == "no_capable_team" for u in evac)
    assert next(u for u in evac if u["listingId"] == "L-C01-EVAC")["returnedFrom"] == "S1"
    assert got(s, "L-C01-MED") == {"M1": 1} and got(s, "L-PA-SUP") == {"R1": 30}
    assert s["simulation"]


def test_what_if_second_boat_is_labelled_a_simulation():
    s2 = {"resourceId": "S2", "teamId": "T-X", "kind": "boat", "capabilities": ["evacuation_transport"], "areas": ["P-B"],
          "capacity": {"evacuation_transport": 12}}
    c = compare_scenarios(SNAP, extra=[s2])
    assert c["diff"]["peopleCoveredDelta"] == 8
    assert "Simulation" in c["label"]
    assert next(r for r in c["whatIf"]["resources"] if r["resourceId"] == "S2")["simulated"]
    assert not c["diff"]["lessCovered"]


def test_explanations_are_facts_for_every_need():
    s = solve_split(SNAP)
    ex = {e["listingId"]: e["facts"] for e in s["explanations"]}
    assert set(ex) == {n["listingId"] for n in SNAP["needs"]}
    assert ex["L-C01-MED"][0].startswith("Tier 1a")
    assert any("Transport linked to urgent medical case C-01" in f for f in ex["L-C01-EVAC"])
    assert any("not covered: capable teams are full today" in f for f in ex["L-C12-MED"])


def test_bad_snapshots_are_refused():
    with pytest.raises(InvalidSnapshot):
        solve_split(SNAP, weights={"w_evac": 0.0})
    over = copy.deepcopy(SNAP)
    next(r for r in over["resources"] if r["resourceId"] == "S1")["capacity"]["evacuation_transport"] = 2
    with pytest.raises(InvalidSnapshot):  # the accepted C-01 family needs 2.5 seats
        solve_split(over)
    bad = copy.deepcopy(SNAP)
    bad["needs"][1]["party"]["adults"] += 1
    with pytest.raises(InvalidSnapshot):
        solve_split(bad)


def test_children_without_an_adult_move_whole():
    snap = copy.deepcopy(SNAP)
    snap["needs"].append({**copy.deepcopy(SNAP["needs"][2]), "listingId": "L-C20-EVAC", "caseId": "C-20", "units": 3,
                          "party": {"adults": 0, "children": 3, "infants": 0, "stretcher": 0},
                          "urgentFlag": {"reason": "Children alone, found by T-R"}})
    s = solve_split(snap)
    assert got(s, "L-C20-EVAC") == {"S1": 3}  # tier 1b, whole group
    assert not next(a for a in s["assignments"] if a["listingId"] == "L-C20-EVAC")["split"]


# --- property tests on random snapshots (T15, solver half) ---

@st.composite
def snapshots(draw):
    needs = []
    for i in range(draw(st.integers(1, 6))):
        typ = draw(st.sampled_from(["evacuation_transport", "medical", "supplies"]))
        party = None
        if typ == "evacuation_transport":
            party = {"adults": draw(st.integers(0, 3)), "children": draw(st.integers(0, 3)),
                     "infants": draw(st.integers(0, 1)), "stretcher": draw(st.integers(0, 1))}
            if sum(party.values()) == 0:
                party["children"] = 1  # also tests groups with no adult
        units = sum(party.values()) if party else draw(st.integers(1, 10))
        needs.append({
            "listingId": f"L-{i}", "caseId": f"C-{i}", "areaId": draw(st.sampled_from(["P-A", "P-B"])),
            "assistanceType": typ, "review": "validated",
            "waitingSince": f"2026-10-11T0{draw(st.integers(0, 2))}:{draw(st.integers(10, 59))}:00Z",
            "units": units, "unit": "packs" if typ == "supplies" else "people", "party": party,
            "pickup": {"at": None},
            "qualifiedAssessment": {"urgentMedical": typ == "medical" and draw(st.booleans())},
            "urgentFlag": {"reason": "stated reason"} if draw(st.booleans()) and draw(st.booleans()) else None,
        })
    resources = []
    for j in range(draw(st.integers(1, 3))):
        caps = draw(st.lists(st.sampled_from(["evacuation_transport", "medical", "supplies"]), min_size=1, max_size=2, unique=True))
        resources.append({"resourceId": f"R{j}", "teamId": f"T-{j}", "kind": "test",
                          "capabilities": caps, "areas": draw(st.lists(st.sampled_from(["P-A", "P-B"]), min_size=1, max_size=2, unique=True)),
                          "capacity": {c: draw(st.integers(0, 12)) for c in caps}, "available": True})
    return {"snapshotAt": "2026-10-11T03:25:00Z", "inputVersions": {"listings": 1},
            "weights": {"w_evac": 1.0, "w_supply": 1.0},
            "seatUnits": {"adults": 1.0, "children": 0.5, "infants": 0.0, "stretcher": 3.0},
            "needs": needs, "resources": resources, "accepted": []}


SETTINGS = settings(max_examples=60, deadline=None, suppress_health_check=[HealthCheck.too_slow])


@SETTINGS
@given(snapshots())
def test_solver_uses_the_same_tiers_as_the_lists(snap):
    s = solve_split(snap)
    want = {n["listingId"]: tier(TierInput.from_listing(n)).value for n in snap["needs"]}
    for row in s["assignments"] + s["unassigned"]:
        assert row["tier"] == want[row["listingId"]]


@SETTINGS
@given(snapshots())
def test_tier_1_coverage_is_never_traded_away(snap):
    # Covering tier 1 alone can't do better than the full problem: tier 2 never displaces a coverable tier-1 need.
    full = solve_split(snap)
    only1 = copy.deepcopy(snap)
    only1["needs"] = [n for n in snap["needs"] if tier(TierInput.from_listing(n)).value != "2"]
    if not only1["needs"]:
        return
    alone = solve_split(only1)
    for lvl in ("tier1aPeopleCovered", "tier1bPeopleCovered"):
        assert full["solver"]["levels"][lvl] == alone["solver"]["levels"][lvl]


@SETTINGS
@given(snapshots())
def test_capacity_parts_and_totals_hold(snap):
    s = solve_split(snap)
    for r in s["resources"]:
        for typ, cap in r["capacity"].items():
            assert r["used"][typ] <= cap + 1e-9
    by_need = {}
    for a in s["assignments"]:
        by_need[a["listingId"]] = by_need.get(a["listingId"], 0) + a["units"]
        n = next(x for x in snap["needs"] if x["listingId"] == a["listingId"])
        if a["part"] and n["party"]["adults"]:
            assert a["part"]["adults"] >= 1 or not (a["part"]["children"] or a["part"]["infants"] or a["part"]["stretcher"])
        if a["part"] and not n["party"]["adults"]:
            assert a["units"] == n["units"]  # no adult: whole group only
    for n in snap["needs"]:
        left = sum(u["units"] for u in s["unassigned"] if u["listingId"] == n["listingId"])
        assert by_need.get(n["listingId"], 0) + left == n["units"]


def test_suggestion_fixture_matches_the_solver():
    import importlib.util
    spec = importlib.util.spec_from_file_location("bsf", Path(__file__).resolve().parents[1] / "scripts/build_suggestion_fixture.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    stored = json.loads((Path(__file__).resolve().parents[2] / "contract/fixtures/allocationSuggestion.cp3.json").read_text())
    assert json.loads(json.dumps(mod.build())) == stored, "rebuild with api/scripts/build_suggestion_fixture.py"
