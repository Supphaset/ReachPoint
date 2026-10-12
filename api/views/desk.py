"""Desk views: zone order and suggested checks (C12), rain (C18), water rising (C19).

Each is built from the same records as the team and briefing views, through the area briefings, so the desk and the
teams never see two versions of a zone.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from api.rules.rain import rain_status, series_from_file
from api.rules.rising import WaitingFamily, gauge_status, rising_water
from api.rules.tiers import PriorityColour, TierInput, ZoneInput, colour, register_counts, zone_order
from api.views.briefing import area_briefing
from api.views.store import ROOT, Store
from api.views.team import listing_doc, team_missions

AREAS = ("P-A", "P-B", "P-C")


def _iso(t: datetime) -> str:
    return t.isoformat().replace("+00:00", "Z")


def zone_inputs(store: Store, briefing_at: str, areas=AREAS, with_register: bool = True) -> list[ZoneInput]:
    reg = register_counts(store.register) if with_register else None
    return [ZoneInput.from_briefing(z, reg) for a in areas for z in area_briefing(store, a, briefing_at)["zones"]]


def red_listings(store: Store) -> list[TierInput]:
    out = []
    for case, need in store.needs():
        if need["review"] != "validated" or need["allocation"]["state"] != "open":
            continue
        doc = listing_doc(case, need)
        doc["pickup"]["at"] = store.landmarks[case["segmentId"]]["at"]
        t = TierInput.from_listing(doc)
        if colour(t) is PriorityColour.RED:
            out.append(t)
    return out


def zone_order_view(store: Store, as_of: datetime, briefing_at: str) -> dict:
    return zone_order(zone_inputs(store, briefing_at), red_listings(store), as_of)


def _ground(store: Store, area_id: str | None = None) -> dict[str, float]:
    return {s["id"]: s["depth"]["groundM"][1] for z in store.catalogue["zones"]
            if area_id is None or z["areaId"] == area_id for s in z["segments"]}


def _rain(package: str = "hy-2025-11", root: Path = ROOT) -> dict:
    return json.loads((root / "data" / package / "rain-imerg.json").read_text())


def _gauge(package: str = "hy-2025-11", root: Path = ROOT) -> dict:
    return json.loads((root / "data" / package / "gauge-x44.json").read_text())


def rain_view(store: Store, area_id: str, as_of: datetime, briefing_at: str, rain: dict | None = None) -> dict:
    zones = zone_inputs(store, briefing_at, (area_id,), with_register=False)
    return rain_status(area_id, series_from_file(rain or _rain(), area_id), as_of, zones, _ground(store))


def waiting_families(store: Store, team_at: str, briefing_at: str) -> list[WaitingFamily]:
    """Every reviewed evacuation listing, as the teams see it (from the first evacuation team's view)."""
    team = next(t for t in store.seed["teams"] if "evacuation_transport" in t["capabilities"])
    return [WaitingFamily.from_listing(l) for l in team_missions(store, team["teamId"], team_at, briefing_at)["open"]]


def rising_water_view(store: Store, area_id: str, as_of: datetime, team_at: str, briefing_at: str,
                      gauge: dict | None = None, rain: dict | None = None) -> dict:
    """X.44 runs through the city centre, so only P-B gets the gauge; rain applies to every area."""
    ground = _ground(store, area_id)
    g = gauge_status(gauge or _gauge(), as_of) if area_id in (gauge or _gauge())["station"]["areas"] else None
    r = rain_status(area_id, series_from_file(rain or _rain(), area_id), as_of, [], ground)
    return rising_water(area_id, as_of, waiting_families(store, team_at, briefing_at), ground, gauge=g, rain=r)
