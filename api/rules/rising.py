"""Water rising: who to re-confirm first (D42). Owner: user. Pure functions, no I/O.

When the river gauge or the rain says the water is rising, families who were safe enough to wait may not be any
more. This rule turns those signals into a short, ranked list for the desk: **waiting families to call back first**,
each with its reasons. It never changes a colour, a tier or a count:
    - water rising is a reason to *ask again*, never proof that someone is in danger;
    - RED still needs a person: a callback that reports danger, or the coordinator's urgent flag with a reason (1b);
    - a forecast is always labelled as a forecast; a gauge reading carries its time and is never filled in between;
    - a gauge level is a level at one point on the canal, never street depth.

Signals (any one starts the prompt):
    - gauge forecast: a published rise of RISE_FORECAST_M or more, valid now (e.g. DDPM, 24 Nov: +1.25–1.45 m);
    - gauge reading: over the bank and up RISE_24H_M or more in 24 h;
    - heavy rain: the D41 rain prompt is up (35 mm or more in 3 h).

How much it may rise (estimate): when a gauge forecast gives a rise, each family that reported a depth also gets
"if the water here rises like the canal: about A–B m (band)", i.e. their reported depth plus the forecast rise. It is
an upper guide, not a measurement: places farther from the canal may rise less. Families with no depth report get
"ask how deep the water is now". Families whose estimate reaches over head height (2 m) are marked `mayBeOverHead`.

Ranking of waiting (non-RED, with an open group) families: points, shown as reasons, then oldest confirmation, then
listing ID. Estimate reaches over head height 1 · water reported at their landmark (chest deep or more 2, any other or older than 6 h 1) · lower ground than most of the area
(lowest third 2, middle third 1) · someone who can't walk or a stretcher case 2, children or babies 1 · last confirmed
6 h or more ago 2, 3 h or more 1.
"""

from __future__ import annotations

import re

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Mapping

from api.rules.rain import BANGKOK, REPLAY_OFFSET

RISE_FORECAST_M = 0.5
RISE_24H_M = 0.3
CHEST_M = 1.3
OVER_HEAD_M = 2.0
BANDS = ((4.0, "above the 2nd floor level"), (3.0, "up to the 2nd floor"), (2.0, "over head height"), (1.3, "chest deep"), (1.0, "waist deep"),
         (0.5, "knee deep"), (0.0, "below the knee"))


def band(m: float) -> str:
    return next(name for floor, name in BANDS if m >= floor)


def _ts(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def _iso(t: datetime) -> str:
    return t.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _clock(t: datetime) -> str:
    return t.astimezone(BANGKOK).strftime("%H:%M")


def _ago(minutes: int) -> str:
    return f"{minutes // 60}h {minutes % 60:02d}m" if minutes >= 60 else f"{minutes}m"


# --- gauge -----------------------------------------------------------------------------------------------------

def gauge_status(doc: Mapping[str, Any], as_of: datetime, offset: timedelta = REPLAY_OFFSET) -> dict:
    """The newest reading at or before `as_of` and the forecasts valid now, on the demo clock."""
    st = doc["station"]
    readings = sorted(((_ts(r["at"]) + offset, r) for r in doc["readings"]), key=lambda x: x[0])
    past = [(t, r) for t, r in readings if t <= as_of]
    out = {"stationId": st["id"], "label": doc["label"], "bankM": st["bankM"], "warningM": st["warningM"],
           "reading": None, "forecasts": [], "line": f"River gauge {st['id']}: no reading yet"}
    if past:
        t, r = past[-1]
        over = round(r["levelM"] - st["bankM"], 2)
        trend = None if r.get("change24hM") is None else ("rising" if r["change24hM"] > 0 else "falling" if r["change24hM"] < 0 else "steady")
        out["reading"] = {"at": _iso(t), "levelM": r["levelM"], "overBankM": over, "change24hM": r.get("change24hM"),
                          "flowM3s": r.get("flowM3s"), "trend": trend, "source": r["source"],
                          "aboveWarning": r["levelM"] >= st["warningM"]}
        where = f"{over:.2f} m over the bank" if over > 0 else f"{-over:.2f} m below the bank"
        change = "" if r.get("change24hM") is None else f", {r['change24hM']:+.2f} m in 24 h"
        out["line"] = f"River {st['id']} at {_clock(t)}: {r['levelM']:.2f} m, {where}{change} (reading, RID)"
    for f in doc.get("forecasts", []):
        issued, until = _ts(f["issuedAt"]) + offset, _ts(f["validUntil"]) + offset
        if issued <= as_of < until:
            out["forecasts"].append({"issuedAt": _iso(issued), "validUntil": _iso(until), "issuer": f["issuer"],
                                     "riseM": f["riseM"], "text": f["text"],
                                     "line": f"Forecast ({f['issuer']}, {_clock(issued)}): {f['text']}"})
    return out


def signals(gauge: dict | None, rain: dict | None) -> list[dict]:
    """The reasons the water may be rising now, each with its kind, source and start time."""
    out = []
    if gauge:
        for f in gauge["forecasts"]:
            if f["riseM"][0] >= RISE_FORECAST_M:
                out.append({"kind": "gauge_forecast", "since": f["issuedAt"], "text": f["line"]})
        r = gauge["reading"]
        if r and r["overBankM"] > 0 and (r["change24hM"] or 0) >= RISE_24H_M:
            out.append({"kind": "gauge_reading", "since": r["at"], "text": gauge["line"]})
    if rain and rain.get("prompt"):
        out.append({"kind": "heavy_rain", "since": rain["prompt"]["promptId"], "text": rain["line"]})
    return out


# --- families --------------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class WaitingFamily:
    listing_id: str
    case_id: str
    colour: str
    segment_id: str
    label: str
    people: str  # "4 people: 2 adults, 2 children"
    children: int
    cant_walk: bool  # a stretcher case or "can't walk"
    water_m: float | None
    water_text: str | None
    water_at: datetime | None
    water_stale: bool
    last_confirmed: datetime
    open_groups: int

    @classmethod
    def from_listing(cls, l: Mapping[str, Any]) -> "WaitingFamily":
        """From an open listing in a team view (contract/fixtures/teamMissions.*.json)."""
        facts = l["urgency"]["facts"]
        water = next((f for f in facts if f["kind"] == "water"), None)
        people = next((f["text"] for f in facts if f["kind"] == "people"), "")
        parties = [g["party"] for g in l["groups"]]
        return cls(
            listing_id=l["listingId"], case_id=l["caseId"], colour=l["colour"], segment_id=l["segmentId"],
            label=l["landmarkLabel"], people=people,
            children=sum(p["children"] + p["infants"] for p in parties),
            cant_walk=any(p["stretcher"] for p in parties) or any(f["kind"] == "mobility" for f in facts),
            water_m=_band_m(water["text"]) if water else None, water_text=water["text"] if water else None,
            water_at=_ts(water["at"]) if water and water.get("at") else None,
            water_stale=bool(water and water.get("stale")),
            last_confirmed=_ts(l["lastConfirmedAt"]),
            open_groups=sum(1 for g in l["groups"] if g["state"] == "open"),
        )


def _band_m(text: str) -> float | None:
    m = re.search(r"about ([\d.]+) m", text)
    return float(m.group(1)) if m else None


def projection(f: WaitingFamily, rise: tuple[float, float] | None) -> dict | None:
    """Reported depth + the forecast rise at the gauge: an upper guide for this place, labelled as an estimate."""
    if rise is None:
        return None
    if f.water_m is None:
        return {"text": "No depth reported here: ask how deep the water is now", "rangeM": None, "mayBeOverHead": None}
    lo, hi = round(f.water_m + rise[0], 1), round(f.water_m + rise[1], 1)
    b = band(lo) if band(lo) == band(hi) else f"{band(lo)} to {band(hi)}"
    old = ", from a report older than 6 h" if f.water_stale else ""
    return {"text": f"If the water here rises like the canal: about {lo:.1f}–{hi:.1f} m, {b} (estimate{old})",
            "rangeM": [lo, hi], "mayBeOverHead": hi >= OVER_HEAD_M}


def rank_families(families: list[WaitingFamily], as_of: datetime, ground_m: Mapping[str, float], area_id: str,
                  rise: tuple[float, float] | None = None) -> list[dict]:
    """Waiting non-RED families with an open group, most at risk first, each with its reasons and points.
    `rise` is the forecast rise at the gauge (low, high) in metres, if one is valid now."""
    area = sorted(ground_m.values())
    rows = []
    for f in families:
        if f.colour == "red" or f.open_groups == 0:
            continue
        pts, why = 0, []
        if f.water_m is not None:
            pts += 1 if f.water_stale or f.water_m < CHEST_M else 2
            said = f"{f.water_text.split(' at ')[0]} at {_clock(f.water_at)}" if f.water_at else f.water_text
            why.append(said + (" (report older than 6 h)" if f.water_stale else ""))
        g = ground_m.get(f.segment_id)
        if g is not None and len(area) >= 3:
            higher = sum(1 for x in area if x > g) / len(area)
            if higher >= 2 / 3:
                pts += 2
            elif higher >= 1 / 3:
                pts += 1
            if higher >= 1 / 3:
                why.append(f"lower ground than {round(100 * higher)}% of {area_id}")
        if f.cant_walk:
            pts += 2
            why.append("someone can't walk")
        elif f.children:
            pts += 1
            why.append(f"{f.children} {'child' if f.children == 1 else 'children'}")
        est = projection(f, rise)
        if est and est["mayBeOverHead"]:
            pts += 1
            why.append(f"may reach {band(est['rangeM'][1])} if the canal rises as forecast")
        mins = int((as_of - f.last_confirmed).total_seconds() // 60)
        if mins >= 360:
            pts += 2
        elif mins >= 180:
            pts += 1
        why.append(f"last confirmed {_ago(mins)} ago")
        rows.append({"listingId": f.listing_id, "caseId": f.case_id, "label": f.label, "people": f.people,
                     "points": pts, "reasons": why, "lastConfirmedAt": _iso(f.last_confirmed),
                     "ifItRises": est,
                     "actions": ["call_back", "flag_urgent", "dismiss"]})
    rows.sort(key=lambda r: (-r["points"], r["lastConfirmedAt"], r["listingId"]))
    for i, r in enumerate(rows, 1):
        r["rank"] = i
    return rows


def rising_water(area_id: str, as_of: datetime, families: list[WaitingFamily], ground_m: Mapping[str, float], *,
                 gauge: dict | None = None, rain: dict | None = None, limit: int = 5) -> dict:
    """The desk prompt for one area, or no prompt when nothing says the water is rising."""
    if as_of.tzinfo is None:
        raise ValueError("as_of must be timezone-aware")
    sig = signals(gauge, rain)
    out = {"areaId": area_id, "asOf": _iso(as_of), "gaugeLine": gauge["line"] if gauge else None,
           "forecastLines": [f["line"] for f in gauge["forecasts"]] if gauge else [], "prompt": None}
    if not sig:
        return out
    rises = [tuple(f["riseM"]) for f in (gauge or {}).get("forecasts", []) if f["riseM"][0] >= RISE_FORECAST_M]
    rise = max(rises, key=lambda r: r[1]) if rises else None
    ranked = rank_families(families, as_of, ground_m, area_id, rise)
    first = min(s["since"] for s in sig if s["kind"] != "heavy_rain") if any(s["kind"] != "heavy_rain" for s in sig) else sig[0]["since"]
    out["prompt"] = {
        "promptId": f"RISE-{area_id}-{first}",
        "state": "proposed",
        "title": "Water rising: re-confirm these families first",
        "signals": sig,
        "rise": None if rise is None else {"atGaugeM": list(rise), "text": f"Forecast rise at the canal: {rise[0]:.2f}–{rise[1]:.2f} m"},
        "reconfirm": ranked[:limit],
        "more": max(0, len(ranked) - limit),
        "note": ("Water rising is a reason to ask again, not proof of danger. A family becomes RED only after a "
                 "callback reports danger or the coordinator flags it urgent with a reason."),
    }
    return out
