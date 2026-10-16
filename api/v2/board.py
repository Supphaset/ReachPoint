"""Board views: what the volunteer board and the time-lapse show at a moment. Every number keeps its source."""

from __future__ import annotations

from functools import lru_cache

from api.v2 import geo as G
from api.v2 import pipeline as P
from api.v2 import sim as S
from api.v2.planner import PEOPLE_PER_HOUSEHOLD, _ground_p50, _mid

# The time-lapse stops: real moments on the 21–28 Nov 2025 timeline.
STOPS = [
    (12, "The canal is still below its bank. The map is unknown, not dry."),
    (36, "Rain all night. The first reports arrive."),
    (52, "The gauge passes the bank. The agents predict the spread and warn people first."),
    (66, "Messages pour in from every channel. Duplicates merge into households."),
    (84, "Targeted questions fill the quiet zones. Plans reach households."),
    (100, "The peak: 9.97 m at the gauge. The picture is at its sharpest."),
    (122, "The water starts to fall. Evacuated and safe households are counted."),
    (150, "Recovery. A few households still haven't answered."),
]


def zone_view(w, geo: G.Geo, zid: str) -> dict:
    meta = {z["properties"]["id"]: z["properties"] for z in geo.zones}[zid]
    lvl = w.levels[zid]
    p50 = _ground_p50(geo, zid)
    hh = [h for h in w.households.values() if h.zone_id == zid]
    obs = [o for o in w.obs if o.zone_id == zid]
    reported_people = sum(h.people or 1 for h in hh)
    possible_dupes = sum(1 for h in hh if h.possible_duplicate_of)
    est = meta["estimate"]
    # most likely depth where people are: the simulation corrected by nearby reports, at each household
    geo_b = geo.buildings
    here = []
    # reports near this zone in the last six hours (the only ones a local estimate can use)
    pool = [o for o in w.obs if abs(o.at_h - w.now_h) <= 6 and o.label != "doubtful"]
    zx = [G.to_m(h.lon, h.lat) for h in hh if h.lon is not None]
    if zx:
        x0, x1 = min(a for a, _ in zx) - 800, max(a for a, _ in zx) + 800
        y0, y1 = min(b for _, b in zx) - 800, max(b for _, b in zx) + 800
        pool = [o for o in pool if x0 <= o.x <= x1 and y0 <= o.y <= y1]
    for h in hh[-40:]:
        if h.lon is None or h.status == "evacuated":
            continue
        x, y = G.to_m(h.lon, h.lat)
        lv = P.local_level(w, x, y, w.now_h, pool=pool)
        b = geo_b.get(h.building_id) if h.building_id else None
        g = b.ground_m if b and b.ground_m is not None else p50
        if lv.wse_m is not None:
            here.append((max(0.0, lv.wse_m - g), max(0.0, lv.lo_m - g), max(0.0, lv.hi_m - g)))
    depth = None
    if here:
        ds = sorted(d for d, _, _ in here)
        depth = (round(ds[len(ds) // 2], 2), round(sorted(d for _, d, _ in here)[len(here) // 4], 2),
                 round(sorted(d for _, _, d in here)[(3 * len(here)) // 4], 2))
    elif lvl.wse_m is not None:
        depth = lvl.depth_at(p50)
    sim_surf, sim_wet = S.zone_at(zid, w.now_h)
    gaps = [o.lo + o.ground_m - o.sim_wse + (o.hi - o.lo) / 2 for o in obs
            if o.sim_wse is not None and o.label != "doubtful" and w.now_h - o.at_h <= 6]
    correction = round(sorted(gaps)[len(gaps) // 2], 2) if len(gaps) >= 2 else None
    sources = []
    if obs:
        labels = {k: sum(1 for o in obs if o.label == k) for k in ("confirmed", "unconfirmed", "doubtful")}
        first = [o for o in obs if o.source in ("self", "reply")]
        others = [o for o in obs if o.source not in ("self", "reply")]
        if first:
            sources.append({"kind": "victims", "text": f"Victim answers: {len(first)}", "labels": labels,
                            "lastH": max(o.at_h for o in first)})
        if others:
            sources.append({"kind": "posts", "text": f"Posts and relatives: {len(others)} mention water here",
                            "lastH": max(o.at_h for o in others)})
    for sp in P.satellite_by_zone()["passes"]:
        if sp["atH"] <= w.now_h:
            share = sp["share"].get(zid, 0)
            sources.append({"kind": "satellite", "text": f"Satellite (Sentinel-1): {round(share * 100)}% of buildings in mapped water",
                            "lastH": sp["atH"], "flooded": share >= 0.15})
    if w.bulletin:
        b = w.bulletin
        sources.append({"kind": "gauge", "text": f"River gauge X.44: {b['gaugeM']:.2f} m (bank 7.40), "
                                                 f"{'rising' if (b['rateMh'] or 0) > 0.01 else 'falling' if (b['rateMh'] or 0) < -0.01 else 'steady'}",
                        "lastH": b["atH"], "reconstructed": True})
    sources.append({"kind": "simulation", "text": f"Flood simulation (gauge + rain + terrain): {round(sim_wet * 100)}% of the zone under water"
                                                 + (f"; reports say {abs(correction):.1f} m {'deeper' if correction > 0 else 'shallower'} than simulated"
                                                    if correction is not None and abs(correction) >= 0.15 else
                                                    "; reports agree" if correction is not None else ""),
                    "lastH": w.now_h, "correctionM": correction, "wetShare": sim_wet})
    sources.append({"kind": "terrain", "text": f"Terrain: typical ground {p50:.1f} m above sea level", "lastH": None})
    gap = w.gaps.get(zid)
    plans = [p for p in w.plans if zid in p.get("zones", [])]
    status = {k: sum(1 for h in hh if h.status == k) for k in ("open", "safe", "evacuated", "lostContact")}
    return {
        "id": zid, "label": meta.get("label", zid), "district": meta.get("district"),
        "level": None if lvl.wse_m is None else {
            "wseM": lvl.wse_m, "loM": lvl.lo_m, "hiM": lvl.hi_m, "depthM": depth[0], "depthLoM": depth[1], "depthHiM": depth[2],
            "trendCmH": lvl.trend_cm_h, "n": lvl.n, "doubtful": len(lvl.doubtful), "certainty": lvl.certainty},
        "people": {"everyone": est.get("everyone"), "likelyFlooded": est.get("modelledFlooded"),
                   "reported": [reported_people - sum((h.people or 1) for h in hh if h.possible_duplicate_of), reported_people],
                   "households": len(hh), "elderly": sum(h.elderly for h in hh), "children": sum(h.children for h in hh),
                   "cannotWalk": sum(h.cannot_walk for h in hh), "urgent": sum(1 for h in hh if h.urgent and h.status == "open")},
        "status": status, "sources": sources, "plans": [{k: p.get(k) for k in ("id", "team", "vehicle", "seats", "eta", "offers", "at", "told")} for p in plans],
        "gap": gap, "quiet": zid in w.quiet, "predicted": zid in w.predicted, "disagree": w.disagree.get(zid),
        "summary": summary_text(zid, lvl, depth, hh, plans, gap, w, correction),
        "simulation": {"wetShare": sim_wet, "surfaceM": sim_surf, "correctionM": correction},
    }


def summary_text(zid, lvl, depth, hh, plans, gap, w, correction=None) -> str:
    """The rule-written zone summary; Gemini rewrites it on demand (api/v2/ai.py) with the same facts."""
    if lvl.wse_m is None:
        return f"{zid}: no reports yet. Unknown, not dry." + (" Water is predicted within about 6 hours." if zid in w.predicted else "")
    trend = "" if lvl.trend_cm_h is None else (f", rising about {lvl.trend_cm_h:.0f} cm/h" if lvl.trend_cm_h > 1 else
                                               f", falling about {-lvl.trend_cm_h:.0f} cm/h" if lvl.trend_cm_h < -1 else ", steady")
    open_ = [h for h in hh if h.status == "open"]
    urgent = sum(1 for h in open_ if h.urgent)
    s = (f"{zid}: most likely about {depth[0]:.1f} m (likely {depth[1]:.1f}–{depth[2]:.1f} m){trend}, from {lvl.n} reports"
         f"{f', {len(lvl.doubtful)} doubtful' if lvl.doubtful else ''}. {len(open_)} households still need help"
         f"{f', {urgent} urgent' if urgent else ''}.")
    if correction is not None and abs(correction) >= 0.3:
        s += f" Reports put the water {abs(correction):.1f} m {'above' if correction > 0 else 'below'} the simulation here" + \
             (" (likely blocked drains or a local low point)." if correction > 0 else " (likely pumping or local drainage).")
    if plans:
        p = plans[-1]
        s += f" {p.get('team') or 'A team'} plans to come{' about ' + p['eta'] if p.get('eta') else ''}."
    if gap:
        s += " " + gap
    lost = sum(1 for h in hh if h.status == "lostContact")
    if lost:
        s += f" {lost} household{'s have' if lost > 1 else ' has'} stopped answering."
    return s


def overall(w) -> dict:
    geo = G.load()
    meta = {z["properties"]["id"]: z["properties"] for z in geo.zones}
    wsum = csum = 0.0
    for zid, lvl in w.levels.items():
        f = _mid(meta[zid]["estimate"].get("modelledFlooded")) or 1
        wsum += f
        csum += f * lvl.certainty
    people = sum(h.people or 1 for h in w.households.values())
    flooded = sum(_mid(m["estimate"].get("modelledFlooded")) for m in meta.values())
    return {"messages": w.messages_in, "channels": w.channels, "households": len(w.households),
            "duplicatesMerged": w.duplicates, "people": people, "likelyFlooded": round(flooded),
            "certainty": round(csum / wsum, 2) if wsum else 0.0,
            "status": {k: sum(1 for h in w.households.values() if h.status == k) for k in ("open", "safe", "evacuated", "lostContact")},
            "estimatedHouseholdsAffected": round(flooded / PEOPLE_PER_HOUSEHOLD)}


def state(now_h: float, extra_messages=None, extra_plans=None, alerts=None, pulled=None) -> dict:
    geo = G.load()
    w = P.run(now_h, extra_messages, extra_plans, alerts, pulled)
    zones = {zid: zone_view(w, geo, zid) for zid in w.levels}
    acts = sorted([a for a in w.activity if a["atH"] <= now_h], key=lambda a: a["atH"])[-60:]
    out = sorted([o for o in w.outbound if o["atH"] <= now_h], key=lambda o: o["atH"])
    return {"atH": now_h, "at": P.label_time(now_h), "overall": overall(w), "zones": zones,
            "households": [h.view() for h in w.households.values()], "plans": w.plans, "activity": acts[::-1],
            "outbound": {"total": len(out), "byKind": _count(out, "kind"), "recent": out[-12:][::-1]},
            "bulletin": w.bulletin, "world": w}


def _count(rows, key):
    c = {}
    for r in rows:
        c[r[key]] = c.get(r[key], 0) + 1
    return c


@lru_cache(maxsize=1)
def timeline() -> dict:
    """The time-lapse: stops with captions, and a series every 3 hours for the charts (scenario only).
    Precomputed by `python -m api.v2.board` into v2-timeline.json; computed here if the file is missing."""
    import json
    f = G.PKG / "v2-timeline.json"
    if f.exists():
        return json.loads(f.read_text())
    return compute_timeline()


def compute_timeline() -> dict:
    series = []
    for h in range(0, P.scenario()["hours"] + 1, 3):
        w = P.run(h)
        o = overall(w)
        series.append({"atH": h, "at": P.label_time(h), "messages": o["messages"], "households": o["households"],
                       "people": o["people"], "certainty": o["certainty"], "gaugeM": (w.bulletin or {}).get("gaugeM")})
    return {"start": P.scenario()["start"], "hours": P.scenario()["hours"],
            "stops": [{"atH": h, "at": P.label_time(h), "caption": c} for h, c in STOPS], "series": series}


if __name__ == "__main__":
    import json
    (G.PKG / "v2-timeline.json").write_text(json.dumps(compute_timeline(), ensure_ascii=False))
    print("wrote", G.PKG / "v2-timeline.json")
