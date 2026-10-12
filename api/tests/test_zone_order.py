"""Zone order and suggested checks (D17c, D18) and the C12 producer test. Run: python -m pytest api/tests -q"""

import dataclasses
import importlib.util
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from api.rules.tiers import (CaseInput, Pin, PriorityColour, SegmentInput, TierInput, ZoneInput, zone_order,
                             zone_sort_key)

ROOT = Path(__file__).resolve().parents[2]
AS_OF = datetime(2026, 10, 11, 3, 16, tzinfo=timezone.utc)
R, Y, G = PriorityColour.RED, PriorityColour.YELLOW, PriorityColour.GREEN


def _fixture_module():
    spec = importlib.util.spec_from_file_location("bzo", ROOT / "api/scripts/build_zone_order_fixture.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


BZO = _fixture_module()


def zone(zid, *, cases=(), segs=None, nyc=(1000, 2000), flooded=(0, 0), reports=0, water=0, register=None):
    segs = segs or (SegmentInput(f"{zid}-L1"),)
    return ZoneInput(zid, "P-T", tuple(segs), tuple(cases), nyc, flooded, reports, water, register)


def ids(out):
    return [z["zoneId"] for z in out["zones"]]


# --- the demo ---

def test_demo_order_and_b4_check():
    out = BZO.build()
    assert ids(out)[:5] == ["B-3", "B-5", "B-6", "B-1", "B-4"]
    assert [e["listingId"] for e in out["emergencies"]] == ["L-C01-EVAC", "L-C01-MED"]
    assert out["suggestedChecks"][0]["zoneId"] == "B-4"
    b4 = out["suggestedChecks"][0]["reasons"]
    assert b4 == ["~6,200–8,900 live in the flooded part (estimate)", "0 reviewed calls", "never checked",
                  "2 on the vulnerable register (not confirmed in need)"]


def test_demo_counts():
    rows = {z["zoneId"]: z for z in BZO.build()["zones"]}
    assert rows["B-3"]["waitingPeople"] == 6  # C-02 + C-03; C-01 is an emergency, not part of the zone
    assert rows["B-3"]["registerNotChecked"] == 1  # partly checked stays in
    assert rows["B-2"]["waitingPeople"] == 0 and rows["B-2"]["registerNotChecked"] == 0  # C-04 taken; VR-05 checked
    assert rows["B-6"]["lastCheckAt"] is None  # couldn't reach is not a check


def test_fixture_matches_the_rule():
    stored = json.loads((ROOT / "contract/fixtures/zoneOrder.hy-2025-11.json").read_text())
    assert json.loads(json.dumps(BZO.build())) == stored, "rebuild with api/scripts/build_zone_order_fixture.py"


def test_register_details_never_leave_the_register():
    text = json.dumps(BZO.build(), ensure_ascii=False)
    for e in json.loads((ROOT / "contract/fixtures/register.hy-2025-11.json").read_text())["entries"]:
        assert e["entryId"] not in text and e["detail"] not in text
        for need in e["needs"]:
            assert need not in text


# --- the rule ---

def test_called_beats_register_beats_estimate_beats_time():
    old = AS_OF - timedelta(hours=5)
    zs = [zone("Z-1", nyc=(9000, 9000)),
          zone("Z-2", register={"Z-2-L1": 1}, nyc=(10, 10)),
          zone("Z-3", cases=[CaseInput("C-1", "Z-3-L1", 1, (Y,))], nyc=(0, 0)),
          zone("Z-4", nyc=(9000, 9000), segs=[SegmentInput("Z-4-L1", "partly_checked", old)]),
          zone("Z-5", nyc=(9000, 9000), segs=[SegmentInput("Z-5-L1", "partly_checked", AS_OF)])]
    assert ids(zone_order(zs, [], AS_OF)) == ["Z-3", "Z-2", "Z-1", "Z-4", "Z-5"]


def test_natural_zone_ids():
    assert ids(zone_order([zone("B-10"), zone("B-2")], [], AS_OF)) == ["B-2", "B-10"]


def test_pins_go_first_with_reason_and_never_above_emergencies():
    zs = [zone("Z-1", cases=[CaseInput("C-1", None, 5, (Y,))]), zone("Z-2")]
    red = TierInput("L-1", "medical", "validated", AS_OF, qualified_urgent_medical=True)
    out = zone_order(zs, [red], AS_OF, pins=[Pin("Z-2", "3 calls dropped mid-sentence", "coordinator K")])
    assert ids(out) == ["Z-2", "Z-1"] and out["emergencies"][0]["listingId"] == "L-1"
    assert out["zones"][0]["reasons"][0] == "Pinned by coordinator K: 3 calls dropped mid-sentence"
    with pytest.raises(ValueError):
        Pin("Z-2", " ", "coordinator K")
    with pytest.raises(ValueError):
        zone_order(zs, [], AS_OF, pins=[Pin("Z-9", "why", "K")])


def test_only_red_listings_are_emergencies():
    yellow = TierInput("L-2", "evacuation_transport", "validated", AS_OF)
    with pytest.raises(ValueError):
        zone_order([zone("Z-1")], [yellow], AS_OF)


def test_suggested_check_conditions():
    base = dict(flooded=(800, 1200))
    assert zone_order([zone("Z-1", **base)], [], AS_OF)["suggestedChecks"][0]["reasons"] == [
        "~800–1,200 live in the flooded part (estimate)", "0 reviewed calls", "never checked"]
    no_flood = zone("Z-1", flooded=(50, 900))  # low end under 100, no reports: not enough evidence
    called = zone("Z-1", cases=[CaseInput("C-1", None, 1, ())], **base)  # any reviewed call, even one already served
    recent = zone("Z-1", segs=[SegmentInput("Z-1-L1", "checked", AS_OF - timedelta(hours=5, minutes=59))], **base)
    for z in (no_flood, called, recent):
        assert zone_order([z], [], AS_OF)["suggestedChecks"] == []
    stale = zone("Z-1", segs=[SegmentInput("Z-1-L1", "checked", AS_OF - timedelta(hours=6))], **base)
    assert "last checked 6h 00m ago" in zone_order([stale], [], AS_OF)["suggestedChecks"][0]["reasons"]
    blocked = zone("Z-1", segs=[SegmentInput("Z-1-L1", "could_not_reach", AS_OF)], **base)
    assert zone_order([blocked], [], AS_OF)["suggestedChecks"]  # couldn't reach never clears a zone
    report_only = zone("Z-1", reports=1, nyc=(300, 900))
    assert zone_order([report_only], [], AS_OF)["suggestedChecks"][0]["reasons"][:2] == [
        "1 cited flood report", "~300–900 live here (estimate)"]


def test_published_and_dismissed_get_no_new_check():
    z = zone("Z-1", flooded=(800, 1200))
    assert zone_order([z], [], AS_OF, published={"Z-1"})["suggestedChecks"] == []
    assert zone_order([z], [], AS_OF, dismissed={"Z-1"})["suggestedChecks"] == []
    assert ids(zone_order([z], [], AS_OF, dismissed={"Z-1"})) == ["Z-1"]  # still on the list


def test_bad_input_is_refused():
    with pytest.raises(ValueError):
        SegmentInput("S", "checked")  # a check needs its time
    with pytest.raises(ValueError):
        SegmentInput("S", "dry")
    with pytest.raises(ValueError):
        zone_order([zone("Z-1"), zone("Z-1")], [], AS_OF)
    with pytest.raises(ValueError):
        zone_order([zone("Z-1")], [], AS_OF.replace(tzinfo=None))


# --- property tests (C12) ---

COLOURS = st.sampled_from([R, Y, G])


@st.composite
def zones(draw):
    out = []
    for i in range(draw(st.integers(1, 7))):
        zid = f"Z-{i + 1}"
        segs = []
        for j in range(draw(st.integers(1, 3))):
            state = draw(st.sampled_from(["not_checked", "checked", "partly_checked", "could_not_reach"]))
            at = AS_OF - timedelta(minutes=draw(st.integers(0, 900))) if state in ("checked", "partly_checked") else None
            segs.append(SegmentInput(f"{zid}-L{j + 1}", state, at))
        cases = [CaseInput(f"C-{i}-{k}", segs[0].segment_id, draw(st.integers(1, 8)),
                           tuple(draw(st.lists(COLOURS, max_size=2))))
                 for k in range(draw(st.integers(0, 3)))]
        lo = draw(st.integers(0, 5000))
        flo = draw(st.integers(0, 3000))
        out.append(ZoneInput(zid, "P-T", tuple(segs), tuple(cases), (lo, lo + draw(st.integers(0, 3000))),
                             (flo, flo + draw(st.integers(0, 1000))), draw(st.integers(0, 2)), draw(st.integers(0, 2)),
                             {s.segment_id: draw(st.integers(0, 2)) for s in segs}))
    return out


SETTINGS = settings(max_examples=150, deadline=None, suppress_health_check=[HealthCheck.too_slow])


@SETTINGS
@given(zones())
def test_red_is_never_ranked_as_a_zone(zs):
    out = zone_order(zs, [], AS_OF)
    for z, row in ((z, next(r for r in out["zones"] if r["zoneId"] == z.zone_id)) for z in zs):
        assert row["waitingPeople"] == sum(c.people for c in z.cases if c.open_colours and R not in c.open_colours)
    # Turning any case RED takes its people out of the zone, never pushes the zone up.
    for z in zs:
        if not z.cases:
            continue
        c = z.cases[0]
        red = dataclasses.replace(z, cases=(dataclasses.replace(c, open_colours=(R,)), *z.cases[1:]))
        after = zone_order([red if x is z else x for x in zs], [], AS_OF)
        assert next(r for r in after["zones"] if r["zoneId"] == z.zone_id)["waitingPeople"] <= \
            next(r for r in out["zones"] if r["zoneId"] == z.zone_id)["waitingPeople"]


@SETTINGS
@given(zones(), st.data())
def test_the_estimate_changes_only_order_never_counts(zs, data):
    before = zone_order(zs, [], AS_OF)
    moved = [dataclasses.replace(z, not_yet_checked=(lo := data.draw(st.integers(0, 50000)), lo + data.draw(st.integers(0, 9000))))
             for z in zs]
    after = zone_order(moved, [], AS_OF)
    counts = lambda o: {r["zoneId"]: (r["waitingPeople"], r["registerNotChecked"], r["lastCheckAt"]) for r in o["zones"]}
    assert counts(before) == counts(after)
    assert len(after["zones"]) == len(zs) and not after["emergencies"]


@SETTINGS
@given(zones())
def test_every_suggested_check_carries_its_reasons(zs):
    out = zone_order(zs, [], AS_OF)
    by_id = {z.zone_id: z for z in zs}
    for s in out["suggestedChecks"]:
        z, why = by_id[s["zoneId"]], s["reasons"]
        assert why and "0 reviewed calls" in why and not z.cases
        assert any(w.startswith("never checked") or w.startswith("last checked") for w in why)
        assert any("flooded part" in w or "cited flood" in w or "reported by" in w for w in why)
        assert z.last_check is None or (AS_OF - z.last_check) >= timedelta(hours=6)
    for row in out["zones"]:
        assert row["reasons"]


@SETTINGS
@given(zones())
def test_order_is_total_and_follows_the_rule(zs):
    out = zone_order(zs, [], AS_OF)
    assert ids(out) == ids(zone_order(list(reversed(zs)), [], AS_OF))
    keys = [zone_sort_key(next(z for z in zs if z.zone_id == i)) for i in ids(out)]
    assert keys == sorted(keys)
    w = [r["waitingPeople"] for r in out["zones"]]
    assert w == sorted(w, reverse=True)
