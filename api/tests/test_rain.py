"""Rain context and the heavy-rain re-check prompt (D41). Run: python -m pytest api/tests -q"""

import importlib.util
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from api.rules.rain import HEAVY_3H_MM, STEP, class_24h, heavy_since, rain_status, series_from_file, total
from api.rules.tiers import SegmentInput, ZoneInput, zone_order

ROOT = Path(__file__).resolve().parents[2]
T0 = datetime(2026, 10, 11, 0, 0, tzinfo=timezone.utc)
RAIN = json.loads((ROOT / "data/hy-2025-11/rain-imerg.json").read_text())


def flat(mm, n=96, start=T0):
    return [(start + i * STEP, mm) for i in range(n)]


def zone(zid, *segs):
    return ZoneInput(zid, "P-T", tuple(segs))


def _bld():
    spec = importlib.util.spec_from_file_location("brf", ROOT / "api/scripts/build_rain_fixtures.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# --- totals ---

def test_totals_and_partial_half_hours():
    s = flat(2.0)
    assert total(s, T0 + timedelta(hours=3), 3).mm == 12.0
    assert total(s, T0 + timedelta(hours=3, minutes=15), 1).mm == 4.0  # two half-hours, cut in proportion
    assert total(s, T0 + timedelta(hours=3), 3).complete


def test_missing_is_unknown_never_zero():
    s = flat(None)
    t = total(s, T0 + timedelta(hours=3), 3)
    assert t.mm is None and t.text() == "no data"
    gappy = [(t_, None if i % 2 else 4.0) for i, (t_, _) in enumerate(flat(0))]
    g = total(gappy, T0 + timedelta(hours=3), 3)
    assert g.mm == 12.0 and not g.complete and g.text() == "at least 12 mm"
    before_data = total(flat(2.0), T0 + timedelta(hours=1), 3)  # window starts before the series
    assert not before_data.complete
    st_ = rain_status("P-T", flat(None), T0 + timedelta(hours=5), [], {})
    assert st_["line"] == "Rain data unavailable" and st_["prompt"] is None


def test_classes():
    assert [class_24h(x) for x in (None, 0, 5, 20, 50, 120)] == [None, "no rain", "light", "moderate", "heavy", "very heavy"]


# --- the prompt ---

def test_prompt_lists_segments_checked_before_the_rain_lowest_first():
    rain = flat(0.0, 12) + flat(7.0, 12, T0 + 12 * STEP)  # dry 00:00–06:00Z, then 14 mm/h
    as_of = T0 + timedelta(hours=9)
    zs = [zone("Z-1", SegmentInput("Z-1-L1", "checked", T0 + timedelta(hours=1)),
               SegmentInput("Z-1-L2", "partly_checked", T0 + timedelta(hours=2)),
               SegmentInput("Z-1-L3", "checked", T0 + timedelta(hours=8)),  # after the rain began: fine
               SegmentInput("Z-1-L4", "could_not_reach", T0 + timedelta(hours=1)),  # not a check
               SegmentInput("Z-1-L5"))]
    out = rain_status("P-T", rain, as_of, zs, {"Z-1-L1": 12.0, "Z-1-L2": 8.0, "Z-1-L3": 5.0, "Z-1-L4": 1.0, "Z-1-L5": 9.0})
    p = out["prompt"]
    assert p and p["state"] == "proposed"
    assert [r["segmentId"] for r in p["recheck"]] == ["Z-1-L2", "Z-1-L1"]
    assert p["recheck"][0]["reason"] == "Partly checked at 09:00, before the heavy rain · lower ground than 40% of P-T"
    assert "Heavy rain since" in p["title"] and "not water depth" in out["label"]


def test_prompt_id_is_stable_through_one_spell():
    rain = flat(0.0, 12) + flat(7.0, 12, T0 + 12 * STEP) + flat(0.0, 24, T0 + 24 * STEP)
    ids = {rain_status("P-T", rain, T0 + timedelta(hours=h, minutes=m), [], {})["prompt"]["promptId"]
           for h in (7, 8, 9, 10, 11) for m in (0, 10, 30) if rain_status("P-T", rain, T0 + timedelta(hours=h, minutes=m), [], {})["prompt"]}
    assert len(ids) == 1
    assert heavy_since(rain, T0 + timedelta(hours=4)) is None


def test_rain_never_changes_the_zone_order():
    zs = [zone("Z-1", SegmentInput("Z-1-L1", "checked", T0)), zone("Z-2")]
    before = zone_order(zs, [], T0 + timedelta(hours=9))
    rain_status("P-T", flat(20.0), T0 + timedelta(hours=9), zs, {})
    assert zone_order(zs, [], T0 + timedelta(hours=9)) == before


def test_naive_time_is_refused():
    with pytest.raises(ValueError):
        rain_status("P-T", flat(1.0), datetime(2026, 10, 11), [], {})


@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(st.lists(st.one_of(st.none(), st.floats(0, 40)), min_size=1, max_size=96), st.integers(0, 60 * 48))
def test_totals_never_invent_rain(values, minutes):
    s = [(T0 + i * STEP, v) for i, v in enumerate(values)]
    as_of = T0 + timedelta(minutes=minutes)
    t = total(s, as_of, 3)
    known = [v for v in values if v is not None]
    if t.mm is not None:
        assert 0 <= t.mm <= sum(known) + 0.05  # totals are rounded to 0.1 mm
    out = rain_status("P-T", s, as_of, [], {})
    if out["prompt"]:
        assert out["last3h"] >= HEAVY_3H_MM


# --- the replay ---

def test_demo_day():
    s = series_from_file(RAIN, "P-B")
    at = lambda h, m=0: rain_status("P-B", s, datetime(2026, 10, 11, h - 7, m, tzinfo=timezone.utc), [], {})
    assert at(10, 16)["prompt"] is None and at(13, 30)["prompt"] is None
    assert at(14)["prompt"]["title"] == "Heavy rain since 11:00: re-check segments checked before then"
    assert at(16, 30)["prompt"] is None
    assert at(10, 16)["class24h"] == "very heavy"


def test_fixture_matches_the_rule():
    stored = json.loads((ROOT / "contract/fixtures/rainStatus.hy-2025-11.json").read_text())
    assert json.loads(json.dumps(_bld().build())) == stored, "rebuild with api/scripts/build_rain_fixtures.py"


def test_rain_file_shape():
    assert set(RAIN["areas"]) == {"P-A", "P-B", "P-C"}
    for v in RAIN["areas"].values():
        assert len(v) == 576 and all(x is None or x >= 0 for _, x in v)
