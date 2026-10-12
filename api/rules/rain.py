"""Rain context and the "heavy rain: re-check" prompt (D41). Owner: user. Pure functions, no I/O.

Input is the satellite rain estimate per area (half-hourly mm, `data/<package>/rain-imerg.json`), replayed on the
demo clock. Output, per area and time:
    - a context line: rain in the last 1 h, 3 h and 24 h, with its source and the 24 h class;
    - a prompt when the last 3 h reach HEAVY_3H_MM: segments checked before the heavy rain began are worth checking
      again, lowest ground first.

Limits, kept in the output:
    - rain is not water depth and never becomes one; it never changes a count, a depth band or the zone order;
    - the satellite estimate under-reads heavy storms, so totals are labelled "at least" when any value is missing
      and "satellite estimate" always; missing data is unknown, never 0 mm;
    - cells are about 10 km, so the prompt is for the whole area, not a zone ranking;
    - the coordinator accepts or dismisses the prompt; nothing changes until then.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable, Mapping

from api.rules.tiers import CHECKED, ZoneInput

STEP = timedelta(minutes=30)
HEAVY_3H_MM = 35.0  # TMD's "heavy rain" day (35.1–90 mm) falling within 3 hours; our threshold, friend to confirm
# Thai Meteorological Department 24 h classes (mm): light 0.1–10, moderate 10.1–35, heavy 35.1–90, very heavy > 90
CLASSES_24H = ((90.0, "very heavy"), (35.0, "heavy"), (10.0, "moderate"), (0.0, "light"))
REPLAY_OFFSET = datetime(2026, 10, 11, tzinfo=timezone.utc) - datetime(2025, 11, 24, tzinfo=timezone.utc)  # 321 days
BANGKOK = timezone(timedelta(hours=7))


@dataclass(frozen=True)
class Total:
    mm: float | None  # None: no data in the window
    complete: bool  # False: some half hours are missing, so mm is a floor

    def text(self) -> str:
        if self.mm is None:
            return "no data"
        v = f"{self.mm:.0f} mm"
        return v if self.complete else f"at least {v}"


def _ts(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def series_from_file(doc: Mapping[str, Any], area_id: str, offset: timedelta = REPLAY_OFFSET) -> list[tuple[datetime, float | None]]:
    """One area's half-hour values from rain-imerg.json, moved onto the demo clock."""
    return [(_ts(t) + offset, mm) for t, mm in doc["areas"][area_id]]


def total(series: Iterable[tuple[datetime, float | None]], as_of: datetime, hours: float) -> Total:
    """Rain in (as_of − hours, as_of]. A half hour cut by the window counts in proportion."""
    start = as_of - timedelta(hours=hours)
    got, have, missing, covered = 0.0, False, False, timedelta(0)
    for t, mm in series:
        lo, hi = max(t, start), min(t + STEP, as_of)
        if hi <= lo:
            continue
        covered += hi - lo
        if mm is None:
            missing = True
        else:
            have = True
            got += mm * ((hi - lo) / STEP)
    if not have:
        return Total(None, False)  # unknown, never 0 mm
    return Total(round(got, 1), not missing and covered >= as_of - start)


def heavy_since(series: list[tuple[datetime, float | None]], as_of: datetime) -> datetime | None:
    """Start of the current heavy spell: 3 h before the first half-hour mark from which every check is heavy.
    Stable while the spell lasts, so the prompt keeps one ID and a dismissal sticks."""
    def heavy(t):
        m = total(series, t, 3).mm
        return m is not None and m >= HEAVY_3H_MM
    if not heavy(as_of):
        return None
    first = as_of
    mark = as_of - timedelta(minutes=as_of.minute % 30, seconds=as_of.second, microseconds=as_of.microsecond)
    if mark == as_of:
        mark -= STEP
    for _ in range(96):  # at most two days back
        if not heavy(mark):
            break
        first, mark = mark, mark - STEP
    return first - timedelta(hours=3)


def class_24h(mm: float | None) -> str | None:
    if mm is None:
        return None
    if mm == 0:
        return "no rain"
    return next(name for floor, name in CLASSES_24H if mm > floor)


def _clock(t: datetime) -> str:
    return t.astimezone(BANGKOK).strftime("%H:%M")


def rain_status(area_id: str, series: list[tuple[datetime, float | None]], as_of: datetime,
                zones: list[ZoneInput], ground_m: Mapping[str, float]) -> dict:
    """Context and, when the last 3 h are heavy, the re-check prompt for one area.

    `ground_m` is each segment's median ground height (FABDEM p50 from the area package), used only to put low ground
    first in the re-check list.
    """
    if as_of.tzinfo is None:
        raise ValueError("as_of must be timezone-aware")
    h1, h3, h24 = (total(series, as_of, h) for h in (1, 3, 24))
    out = {
        "areaId": area_id,
        "asOf": as_of.isoformat().replace("+00:00", "Z"),
        "label": "Rain (satellite estimate). Often under-reads heavy storms; not water depth",
        "source": "NASA GPM IMERG V07, about 10 km cells, replayed from 24 Nov 2025",
        "last1h": h1.mm, "last3h": h3.mm, "last24h": h24.mm,
        "complete": h1.complete and h3.complete and h24.complete,
        "class24h": class_24h(h24.mm),
        "line": "Rain data unavailable" if h24.mm is None else
                f"Rain (satellite estimate): {h3.text()} in the last 3 h · {h24.text()} in 24 h ({class_24h(h24.mm)})",
        "prompt": None,
    }
    if h3.mm is None or h3.mm < HEAVY_3H_MM:
        return out
    since = heavy_since(series, as_of)
    recheck = []
    for z in zones:
        for s in z.segments:
            if s.check_state in CHECKED and s.checked_at < since:
                recheck.append((ground_m.get(s.segment_id, float("inf")), s.segment_id, z.zone_id, s))
    recheck.sort(key=lambda r: (r[0], r[1]))
    area_ground = [ground_m[s.segment_id] for z in zones for s in z.segments if s.segment_id in ground_m]

    def lower_than(g: float) -> str:
        if g == float("inf") or len(area_ground) < 2:
            return ""
        pct = round(100 * sum(1 for x in area_ground if x > g) / len(area_ground))
        return f" · lower ground than {pct}% of {area_id}"
    out["prompt"] = {
        "promptId": f"RAIN-{area_id}-{since.strftime('%Y%m%dT%H%MZ')}",
        "state": "proposed",
        "title": f"Heavy rain since {_clock(since)}: re-check segments checked before then",
        "reasons": [f"{h3.text()} in the last 3 h (satellite estimate; heavy is {HEAVY_3H_MM:.0f} mm in 3 h)",
                    f"{h24.text()} in the last 24 h ({class_24h(h24.mm)})",
                    "Water may have risen where teams already checked; rain alone can't say where or how deep"],
        "recheck": [{"segmentId": sid, "zoneId": zid, "checkedAt": s.checked_at.isoformat().replace("+00:00", "Z"),
                     "groundM": None if g == float("inf") else g,
                     "reason": f"{'Checked' if s.check_state == 'checked' else 'Partly checked'} at {_clock(s.checked_at)}, "
                               f"before the heavy rain{lower_than(g)}"}
                    for g, sid, zid, s in recheck],
        "note": "A prompt only: the coordinator accepts or dismisses it. Rain never changes counts, depth or the zone order.",
    }
    return out
