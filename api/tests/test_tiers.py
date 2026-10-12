"""Tests for the shared tiers and sort (C3, T15). Run: python -m pytest api/tests -q"""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from api.rules.tiers import (
    COLOUR_RANK,
    NotReviewed,
    PriorityColour,
    Tier,
    TierInput,
    colour,
    distance_m,
    order,
    sort_key,
    tier,
)

FIXTURE = Path(__file__).resolve().parents[2] / "contract" / "fixtures" / "listings.sort-cases.json"
T0 = datetime(2026, 10, 11, 3, 0, tzinfo=timezone.utc)
HAT_YAI = (100.47, 7.01)


@pytest.fixture(scope="module")
def cases():
    return json.loads(FIXTURE.read_text())


# --- the shared fixture (the friend's contract test checks the open-list view against the same file) ---

def test_fixture_order(cases):
    items = [TierInput.from_listing(d) for d in cases["listings"]]
    assert [i.listing_id for i in order(items, tuple(cases["teamLocation"]))] == cases["expectedOrder"]


def test_fixture_order_without_team_location(cases):
    items = [TierInput.from_listing(d) for d in cases["listings"]]
    assert [i.listing_id for i in order(items, None)] == cases["teamUnknownOrder"]


def test_fixture_colours(cases):
    by_id = {d["listingId"]: TierInput.from_listing(d) for d in cases["listings"]}
    for lid, c in cases["expectedColours"].items():
        assert colour(by_id[lid]).value == c, lid


def test_unreviewed_has_no_colour(cases):
    with pytest.raises(NotReviewed):
        colour(TierInput.from_listing(cases["notListed"][0]))


# --- the colour mapping ---

def item(**kw):
    base = dict(listing_id="L-1", assistance_type="evacuation_transport", review="validated", waiting_since=T0)
    return TierInput(**{**base, **kw})


@pytest.mark.parametrize(
    "kw, expected_tier, expected_colour",
    [
        (dict(assistance_type="medical", qualified_urgent_medical=True), Tier.T1A, PriorityColour.RED),
        (dict(urgent_reason="linked to medical case C-01"), Tier.T1B, PriorityColour.RED),
        (dict(assistance_type="supplies", urgent_reason="insulin needs cold storage"), Tier.T1B, PriorityColour.RED),
        (dict(), Tier.T2, PriorityColour.YELLOW),
        (dict(assistance_type="medical"), Tier.T2, PriorityColour.YELLOW),
        (dict(assistance_type="supplies"), Tier.T2, PriorityColour.GREEN),
        (dict(urgent_reason="   "), Tier.T2, PriorityColour.YELLOW),  # a flag needs a stated reason
    ],
)
def test_mapping(kw, expected_tier, expected_colour):
    i = item(**kw)
    assert tier(i) == expected_tier
    assert colour(i) == expected_colour


def test_needs_clarification_is_not_on_a_list():
    with pytest.raises(NotReviewed):
        tier(item(review="needs_clarification"))


def test_bad_inputs_are_rejected():
    with pytest.raises(ValueError):
        item(assistance_type="boat")
    with pytest.raises(ValueError):
        item(waiting_since=datetime(2026, 10, 11, 3, 0))


def test_distance():
    # 0.01° of latitude is about 1.1 km
    assert distance_m((100.47, 7.00), (100.47, 7.01)) == pytest.approx(1112, abs=5)


# --- property tests (T15) ---

points = st.tuples(st.floats(100.40, 100.55), st.floats(6.95, 7.08)) | st.none()
items = st.builds(
    TierInput,
    listing_id=st.text("ABC123-", min_size=1, max_size=6),
    assistance_type=st.sampled_from(["evacuation_transport", "medical", "supplies"]),
    review=st.just("validated"),
    waiting_since=st.integers(0, 24 * 60).map(lambda m: T0 - timedelta(minutes=m)),
    qualified_urgent_medical=st.booleans(),
    urgent_reason=st.sampled_from([None, "", "elderly, bedridden", "linked to medical case"]),
    at=points,
)
team = st.tuples(st.floats(100.40, 100.55), st.floats(6.95, 7.08)) | st.none()


@settings(max_examples=300)
@given(st.lists(items, max_size=25), team)
def test_red_always_first(xs, t):
    ranks = [COLOUR_RANK[colour(i)] for i in order(xs, t)]
    assert ranks == sorted(ranks)


@settings(max_examples=300)
@given(st.lists(items, max_size=25), team)
def test_nearest_first_within_a_colour_and_unknown_last(xs, t):
    out = order(xs, t)
    for a, b in zip(out, out[1:]):
        if colour(a) != colour(b):
            continue
        known_a, known_b = a.at is not None and t is not None, b.at is not None and t is not None
        assert known_a or not known_b  # unknown distance never jumps ahead of a known one
        if known_a and known_b:
            assert distance_m(t, a.at) <= distance_m(t, b.at) + 0.1


@settings(max_examples=300)
@given(st.lists(items, max_size=25), team)
def test_longest_waiting_breaks_distance_ties(xs, t):
    out = order(xs, t)
    for a, b in zip(out, out[1:]):
        if sort_key(a, t)[:2] == sort_key(b, t)[:2]:
            assert a.waiting_since <= b.waiting_since


@given(st.lists(items, max_size=25), team, st.randoms())
def test_order_ignores_input_order(xs, t, rnd):
    shuffled = xs[:]
    rnd.shuffle(shuffled)
    assert [sort_key(i, t) for i in order(xs, t)] == [sort_key(i, t) for i in order(shuffled, t)]


@given(items)
def test_colour_is_a_view_of_the_tier(i):
    # The solver ranks by tier, the lists by colour: RED exactly when tier 1, so they can't disagree.
    assert (colour(i) == PriorityColour.RED) == (tier(i) in (Tier.T1A, Tier.T1B))
