"""Views built from the demo records (C2, C5, C12, C18, C19). Run: python -m pytest api/tests -q

The fixture files the screens read are exactly what `api/views` builds from `contract/seed/demo.*.json`, so the
friend's API, calling the same functions on Firestore documents of the same shape, serves the same views.
"""

import copy
import importlib.util
import json
from pathlib import Path

import pytest

from api.views import store as S
from api.views.briefing import area_briefing, briefing_cases, nice, span
from api.views.team import team_missions

ROOT = Path(__file__).resolve().parents[2]
FX = ROOT / "contract" / "fixtures"
ST = S.load()


def _script(path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def fixture(name):
    return json.loads((FX / name).read_text())


@pytest.mark.parametrize("area", ["P-A", "P-B", "P-C"])
def test_briefing_fixture_is_the_view(area):
    assert json.loads(json.dumps(area_briefing(ST, area, "2026-10-11T03:15:00Z"))) == fixture(f"areaBriefing.{area}.json")


def test_team_fixtures_are_the_view():
    assert json.loads(json.dumps(team_missions(ST, "T-S", "2026-10-11T03:16:00Z", "2026-10-11T03:15:00Z"))) == fixture("teamMissions.T-S.json")
    mod = _script(ROOT / "api/scripts/build_team_fixtures.py")
    st = S.load()
    assert json.loads(json.dumps(mod.pickups(st))) == fixture("pickups.synthetic.json")
    assert json.loads(json.dumps(mod.medical_notes(st))) == fixture("medicalNotes.synthetic.json")


def test_one_truth_per_family():
    # The map and the team list read the same records: what the briefing calls taken, the team list shows taken.
    taken = {(c["caseId"], a["type"]): a["teamId"] for c in briefing_cases(ST) for a in c["assistance"] if a["allocation"] == "taken"}
    for row in team_missions(ST, "T-S", "2026-10-11T03:16:00Z")["open"]:
        who = taken.get((row["caseId"], row["assistanceType"]))
        assert all((g["state"] == "taken") == bool(who) for g in row["groups"]), row["listingId"]
        assert all(g.get("takenBy") == who for g in row["groups"] if who)


def test_colours_come_from_the_tiers():
    # Flagging a need urgent in the records turns it RED everywhere, with no colour typed by hand.
    seed = copy.deepcopy(ST.seed)
    need = next(n for c in seed["cases"] if c["caseId"] == "C-08" for n in c["needs"])
    need["urgentFlag"] = {"reason": "Callback: water at the 2nd floor"}
    st = S.Store(seed, ST.catalogue, ST.exposure, ST.register)
    assert next(a for c in briefing_cases(st) if c["caseId"] == "C-08" for a in c["assistance"])["priority"] == "red"
    rows = team_missions(st, "T-S", "2026-10-11T03:16:00Z")["open"]
    assert [r["caseId"] for r in rows if r["colour"] == "red"] == ["C-01", "C-08"]


def test_area_facts_are_computed_from_the_cases():
    facts = {f["key"]: f["value"] for f in area_briefing(ST, "P-B", "2026-10-11T03:15:00Z")["facts"]}
    assert facts == {"reviewedDemand": 24, "conditionalCapacity": 12, "knownGap": 24, "medicalUnderReview": 1}


def test_seed_keeps_private_fields_out_of_shared_views():
    shared = json.dumps([area_briefing(ST, a, "2026-10-11T03:15:00Z") for a in ("P-A", "P-B", "P-C")]
                        + [team_missions(ST, "T-S", "2026-10-11T03:16:00Z")], ensure_ascii=False)
    for _, n in ST.needs():
        if n.get("exactPickup"):
            assert str(n["exactPickup"]["at"][0]) not in shared
        for note in (n.get("medicalNotes") or {}).get("functional", []):
            assert note not in shared


def test_ranges_match_the_geography_build():
    geo = _script(ROOT / "data/scripts/build_geography.py")
    for x in (0, 5, 999, 1000, 1234, 98765, 406374):
        assert nice(x, True) == geo.nice(x, True) and nice(x, False) == geo.nice(x, False)
    assert span(10, 2000) == geo.span(10, 2000)


def test_reported_flooding_counts_match_the_map():
    shapely = pytest.importorskip("shapely.geometry")
    pkg = ROOT / "data" / "hy-2025-11"
    zones = {f["properties"]["id"]: shapely.shape(f["geometry"]) for f in json.loads((pkg / "zones.geojson").read_text())["features"]}
    pts = [shapely.Point(f["geometry"]["coordinates"]) for f in json.loads((pkg / "reported-flooding.geojson").read_text())["features"]]
    assert ST.seed["reportedFloodingByZone"] == {z: sum(g.contains(p) for p in pts) for z, g in zones.items()}
