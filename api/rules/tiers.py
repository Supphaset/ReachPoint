"""Shared priority tiers and the open-list sort (C3). Owner: user. Pure functions, no I/O.

One rule, used everywhere a list of waiting requests is ordered:
    1. colour: RED (life-threatening) → YELLOW (urgent) → GREEN (can wait). RED always comes first (D9);
    2. then distance from the team, nearest first (unknown distance goes after every known one);
    3. then waiting time, longest first;
    4. then the listing ID, so the order is total and the same on every machine.

The colours are a view of the solver's tiers (design doc, "Urgent tier"), so the team lists, the split
solver (`allocation.py`) and the triage agent's safety floor can never disagree:

    tier 1a  validated + a qualified review requiring urgent medical capability   → RED
    tier 1b  validated + a coordinator `urgent` flag with a stated reason          → RED
    tier 2   any other validated evacuation or medical need                        → YELLOW
    tier 2   validated supplies                                                    → GREEN

Mapping proposed 12 Oct (user); friend to confirm. Nothing here reads free text: what a caller says can
change the order only through a reviewed field (a qualified review or the coordinator's flag).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Mapping


class PriorityColour(str, Enum):
    RED = "red"
    YELLOW = "yellow"
    GREEN = "green"


class Tier(str, Enum):
    T1A = "1a"
    T1B = "1b"
    T2 = "2"


COLOUR_RANK = {PriorityColour.RED: 0, PriorityColour.YELLOW: 1, PriorityColour.GREEN: 2}
ASSISTANCE_TYPES = ("evacuation_transport", "medical", "supplies")


class NotReviewed(ValueError):
    """Only validated listings have a colour; unreviewed reports stay on the desk, not on team lists."""


@dataclass(frozen=True)
class TierInput:
    """The reviewed fields that decide a listing's tier and place. Locations are landmark-level (D25)."""

    listing_id: str
    assistance_type: str  # evacuation_transport | medical | supplies
    review: str  # reported | validated | needs_clarification
    waiting_since: datetime  # when the need was first reviewed; timezone-aware
    qualified_urgent_medical: bool = False  # qualified review requires urgent medical capability
    urgent_reason: str | None = None  # coordinator urgent flag; only counts with a stated reason
    at: tuple[float, float] | None = None  # (lon, lat) of the pickup landmark, if known

    def __post_init__(self):
        if self.assistance_type not in ASSISTANCE_TYPES:
            raise ValueError(f"unknown assistance type {self.assistance_type!r}")
        if self.waiting_since.tzinfo is None:
            raise ValueError("waiting_since must be timezone-aware")

    @classmethod
    def from_listing(cls, doc: Mapping[str, Any]) -> "TierInput":
        """From a listing document (draft shape, see contract/fixtures/listings.sort-cases.json)."""
        urgent = doc.get("urgentFlag") or {}
        at = doc.get("pickup", {}).get("at")
        return cls(
            listing_id=doc["listingId"],
            assistance_type=doc["assistanceType"],
            review=doc["review"],
            waiting_since=datetime.fromisoformat(doc["waitingSince"].replace("Z", "+00:00")),
            qualified_urgent_medical=bool(doc.get("qualifiedAssessment", {}).get("urgentMedical")),
            urgent_reason=urgent.get("reason"),
            at=tuple(at) if at else None,
        )


def tier(item: TierInput) -> Tier:
    """The solver's tier. The split panel and the colour both come from this one function."""
    if item.review != "validated":
        raise NotReviewed(item.listing_id)
    if item.qualified_urgent_medical:
        return Tier.T1A
    if item.urgent_reason and item.urgent_reason.strip():
        return Tier.T1B
    return Tier.T2


def colour(item: TierInput) -> PriorityColour:
    if tier(item) in (Tier.T1A, Tier.T1B):
        return PriorityColour.RED
    return PriorityColour.GREEN if item.assistance_type == "supplies" else PriorityColour.YELLOW


def distance_m(a: tuple[float, float], b: tuple[float, float]) -> float:
    """Great-circle distance in metres between two (lon, lat) points. Straight line, not a route."""
    lon1, lat1, lon2, lat2 = map(math.radians, (*a, *b))
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 2 * 6_371_000 * math.asin(math.sqrt(h))


def sort_key(item: TierInput, team_location: tuple[float, float] | None) -> tuple:
    """Key for `sorted(listings, key=lambda l: sort_key(l, team_at))`: colour → distance → waiting → ID."""
    if item.at is None or team_location is None:
        dist = (1, 0.0)  # unknown distance: after every known one, never before
    else:
        dist = (0, round(distance_m(team_location, item.at), 1))
    return (COLOUR_RANK[colour(item)], dist, item.waiting_since.timestamp(), item.listing_id)


def order(items: list[TierInput], team_location: tuple[float, float] | None) -> list[TierInput]:
    return sorted(items, key=lambda i: sort_key(i, team_location))
