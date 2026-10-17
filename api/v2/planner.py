"""Planner: decides whom to ask what, whom to warn first, and who has gone quiet. Writes the outreach list and logs
each decision. It never assigns work to volunteers; it only informs.
"""

from __future__ import annotations

from api.v2 import geo as G
from api.v2.messages import plan_update, say

PEOPLE_PER_HOUSEHOLD = 2.72  # DOPA, Hat Yai


def _mid(r):
    return (r[0] + r[1]) / 2 if r else 0


def check_times(after_h: float, until_h: float, start_hour: int = 6) -> list[float]:
    """Scheduled safety checks (07:00 and 19:00) strictly after one time and up to another."""
    out = []
    h = int(after_h) + 1
    while h <= until_h:
        if (h + start_hour) % 24 in (7, 19):
            out.append(h)
        h += 1
    return out


def zone_meta(geo: G.Geo) -> dict:
    return {z["properties"]["id"]: z["properties"] for z in geo.zones}


def plan_outreach(w, geo: G.Geo) -> None:
    from api.v2.pipeline import label_time, satellite_by_zone
    meta = zone_meta(geo)
    now = w.now_h
    w.quiet, w.predicted, w.gaps, w.disagree = [], [], {}, {}

    # lost contact: two scheduled checks with no reply
    for hh in w.households.values():
        if not hh.first_hand or hh.status in ("safe", "evacuated") or hh.outcome:
            continue
        missed = check_times(hh.last_heard_h, now)
        hh.checks_unanswered = len(missed)
        for t in missed:
            w.outbound.append({"atH": t, "householdId": hh.id, "kind": "check", "text": say("check")})
        if len(missed) >= 2 and hh.status != "lostContact":
            hh.status = "lostContact"
            w.activity.append({"atH": missed[1], "at": label_time(missed[1]), "agent": "Planner",
                               "text": f"{hh.id} in {hh.zone_id} missed two safety checks → lost contact. AI voice call queued.",
                               "tool": "check schedule", "ref": hh.id, "key": "lost"})
            w.outbound.append({"atH": missed[1] + 0.25, "householdId": hh.id, "kind": "lostCall", "text": say("lostCall")})

    # prediction and early warning from the gauge
    from api.v2 import sim as S
    b = w.bulletin
    if b and b.get("gaugeM") and b["gaugeM"] > 7.0 and (b.get("rateMh") or 0) > 0.01:
        for zid in w.levels:
            _, wet_now = S.zone_at(zid, now)
            _, wet_next = S.zone_at(zid, now + 6)
            if wet_next - wet_now >= 0.08 and wet_next >= 0.15:
                w.predicted.append(zid)
        if w.predicted:
            vulnerable = [h for h in w.households.values() if h.zone_id in w.predicted and (h.elderly or h.cannot_walk or h.children)]
            w.activity.append({"atH": b["atH"], "at": label_time(b["atH"]), "agent": "Analyst",
                               "text": f"Flood simulation: water spreading into {', '.join(w.predicted)} within about 6 hours "
                                       f"(gauge X.44 rising, terrain). Early warning to {len(vulnerable)} vulnerable households first.",
                               "tool": "flood simulation · gauge · terrain", "ref": None, "key": "predict"})
            for h in vulnerable:
                w.outbound.append({"atH": b["atH"] + 0.1, "householdId": h.id, "kind": "earlyWarning", "text": say("earlyWarning")})

    # doubtful reports: one check question each
    asked = set()
    for o in w.obs:
        if o.label == "doubtful" and o.household_id and o.household_id not in asked and o.source in ("self", "reply"):
            asked.add(o.household_id)
            w.outbound.append({"atH": o.at_h + 0.1, "householdId": o.household_id, "kind": "askBack", "text": say("askBack")})
    if asked:
        w.activity.append({"atH": now, "at": label_time(now), "agent": "Planner",
                           "text": f"{len(asked)} reports don't fit the water around them. One check question sent to each "
                                   f"(\"above or below your door handle?\").", "tool": "zone levels", "ref": None, "key": "askBack"})

    # quiet zones: many people likely flooded, few heard from
    flooding = bool(b and (b.get("gaugeM") or 0) > 7.4)
    for zid, lvl in (w.levels.items() if flooding else ()):
        est = meta[zid]["estimate"]
        flooded = _mid(est.get("modelledFlooded"))
        people = sum((h.people or 1) for h in w.households.values() if h.zone_id == zid)
        if flooded > 1500 and people / flooded < 0.004 and (lvl.certainty < 0.35):
            w.quiet.append(zid)
    if w.quiet:
        targets = [h for h in w.households.values() if h.zone_id in w.quiet and h.first_hand][:6]
        for h in targets:
            w.outbound.append({"atH": now, "householdId": h.id, "kind": "quiet", "text": say("quiet")})
        w.activity.append({"atH": now, "at": label_time(now), "agent": "Planner",
                           "text": f"Quiet zones {', '.join(w.quiet)}: many people likely flooded, few reports. Asking "
                                   f"{len(targets)} households there about the streets around them.", "tool": "map certainty",
                           "ref": None, "key": "quiet"})

    # plans: tell households in each zone; post a gap when nobody plans what is needed
    for p in w.plans:
        told = 0
        blocks = set(p.get("blocks") or [])
        block_zones = {b.split("·")[0] for b in blocks}
        for z in p.get("zones", []):
            for h in w.households.values():
                if h.zone_id == z and h.status not in ("evacuated", "atShelter"):
                    if z in block_zones:  # the plan names streets in this zone: tell only the families on them
                        bl = geo.buildings.get(h.building_id) if h.building_id else None
                        if not bl or bl.block_id not in blocks:
                            continue
                    w.outbound.append({"atH": p["atH"], "householdId": h.id, "kind": "planUpdate", "text": plan_update(p, z),
                                       "team": p.get("team") or (p.get("_parsed") or {}).get("team")})
                    told += 1
        p["told"] = told
        w.activity.append({"atH": p["atH"], "at": p["at"], "agent": "Notifier",
                           "text": f"Plan from {p.get('team') or 'a team'} ({', '.join(p.get('zones', []))}"
                                   + (f"; streets: {len(blocks)} blocks" if blocks else "") + 
                                   f"{', ' + p['eta'] if p.get('eta') else ''}): {told} households told.",
                           "tool": "plan line · message", "ref": p["id"], "key": "plan"})
    for zid in w.levels:
        need_med = sum(h.cannot_walk for h in w.households.values() if h.zone_id == zid and h.status == "open")
        has_med = any(zid in p.get("zones", []) and p.get("offers") in ("medical", "medical evacuation") for p in w.plans)
        if need_med and not has_med:
            w.gaps[zid] = f"Nobody plans medical help. {need_med} {'person' if need_med == 1 else 'people'} can't walk."

    # rain alerts: the flood model's expected rise at each house; warn those it affects, most in need first
    from api.v2 import rain as RN
    for a in [a for a in getattr(w, "alerts", []) if a["kind"] == "rain" and RN.load()]:
        rows = []
        for h in w.households.values():
            if h.status not in ("open", "lostContact", "toShelter") or h.lon is None:
                continue
            r = RN.rise(h.lon, h.lat)
            if r and r[0] >= RN.WARN_M:
                need = (3 if h.cannot_walk else 0) + (2 if h.elderly else 0) + (1 if h.children else 0) + (2 if h.urgent else 0)
                rows.append((need, r[0], r[1], h))
        rows.sort(key=lambda x: (-x[0], -x[1]))
        for i, (need, m, lag, h) in enumerate(rows):
            advice_th = ("ถ้าในบ้านมีคนเดินไม่ได้ ตอบ 2 แล้วเราจะแจ้งทีมเรือให้มารับก่อน" if h.cannot_walk
                         else "ถ้าออกได้ ให้ไปศูนย์พักพิงตอนนี้ ก่อนน้ำขึ้น ถ้าออกไม่ได้ ขึ้นที่สูงไว้ก่อน")
            text = say("rainRise", mm=int(RN.FORECAST_MM), cm=int(round(m * 100 / 5) * 5), h=max(1, lag), advice=advice_th)
            w.outbound.append({"atH": a["atH"], "order": i, "householdId": h.id, "kind": "rainRise", "text": text,
                               "riseM": round(m, 2), "inH": lag})
        top = max(rows, key=lambda x: x[1]) if rows else None
        w.activity.append({"atH": a["atH"], "at": label_time(a["atH"]), "agent": "Planner",
                           "text": f"Rain forecast {int(RN.FORECAST_MM)} mm in 6 h: the flood model expects at least {int(RN.WARN_M * 100)} cm more "
                                   f"water at {len(rows)} homes" + (f", up to {top[1] * 100:.0f} cm in {top[3].zone_id} after about {top[2]} h" if top else "")
                                   + f". Warned them first by need: {sum(1 for r in rows if r[3].cannot_walk)} with someone who can't walk, "
                                   f"{sum(1 for r in rows if r[3].elderly)} with elderly people.",
                           "tool": "flood model · extra-rain response · message", "ref": None, "key": "rainRise"})

    # river alerts from the demo clock: a safety check to every household in the zones at risk
    for a in [a for a in getattr(w, "alerts", []) if a["kind"] != "rain" or not RN.load()]:
        zones = [z for z, l in w.levels.items() if l.wse_m is not None] + list(w.predicted)
        told = [h for h in w.households.values() if h.zone_id in zones and h.status in ("open", "lostContact")]
        for h in told:
            # one warning of a kind per home every 3 hours, however many times the alert is raised
            if any(o["householdId"] == h.id and o["kind"] == a["kind"] and abs(o["atH"] - a["atH"]) < 3 for o in w.outbound):
                continue
            w.outbound.append({"atH": a["atH"], "householdId": h.id, "kind": a["kind"], "text": say(a["kind"])})
        w.activity.append({"atH": a["atH"], "at": label_time(a["atH"]), "agent": "Notifier",
                           "text": f"{'Rain' if a['kind'] == 'rain' else 'River'} alert: safety check sent to {len(told)} households in "
                                   f"{len(set(zones))} zones.", "tool": "forecast · message", "ref": None, "key": a["kind"]})

    # satellite against reports
    for sp in satellite_by_zone()["passes"]:
        if sp["atH"] > now:
            continue
        from api.v2.level import estimate
        for zid in w.levels:
            share = sp["share"].get(zid, 0)
            all_obs, bad = w.zone_obs.get(zid, ([], set()))
            lvl = estimate(all_obs, sp["atH"] + 3, exclude=bad)  # reports around the time of the pass
            d = lvl.depth_at(_ground_p50(geo, zid)) if lvl.wse_m is not None else None
            if d and d[0] >= 0.5 and share < 0.15 and lvl.n >= 3:
                w.disagree[zid] = (f"Satellite ({sp['at'][:10]}) shows little water, but {lvl.n} reports put it near "
                                   f"{d[0]:.1f} m. Radar misses water between buildings ({round(meta[zid].get('noSatelliteDataShare', 0) * 100)}% "
                                   f"of this zone is dense built-up), so reports win here.")
        w.activity.append({"atH": sp["atH"], "at": label_time(sp["atH"]), "agent": "Supervisor",
                           "text": f"New Sentinel-1 pass ({sp['at'][:10]}): Earth Engine flood extent compared with every zone.",
                           "tool": "earth engine · sentinel-1", "ref": sp["file"], "key": "satellite"})


_P50 = {}


def _ground_p50(geo: G.Geo, zid: str) -> float:
    if zid not in _P50:
        g = sorted(b.ground_m for b in geo.buildings.values() if b.zone_id == zid and b.ground_m is not None)
        _P50[zid] = g[len(g) // 2] if g else 0.0
    return _P50[zid]
