"""Water rising: who to re-confirm first (D42). Run: python -m pytest api/tests -q"""

import dataclasses
import importlib.util
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from api.rules.rising import WaitingFamily, gauge_status, rank_families, rising_water, signals

ROOT = Path(__file__).resolve().parents[2]
GAUGE = json.loads((ROOT / "data/hy-2025-11/gauge-x44.json").read_text())
T = lambda h, m=0: datetime(2026, 10, 11, h - 7, m, tzinfo=timezone.utc)  # Bangkok clock on the demo day


def _mod():
    spec = importlib.util.spec_from_file_location("brw", ROOT / "api/scripts/build_rising_fixtures.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


BRW = _mod()


def fam(lid, *, colour="yellow", seg="S-1", water=None, stale=False, children=0, cant_walk=False, confirmed_h=1.0, open_groups=1):
    return WaitingFamily(lid, "C-" + lid, colour, seg, seg, "2 people: 2 adults", children, cant_walk, water,
                         None if water is None else f"Water (about {water} m) at the landmark",
                         None if water is None else T(9), stale, T(12) - timedelta(hours=confirmed_h), open_groups)


GROUND = {"S-1": 5.0, "S-2": 10.0, "S-3": 15.0}
FORECAST = {"forecasts": [{"riseM": [1.25, 1.45], "issuedAt": "x", "line": "Forecast (DDPM, 10:13): rise"}], "reading": None, "line": ""}


# --- gauge ---

def test_gauge_reading_is_the_newest_at_or_before_the_clock():
    g = gauge_status(GAUGE, T(10, 16))
    assert g["reading"]["levelM"] == 7.9 and g["reading"]["overBankM"] == 0.5 and g["reading"]["trend"] == "rising"
    assert g["line"] == "River X.44 at 06:00: 7.90 m, 0.50 m over the bank, +0.14 m in 24 h (reading, RID)"
    assert gauge_status(GAUGE, T(10) - timedelta(hours=4, minutes=1))["reading"]["levelM"] == 7.76  # the 06:00 reading isn't visible before 06:00


def test_forecast_is_labelled_and_only_valid_in_its_window():
    assert gauge_status(GAUGE, T(10, 0))["forecasts"] == []  # issued 10:13
    f = gauge_status(GAUGE, T(10, 16))["forecasts"]
    assert len(f) == 1 and f[0]["line"].startswith("Forecast (DDPM (ปภ.) evacuation SMS, 10:13)")
    assert gauge_status(GAUGE, T(10, 16) + timedelta(days=1))["forecasts"] == []  # expired 07:00 next day


def test_gauge_never_says_street_depth():
    for h in range(10, 18):
        g = gauge_status(GAUGE, T(h))
        assert "deep" not in g["line"] and "street" not in g["line"]
    assert "not water depth" in GAUGE["label"]


# --- signals and the prompt ---

def test_no_signal_no_prompt():
    assert rising_water("P-T", T(12), [fam("1", water=2.0)], GROUND)["prompt"] is None
    quiet = {"forecasts": [], "reading": {"overBankM": 0.5, "change24hM": 0.14, "at": "x"}, "line": "slow"}
    assert signals(quiet, None) == []  # over the bank but rising slowly: context, not a prompt


def test_red_and_fully_taken_families_are_never_listed():
    fs = [fam("1", colour="red", water=3.0), fam("2", open_groups=0, water=3.0), fam("3")]
    out = rising_water("P-T", T(12), fs, GROUND, gauge=FORECAST)
    assert [r["listingId"] for r in out["prompt"]["reconfirm"]] == ["3"]


def test_ranking_and_reasons():
    fs = [fam("a", seg="S-3", confirmed_h=1), fam("b", seg="S-1", water=1.3, children=2, confirmed_h=7),
          fam("c", seg="S-2", water=2.0, stale=True, cant_walk=True, confirmed_h=4)]
    rows = rank_families(fs, T(12), GROUND, "P-T")
    assert [r["listingId"] for r in rows] == ["b", "c", "a"]
    assert rows[0]["reasons"] == ["Water (about 1.3 m) at 09:00", "lower ground than 67% of P-T", "2 children", "last confirmed 7h 00m ago"]
    assert "(report older than 6 h)" in rows[1]["reasons"][0]
    assert all(r["actions"] == ["call_back", "flag_urgent", "dismiss"] for r in rows)


def test_naive_time_refused():
    with pytest.raises(ValueError):
        rising_water("P-T", datetime(2026, 10, 11), [], GROUND)


FAMS = st.lists(st.builds(
    lambda i, colour, seg, water, stale, kids, cw, h, og: fam(str(i), colour=colour, seg=seg, water=water, stale=stale,
                                                             children=kids, cant_walk=cw, confirmed_h=h, open_groups=og),
    st.integers(0, 50), st.sampled_from(["red", "yellow", "green"]), st.sampled_from(list(GROUND)),
    st.one_of(st.none(), st.sampled_from([0.5, 1.0, 1.3, 2.0, 3.0])), st.booleans(), st.integers(0, 3), st.booleans(),
    st.floats(0, 12), st.integers(0, 2)), max_size=8, unique_by=lambda f: f.listing_id)


@settings(max_examples=150, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(FAMS)
def test_rising_water_never_changes_a_family_and_more_risk_never_ranks_lower(fs):
    before = [dataclasses.replace(f) for f in fs]
    rows = rank_families(fs, T(12), GROUND, "P-T")
    assert fs == before  # pure: nothing about a family changes
    assert all(r["listingId"] not in {f.listing_id for f in fs if f.colour == "red" or f.open_groups == 0} for r in rows)
    for f in fs:
        if f.colour == "red" or f.open_groups == 0 or f.cant_walk:
            continue
        worse = dataclasses.replace(f, cant_walk=True)
        old = next(r["points"] for r in rows if r["listingId"] == f.listing_id)
        new = next(r["points"] for r in rank_families([worse if x is f else x for x in fs], T(12), GROUND, "P-T")
                   if r["listingId"] == f.listing_id)
        assert new >= old


# --- the replay ---

def test_demo_day():
    snaps = {s["asOf"][11:16]: s for s in BRW.build()["snapshots"]}
    assert snaps["03:00"]["prompt"] is None  # 10:00: the reading only
    p = snaps["03:30"]["prompt"]  # 10:30: the DDPM forecast is out
    assert [s["kind"] for s in p["signals"]] == ["gauge_forecast"]
    assert [r["caseId"] for r in p["reconfirm"]][:2] == ["C-08", "C-05"]
    assert "C-04" not in {r["caseId"] for s in snaps.values() if s["prompt"] for r in s["prompt"]["reconfirm"]}  # taken by T-R
    assert [s["kind"] for s in snaps["07:00"]["prompt"]["signals"]] == ["gauge_forecast", "heavy_rain"]  # 14:00
    assert len({s["prompt"]["promptId"] for s in snaps.values() if s["prompt"]}) == 1  # one prompt all day


def test_fixture_matches_the_rule():
    stored = json.loads((ROOT / "contract/fixtures/risingWater.P-B.json").read_text())
    assert json.loads(json.dumps(BRW.build())) == stored, "rebuild with api/scripts/build_rising_fixtures.py"


def test_gauge_file():
    st_ = GAUGE["station"]
    assert (st_["id"], st_["bankM"], st_["warningM"]) == ("X.44", 7.4, 7.15)
    assert max(r["levelM"] for r in GAUGE["readings"]) == 9.97
    assert all(r["source"] for r in GAUGE["readings"]) and all(f["issuer"] for f in GAUGE["forecasts"])


def test_how_much_it_may_rise():
    fs = [fam("b", water=1.3), fam("d")]
    out = rising_water("P-T", T(12), fs, GROUND, gauge=FORECAST)
    rows = {r["listingId"]: r for r in out["prompt"]["reconfirm"]}
    assert rows["b"]["ifItRises"] == {"text": "If the water here rises like the canal: about 2.5–2.8 m, over head height (estimate)",
                                      "rangeM": [2.5, 2.8], "mayBeOverHead": True}
    assert rows["d"]["ifItRises"]["text"] == "No depth reported here: ask how deep the water is now"
    assert out["prompt"]["rise"]["text"] == "Forecast rise at the canal: 1.25–1.45 m"
    # Rain alone gives no rise estimate: rain is never turned into depth.
    rain_only = rising_water("P-T", T(12), fs, GROUND, rain={"prompt": {"promptId": "R"}, "line": "heavy"})
    assert rain_only["prompt"]["rise"] is None and all(r["ifItRises"] is None for r in rain_only["prompt"]["reconfirm"])


def test_the_forecast_was_close():
    # DDPM said +1.25–1.45 m by about 06:00; the 06:00 reading next day was +1.49 m (9.39 vs 7.90).
    r = {x["at"][:16]: x["levelM"] for x in GAUGE["readings"]}
    assert round(r["2025-11-25T06:00"] - r["2025-11-24T06:00"], 2) == 1.49
