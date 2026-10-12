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


# --- Zone order and suggested checks (D17c, D18; C12) ---------------------------------------------------------
#
# The desk's work list:
#     1. RED emergencies first. They are cases, never zones, and their people never count towards a zone.
#     2. Then zones, each with its reasons, by a fixed rule (the triage agent's safety floor and fallback, D22):
#         a. reviewed people who called and still wait for a team (open non-RED needs);
#         b. vulnerable residents on the register, in segments not yet checked (counts only, never details);
#         c. estimated people living in segments not yet checked (low end, then high end);
#         d. time since the last check, longest first ("Couldn't reach" is not a check);
#         e. the zone ID, so the order is total.
#     A coordinator pin puts a zone above the rule, with its reason and author; never above an emergency.
#
# The estimate only orders zones: it never adds to a count and never creates a case. A suggested check (D18) is a
# zone with flood evidence, people living in the flooded part, no reviewed calls, and no check in the last 6 hours.
# The coordinator publishes or dismisses it; nothing is published automatically. The call-rate "quiet" flag and the
# depth rise come with exposure.py (C15) and the depth tool (C17).

CHECKED = ("checked", "partly_checked")  # a team was there; could_not_reach never counts as a check
CHECK_STATES = ("not_checked", *CHECKED, "could_not_reach")
SUGGEST_AFTER_S = 6 * 3600
SUGGEST_MIN_FLOODED = 100  # people living in the flooded part (low end): "buildings in the water"


def _ts(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def _zone_key(zone_id: str) -> tuple:
    """B-2 before B-10."""
    prefix, _, num = zone_id.partition("-")
    return (prefix, int(num) if num.isdigit() else 0, zone_id)


@dataclass(frozen=True)
class SegmentInput:
    segment_id: str
    check_state: str = "not_checked"
    checked_at: datetime | None = None

    def __post_init__(self):
        if self.check_state not in CHECK_STATES:
            raise ValueError(f"unknown check state {self.check_state!r}")
        if self.check_state in CHECKED and self.checked_at is None:
            raise ValueError(f"{self.segment_id}: a check needs its time")

    @property
    def open(self) -> bool:
        """Still counts as "not yet checked" (D27): everything except Checked; Partly checked and Couldn't reach stay in."""
        return self.check_state not in ("checked",)


@dataclass(frozen=True)
class CaseInput:
    """A reviewed case in the zone: its people and the colours of its needs still waiting for a team."""

    case_id: str
    segment_id: str | None
    people: int
    open_colours: tuple[PriorityColour, ...]

    @property
    def emergency(self) -> bool:
        return PriorityColour.RED in self.open_colours

    @property
    def waiting(self) -> bool:
        return bool(self.open_colours) and not self.emergency


@dataclass(frozen=True)
class ZoneInput:
    zone_id: str
    area_id: str
    segments: tuple[SegmentInput, ...]
    cases: tuple[CaseInput, ...] = ()
    not_yet_checked: tuple[int, int] = (0, 0)  # estimate: people living in segments not yet checked (D27-D28)
    flooded_part: tuple[int, int] = (0, 0)  # estimate: people living in the flooded part
    flood_reports: int = 0  # cited official and news reports in the zone
    caller_water: int = 0  # reviewed caller water reports in the zone
    register: Mapping[str, int] | None = None  # vulnerable residents per segment (counts only)

    @classmethod
    def from_briefing(cls, zone: Mapping[str, Any], register_counts: Mapping[str, int] | None = None) -> "ZoneInput":
        """From one zone of an area briefing (contract/fixtures/areaBriefing.*.json)."""
        est = zone.get("estimate") or {}
        facts = {f["key"]: f["value"] for f in zone.get("facts", [])}
        flooded = est.get("modelledFlooded") if est.get("basis") == "model" else est.get("inSatelliteExtent")
        segs = tuple(SegmentInput(s["segmentId"], s["check"]["state"], _ts(s["check"]["at"]) if s["check"].get("at") else None)
                     for s in zone["segments"])
        ids = {s.segment_id for s in segs}
        cases = tuple(CaseInput(c["caseId"], c.get("segmentId"), c["people"],
                                tuple(PriorityColour(a["priority"]) for a in c["assistance"]
                                      if a["review"] == "validated" and a["allocation"] == "open"))
                      for c in zone.get("cases", []))
        return cls(zone_id=zone["zoneId"], area_id=zone["areaId"], segments=segs, cases=cases,
                   not_yet_checked=tuple(est.get("notYetChecked") or (0, 0)), flooded_part=tuple(flooded or (0, 0)),
                   flood_reports=facts.get("reportedFloodingPoints", 0), caller_water=len(zone.get("callerWater", [])),
                   register={k: v for k, v in (register_counts or {}).items() if k in ids})

    @property
    def waiting_people(self) -> int:
        return sum(c.people for c in self.cases if c.waiting)

    @property
    def register_not_checked(self) -> int:
        open_ids = {s.segment_id for s in self.segments if s.open}
        return sum(n for seg, n in (self.register or {}).items() if seg in open_ids)

    @property
    def last_check(self) -> datetime | None:
        times = [s.checked_at for s in self.segments if s.check_state in CHECKED]
        return max(times) if times else None


@dataclass(frozen=True)
class Pin:
    """A coordinator's override: this zone goes above the rule. Needs a reason and an author (D22)."""

    zone_id: str
    reason: str
    by: str

    def __post_init__(self):
        if not (self.reason or "").strip() or not (self.by or "").strip():
            raise ValueError(f"pin on {self.zone_id} needs a reason and who set it")


def register_counts(register: Mapping[str, Any]) -> dict[str, int]:
    """Vulnerable residents per segment from the register fixture. Counts only; details stay with the coordinator."""
    out: dict[str, int] = {}
    for e in register["entries"]:
        out[e["segmentId"]] = out.get(e["segmentId"], 0) + int(e["people"])
    return out


def _range(r: tuple[int, int]) -> str:
    lo, hi = r
    return f"~{lo:,}" if lo == hi else f"~{lo:,}–{hi:,}"


def _since(z: ZoneInput, as_of: datetime) -> str:
    if z.last_check is None:
        return "never checked"
    mins = int((as_of - z.last_check).total_seconds() // 60)
    return f"last checked {mins // 60}h {mins % 60:02d}m ago" if mins >= 60 else f"last checked {mins}m ago"


def zone_sort_key(z: ZoneInput) -> tuple:
    never = z.last_check is None
    return (-z.waiting_people, -z.register_not_checked, -z.not_yet_checked[0], -z.not_yet_checked[1],
            0 if never else 1, z.last_check.timestamp() if z.last_check else 0.0, _zone_key(z.zone_id))


def _reasons(z: ZoneInput, as_of: datetime) -> list[str]:
    out = []
    if z.waiting_people:
        n = sum(1 for c in z.cases if c.waiting)
        out.append(f"{z.waiting_people} reviewed {'person' if z.waiting_people == 1 else 'people'} waiting for a team "
                   f"({n} {'case' if n == 1 else 'cases'})")
    if z.register_not_checked:
        out.append(f"{z.register_not_checked} on the vulnerable register (not confirmed in need)")
    if z.not_yet_checked[1]:
        out.append(f"{_range(z.not_yet_checked)} live in segments not yet checked (estimate)")
    out.append(_since(z, as_of))
    return out


def suggested_check(z: ZoneInput, as_of: datetime) -> list[str] | None:
    """D18: the reasons this zone should get a suggested check, or None. Every condition shows up in the reasons."""
    evidence = []
    if z.flooded_part[0] >= SUGGEST_MIN_FLOODED:
        evidence.append(f"{_range(z.flooded_part)} live in the flooded part (estimate)")
    if z.flood_reports:
        evidence.append(f"{z.flood_reports} cited flood {'report' if z.flood_reports == 1 else 'reports'}")
    if z.caller_water:
        evidence.append(f"water reported by {z.caller_water} {'caller' if z.caller_water == 1 else 'callers'}")
    calls = len(z.cases)
    recent = z.last_check is not None and (as_of - z.last_check).total_seconds() < SUGGEST_AFTER_S
    if not evidence or calls or recent:
        return None
    if z.flooded_part[0] < SUGGEST_MIN_FLOODED:
        evidence.append(f"{_range(z.not_yet_checked)} live here (estimate)")
    out = [*evidence, "0 reviewed calls", _since(z, as_of)]
    if z.register_not_checked:
        out.append(f"{z.register_not_checked} on the vulnerable register (not confirmed in need)")
    return out


def zone_order(zones: list[ZoneInput], emergencies: list[TierInput], as_of: datetime, *,
               pins: list[Pin] = (), published: set[str] = frozenset(), dismissed: set[str] = frozenset()) -> dict:
    """The desk's ordered work list. Pure: same input, same output.

    `emergencies` are the RED listings (checked here); they come first in `tiers.order` order without a team
    location. `published` zones already have a zone mission and `dismissed` ones were dismissed by the coordinator:
    neither gets a new suggested check.
    """
    if as_of.tzinfo is None:
        raise ValueError("as_of must be timezone-aware")
    ids = [z.zone_id for z in zones]
    if len(ids) != len(set(ids)):
        raise ValueError("zone IDs must be unique")
    for e in emergencies:
        if colour(e) is not PriorityColour.RED:
            raise ValueError(f"{e.listing_id} is not RED; only RED listings are emergencies")
    pinned = {}
    for p in pins:
        if p.zone_id not in ids:
            raise ValueError(f"pin on unknown zone {p.zone_id}")
        pinned.setdefault(p.zone_id, p)

    by_id = {z.zone_id: z for z in zones}
    ruled = sorted(zones, key=zone_sort_key)
    ordered = [by_id[i] for i in pinned] + [z for z in ruled if z.zone_id not in pinned]
    rows = []
    for rank, z in enumerate(ordered, 1):
        p = pinned.get(z.zone_id)
        rows.append({
            "rank": rank, "zoneId": z.zone_id, "areaId": z.area_id,
            "pinned": {"reason": p.reason, "by": p.by} if p else None,
            "waitingPeople": z.waiting_people,
            "registerNotChecked": z.register_not_checked,
            "notYetChecked": list(z.not_yet_checked),
            "lastCheckAt": z.last_check.isoformat().replace("+00:00", "Z") if z.last_check else None,
            "segmentsNotChecked": sum(1 for s in z.segments if s.open),
            "segments": len(z.segments),
            "reasons": ([f"Pinned by {p.by}: {p.reason}"] if p else []) + _reasons(z, as_of),
        })
    checks = []
    for z in ruled:
        if z.zone_id in published or z.zone_id in dismissed:
            continue
        why = suggested_check(z, as_of)
        if why:
            checks.append({"suggestionId": f"SC-{z.zone_id}", "zoneId": z.zone_id, "areaId": z.area_id, "reasons": why})
    return {
        "asOf": as_of.isoformat().replace("+00:00", "Z"),
        "emergencies": [{"listingId": e.listing_id, "tier": tier(e).value, "reason": e.urgent_reason if tier(e) is Tier.T1B
                         else "Qualified review: urgent medical help"} for e in order(emergencies, None)],
        "zones": rows,
        "suggestedChecks": checks,
    }
