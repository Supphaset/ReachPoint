"""Checks for the team view and claim fixtures (C5, C6; build_team_fixtures.py)."""

import json
from pathlib import Path

from api.rules.tiers import TierInput, colour, sort_key

FIXTURES = Path(__file__).resolve().parents[2] / "contract" / "fixtures"
view = json.loads((FIXTURES / "teamMissions.T-S.json").read_text())
snap = {n["listingId"]: n for n in json.loads((FIXTURES / "allocationInput.cp3.json").read_text())["needs"]}


def test_open_list_is_in_the_shared_order():
    team_at = tuple(view["team"]["location"]["at"])
    items = [TierInput.from_listing(snap[r["listingId"]]) for r in view["open"]]
    keys = [sort_key(i, team_at) for i in items]
    assert keys == sorted(keys)
    assert [r["colour"] for r in view["open"]] == [colour(i).value for i in items]
    assert view["open"][0]["colour"] == "red"


def test_no_exact_location_before_taking():
    # D25: the shared list carries landmark-level places only; exact points come with the team's own job.
    text = json.dumps(view["open"])
    for lid, p in json.loads((FIXTURES / "pickups.synthetic.json").read_text())["pickups"].items():
        assert str(p["at"][0]) not in text, lid
    for r in view["open"]:
        assert not {"at", "exact", "address", "phone", "name"} & set(r)


def test_groups_add_up_and_carry_seats():
    seat = view["seatUnits"]
    for r in view["open"]:
        assert sum(g["people"] for g in r["groups"]) == r["people"] == snap[r["listingId"]]["units"]
        for g in r["groups"]:
            assert g["seatUnits"] == sum(g["party"][k] * seat[k] for k in ("adults", "children", "infants", "stretcher"))


def test_every_claim_result_has_a_fixture():
    codes = {json.loads(p.read_text())["response"].get("code", "OK") for p in FIXTURES.glob("claim.*.json")}
    assert codes == {"OK", "ALREADY_TAKEN", "NOT_ENOUGH_CAPACITY", "NEED_CHANGED", "ALLOCATION_CLOSED", "VERSION_CONFLICT"}
    accepted = json.loads((FIXTURES / "claim.accepted.json").read_text())["response"]["allocation"]
    assert accepted["window"] is None  # no window until the team sets one
    assert accepted["pickup"]["precision"] in {"rooftop", "building", "landmark"}
