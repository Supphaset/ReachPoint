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


def test_urgency_details_are_operational_only():
    # Teams see why a case is urgent and what to bring; never transcripts or medical narrative (pack §4.1).
    snap_text = json.dumps(json.loads((FIXTURES / "allocationInput.cp3.json").read_text()))
    for r in view["open"]:
        u = r["urgency"]
        assert u["title"] == {"red": "Why this is an emergency", "yellow": "Why it's urgent", "green": "Why it can wait"}[r["colour"]]
        assert u["summary"] and u["facts"]
        for f in u["facts"]:
            assert f["basis"] in {"qualified review", "coordinator", "reviewed call", "callers", "none"}, f
        if any(f["kind"] in ("medical", "medical_category") for f in u["facts"]):
            assert u["withheld"] == "Medical details come with the job, for the team that takes it"
        text = json.dumps(u, ensure_ascii=False).lower()
        for word in ("transcript", "diagnos", "oxygen", "asthma", "copd", "inhaler", "caller-anon", "phone"):
            assert word not in text, (r["listingId"], word)
    c01 = view["open"][0]["urgency"]
    assert "Boat needed (water 1.2 m or more)" in c01["kit"]
    assert any(f["kind"] == "medical" and "asked separately" in f["text"] for f in c01["facts"])


def test_kit_follows_depth_and_people():
    by = {r["caseId"]: r["urgency"] for r in view["open"]}
    assert by["C-06"]["kit"][0].startswith("Wading may be possible")  # knee deep
    assert "Stretcher, and at least 2 people to carry" in by["C-05"]["kit"]
    assert by["C-05"]["summary"] == "Can't walk: must be carried"


def test_medical_notes_only_come_with_the_job():
    # D38: the shared list shows a category; the condition and functional notes arrive with the claim.
    notes = json.loads((FIXTURES / "medicalNotes.synthetic.json").read_text())["notes"]
    text = json.dumps(view, ensure_ascii=False)
    for lid, n in notes.items():
        assert n["condition"] not in text and not any(f in text for f in n["functional"]), lid
        assert n["consent"] in {"given", "cannot_consent"} and n["basis"]
    c05 = next(r for r in view["open"] if r["caseId"] == "C-05")
    assert any("Medical need: affects how to move them" in f["text"] for f in c05["urgency"]["facts"])
    accepted = json.loads((FIXTURES / "claim.accepted.json").read_text())["response"]["allocation"]
    assert accepted["medical"]["condition"] and accepted["destination"]["id"] == "H1"


def test_every_listing_has_a_destination():
    for r in view["open"]:
        assert r["destination"]["id"] in {"D1", "H1"} and r["destination"]["reason"]
    assert {r["caseId"] for r in view["open"] if r["destination"]["id"] == "H1"} == {"C-01", "C-05"}
