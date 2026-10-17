"""Volunteer pages (docs/product/v2-volunteer-pages.md): the city overview, the live feed, a zone, one family's case
and a trip plan, all read from the same world the board uses. Nothing here decides who goes where: families are
sorted by need, and teams choose by posting plans.

Privacy: everyone sees a household's zone, its dot and its needs. The exact address and the raw message text are
shown only to a team whose posted plan covers that zone; elsewhere house numbers are masked.
"""

from __future__ import annotations

import re

from api.v2 import geo as G, pipeline as P, sim as S

BOAT_M = 0.5        # boat suggested at or above this depth at the house (Earth's desk threshold, decision 0017)
DEEP_M = 1.2
HOUSE_NO = re.compile(r"(บ้านเลขที่\s*|เลขที่\s*|house\s*(?:no\.?\s*)?)\d+(?:\s*/\s*\d+)*|\b\d+\s*/\s*\d+\b", re.I)
CLOSED = ("safe", "evacuated", "nobodyThere", "atShelter")


def mask(text: str) -> str:
    return HOUSE_NO.sub(lambda m: (m.group(1) or "") + "••/•", text or "")


def unlocked(w, team: str | None, zone_id: str | None) -> bool:
    """A team sees exact addresses in the zones its own posted plans cover."""
    if not team or not zone_id:
        return False
    t = team.strip().lower()
    return any((p.get("team") or "").strip().lower() == t and zone_id in (p.get("zones") or []) for p in w.plans)


def _depth(st: dict, h) -> tuple[float, float, float, int, float] | None:
    """(depth, low, high, reports used, model depth) at the house now, cached per board state."""
    cache = st.setdefault("_depth", {})
    if h.id not in cache:
        if h.lon is None:
            cache[h.id] = None
        else:
            d, sd, n, prior = P.local_depth(st["world"], h.lon, h.lat, st["world"].now_h)
            cache[h.id] = (round(d, 2), round(max(0.0, d - sd), 2), round(d + sd, 2), n, round(prior, 2))
    return cache[h.id]


def priority(h, depth: float | None) -> int:
    if h.status in CLOSED:
        return 0
    s = 100 if h.urgent else 0
    s += 60 if h.status == "lostContact" else 0
    s += 30 if h.cannot_walk else 0
    s += 40 if getattr(h, "wants_out", False) else 0
    s += 20 if depth is not None and depth >= DEEP_M else 0
    s += 15 if h.elderly else 0
    s += 10 if h.children else 0
    return s + 1


def needs(h) -> list[str]:
    out = []
    if h.urgent and h.status not in CLOSED:
        out.append("urgent")
    if getattr(h, "wants_out", False) and h.status not in CLOSED:
        out.append("wants to leave, needs a ride")
    if h.cannot_walk:
        out.append(f"{h.cannot_walk} can't walk")
    if h.elderly:
        out.append(f"{h.elderly} elderly")
    if h.children:
        out.append(f"{h.children} {'child' if h.children == 1 else 'children'}")
    return out


def row(st: dict, h) -> dict:
    dep = _depth(st, h)
    d = dep[0] if dep else None
    w = st["world"]
    return {"id": h.id, "zoneId": h.zone_id, "lon": h.lon, "lat": h.lat, "people": h.people, "elderly": h.elderly,
            "children": h.children, "cannotWalk": h.cannot_walk, "urgent": h.urgent and h.status not in CLOSED,
            "status": h.status, "needs": needs(h), "depth": dep and {"m": dep[0], "lo": dep[1], "hi": dep[2], "reports": dep[3]},
            "boat": d is not None and d >= BOAT_M, "priority": priority(h, d), "messages": len(h.message_ids),
            "lastHeardH": h.last_heard_h, "lastHeard": P.label_time(h.last_heard_h), "hoursSilent": round(w.now_h - h.last_heard_h, 1),
            "firstHand": h.first_hand, "possibleDuplicateOf": h.possible_duplicate_of, "outcome": h.outcome,
            "shelterId": h.shelter_id,
            "reportedBy": "family" if h.first_hand else "others only"}


def _rows(st: dict, zone_id: str | None = None) -> list[dict]:
    hs = [h for h in st["world"].households.values() if zone_id is None or h.zone_id == zone_id]
    return sorted((row(st, h) for h in hs), key=lambda r: (-r["priority"], -(r["depth"] or {}).get("m", 0)))


# --- city overview ---
def overview(st: dict) -> dict:
    w = st["world"]
    zones = []
    for zid, z in st["zones"].items():
        rs = _rows(st, zid)
        open_ = [r for r in rs if r["status"] not in CLOSED]
        lf = (z["people"].get("likelyFlooded") or [0, 0])
        likely = (lf[0] + lf[1]) / 2 if lf else 0
        heard = sum(r["people"] or 1 for r in rs)
        plans = z["plans"]
        unmet = (sum(100 for r in open_ if r["urgent"]) + sum(60 for r in open_ if r["status"] == "lostContact")
                 + sum(30 for r in open_ if r["cannotWalk"]) + sum(15 for r in open_ if r["elderly"]))
        score = unmet * (0.5 if plans else 1.0) + max(0, likely - heard) * 0.2
        zones.append({
            "id": zid, "label": z.get("label"), "district": z.get("district"), "sector": z.get("sector"),
            "sectorName": z.get("sectorName"), "score": round(score),
            "open": len(open_), "urgent": sum(1 for r in open_ if r["urgent"]),
            "lostContact": sum(1 for r in open_ if r["status"] == "lostContact"),
            "cannotWalk": sum(r["cannotWalk"] for r in open_), "elderly": sum(r["elderly"] for r in open_),
            "boat": sum(1 for r in open_ if r["boat"]), "depthM": (z["level"] or {}).get("depthM"),
            "likelyFlooded": lf, "heard": heard, "plans": len(plans), "nextPlan": plans[-1] if plans else None,
            "gap": z.get("gap"), "quiet": z.get("quiet"), "predicted": z.get("predicted"),
            "closed": sum(1 for r in rs if r["status"] in CLOSED),
        })
    zones.sort(key=lambda z: -z["score"])
    sectors = []
    for sf in G.load().sectors:
        sid = sf["properties"]["id"]
        mine = [z for z in zones if z["sector"] == sid]
        sectors.append({"id": sid, "name": sf["properties"].get("name"), "zones": len(mine), "open": sum(z["open"] for z in mine),
                        "urgent": sum(z["urgent"] for z in mine), "noTeam": sum(1 for z in mine if z["open"] and not z["plans"]),
                        "boat": sum(z["boat"] for z in mine)})
    points = [{"id": h.id, "lon": h.lon, "lat": h.lat, "status": h.status, "urgent": h.urgent and h.status not in CLOSED,
               "outcome": h.outcome, "needs": needs(h), "depth": None, "zoneId": h.zone_id}
              for h in w.households.values() if h.lon is not None]
    return {"atH": w.now_h, "at": P.label_time(w.now_h), "overall": st["overall"], "zones": zones, "points": points,
            "shelters": st.get("shelters", []), "hotspots": [c for c in subareas(st) if c["need"] > 0][:10], "sectors": sectors}


# --- live feed: what the AI did with every message ---
def _messages(room_msgs: list[dict]) -> dict:
    out = {m["id"]: m for m in P.scenario()["messages"]}
    out.update({m["id"]: m for m in room_msgs})
    return out


def _facts(m: dict) -> list[dict]:
    if m.get("outcome"):
        return []
    r = m.get("_read") or P.facts_for(m)
    return [{"field": f.field, "value": f.value, "quote": f.quote} for f in r.facts]


def _reader(m: dict) -> str | None:
    r = m.get("_read") or (None if m.get("outcome") else P.facts_for(m))
    return getattr(r, "reader", None)


ACTION = {"self": "First-hand report", "reply": "Reply to a check", "relative": "Relative or friend", "post": "Public post",
          "forward": "Forwarded copy", "team": "Team visit"}


def feed(st: dict, room_msgs: list[dict], kind: str | None = None, limit: int = 80, team: str | None = None) -> dict:
    w = st["world"]
    msgs = _messages(room_msgs)
    labels = {o.message_id: o.label for o in w.obs}
    items = []
    for mid, link in w.msg_link.items():
        m = msgs.get(mid)
        if not m or m["atH"] > w.now_h:
            continue
        h = w.households.get(link["householdId"])
        facts = _facts(m)
        urgent = any(f["field"] == "urgent" and f["value"] is True for f in facts)
        how = link["how"] or "new household"
        tags = []
        if urgent:
            tags.append("urgent")
        if how.startswith("new"):
            tags.append("new")
        elif link["kind"] != "team":
            tags.append("merged")
        if labels.get(mid) == "doubtful":
            tags.append("doubtful")
        if h and h.possible_duplicate_of and how.startswith("new"):
            tags.append("possibleDuplicate")
        if h and h.status == "lostContact":
            tags.append("lostContact")
        if any(f["field"] == "neighbour" for f in facts):
            tags.append("neighbour")
        if link["kind"] == "team":
            tags.append("team")
        if kind and kind not in tags:
            continue
        show = unlocked(w, team, h.zone_id if h else None)
        items.append({"id": mid, "atH": m["atH"], "at": P.label_time(m["atH"]), "channel": m["channel"],
                      "source": ACTION.get(link["kind"], link["kind"]), "text": m["text"] if show else mask(m["text"]),
                      "householdId": link["householdId"], "zoneId": h.zone_id if h else None, "how": how, "tags": tags,
                      "facts": [{**f, "quote": f["quote"] if show else mask(f["quote"])} for f in facts if f["field"] not in ("address",)],
                      "label": labels.get(mid), "reader": _reader(m)})
    items.sort(key=lambda i: -i["atH"])
    counts = {}
    for i in items:
        for t in i["tags"]:
            counts[t] = counts.get(t, 0) + 1
    return {"atH": w.now_h, "items": items[:limit], "total": len(items), "counts": counts}


# --- one family's case ---
def case(st: dict, room_msgs: list[dict], hid: str, team: str | None = None) -> dict | None:
    w = st["world"]
    h = w.households.get(hid)
    if h is None:
        return None
    msgs = _messages(room_msgs)
    show = unlocked(w, team, h.zone_id)
    obs = {o.message_id: o for o in w.obs if o.household_id == hid}
    story = []
    for mid in h.message_ids:
        m = msgs.get(mid)
        if not m:
            continue
        link = w.msg_link.get(mid, {})
        o = obs.get(mid)
        facts = _facts(m)
        story.append({"id": mid, "atH": m["atH"], "at": P.label_time(m["atH"]), "channel": m["channel"],
                      "source": ACTION.get(link.get("kind"), link.get("kind")), "how": link.get("how"),
                      "text": m.get("text") if show else mask(m.get("text")),
                      "facts": [{**f, "quote": f["quote"] if show else mask(f["quote"])} for f in facts
                                if show or f["field"] != "address"],
                      "reader": _reader(m),
                      "depth": o and {"lo": o.lo, "hi": o.hi, "model": round(o.prior, 2), "label": o.label, "weight": o.weight}})
    story.sort(key=lambda s: s["atH"])
    dep = _depth(st, h)
    # the water at the house over time: the model, and what people said
    series = []
    if h.lon is not None:
        for k in range(0, int(w.now_h) + 1, 3):
            series.append([k, round(S.depth(h.lon, h.lat, k) or 0.0, 2)])
    reports = [[o.at_h, o.lo, o.hi, o.label] for o in obs.values()]
    doubtful = [o for o in obs.values() if o.label == "doubtful"]
    why = None
    if doubtful:
        o = doubtful[-1]
        why = (f"This family said {o.lo:.1f}–{o.hi:.1f} m at {P.label_time(o.at_h)}; the model and the reports around "
               f"them point to about {dep[0]:.1f} m. It still counts, with less weight, and the family was asked again."
               if dep else "It disagrees with the model and the reports around it.")
    links = [dict(l, toZone=w.households[l["to"]].zone_id if l["to"] in w.households else None)
             for l in w.nb_links if l["from"] == hid or l["to"] == hid]
    dupes = [x.id for x in w.households.values() if x.possible_duplicate_of == hid]
    inbox = sorted([o for o in w.outbound if o["householdId"] == hid and o["atH"] <= w.now_h], key=lambda o: o["atH"])
    replies = [s for s in story if s["channel"] == "safetyReply"]
    building = G.load().buildings.get(h.building_id) if h.building_id else None
    zone = st["zones"].get(h.zone_id) if h.zone_id else None
    plans = [p for p in w.plans if h.zone_id in (p.get("zones") or [])]
    from api.v2 import shelters as SH
    shelter_opts = SH.options(w, h.lon, h.lat) if h.lon is not None else []
    return {
        "household": row(st, h), "unlocked": show, "shelterOptions": shelter_opts,
        "shelter": SH.by_id(h.shelter_id),
        "address": (next((f["quote"] for s in story for f in s["facts"] if f["field"] == "address"), None) if show else None),
        "building": building and {"id": building.id, "outline": building.outline, "groundM": building.ground_m},
        "story": story,
        "depth": dep and {"m": dep[0], "lo": dep[1], "hi": dep[2], "reports": dep[3], "model": dep[4]},
        "depthSeries": series, "depthReports": reports, "doubtfulWhy": why,
        "neighbours": links, "possibleDuplicates": ([h.possible_duplicate_of] if h.possible_duplicate_of else []) + dupes,
        "contact": {"sent": [{**o, "at": P.label_time(o["atH"])} for o in inbox], "replies": len(replies),
                    "unanswered": h.checks_unanswered, "lastHeard": P.label_time(h.last_heard_h)},
        "zone": zone and {"id": zone["id"], "district": zone.get("district"), "level": zone.get("level"), "gap": zone.get("gap")},
        "plans": [{k: p.get(k) for k in ("id", "team", "vehicle", "seats", "eta", "offers", "at")} for p in plans],
        "now": {"atH": w.now_h, "at": P.label_time(w.now_h)},
    }


# --- a zone in depth ---
def zone(st: dict, zid: str, team: str | None = None) -> dict | None:
    w = st["world"]
    z = st["zones"].get(zid)
    if z is None:
        return None
    rs = _rows(st, zid)
    outlook = []
    for k in range(0, 7):
        surf, wet = S.zone_at(zid, w.now_h + k)
        outlook.append({"inH": k, "wetShare": round(wet, 3), "surfaceM": surf})
    open_ = [r for r in rs if r["status"] not in CLOSED]
    brief = briefing(z, open_, outlook)
    return {"zone": z, "households": rs, "outlook": outlook, "briefing": brief, "unlocked": unlocked(w, team, zid),
            "subareas": subareas(st, zid), "blocks": blocks(st, zid),
            "totals": {"open": len(open_), "people": sum(r["people"] or 1 for r in open_), "urgent": sum(1 for r in open_ if r["urgent"]),
                       "boat": sum(1 for r in open_ if r["boat"]), "closed": len(rs) - len(open_)},
            "now": {"atH": w.now_h, "at": P.label_time(w.now_h)}}


def briefing(z: dict, open_: list[dict], outlook: list[dict]) -> str:
    """A short handover a team can read before going in. Built from the numbers on the page, nothing else."""
    parts = []
    lvl = z.get("level")
    if lvl:
        trend = lvl.get("trendCmH")
        parts.append(f"Water about {lvl['depthM']:.1f} m at households (likely {lvl['depthLoM']:.1f}–{lvl['depthHiM']:.1f} m)"
                     + (f", {'rising' if trend > 1 else 'falling' if trend < -1 else 'steady'}" if trend is not None else "") + ".")
    w0, w6 = outlook[0]["wetShare"], outlook[-1]["wetShare"]
    if w6 - w0 > 0.05:
        parts.append(f"The model expects more of the zone under water in 6 hours ({w0 * 100:.0f}% → {w6 * 100:.0f}%).")
    elif w0 - w6 > 0.05:
        parts.append(f"The model expects the water to recede over the next 6 hours ({w0 * 100:.0f}% → {w6 * 100:.0f}%).")
    if open_:
        u = sum(1 for r in open_ if r["urgent"])
        cw = sum(r["cannotWalk"] for r in open_)
        lost = sum(1 for r in open_ if r["status"] == "lostContact")
        boat = sum(1 for r in open_ if r["boat"])
        parts.append(f"{len(open_)} families still at home ({sum(r['people'] or 1 for r in open_)} people)"
                     + (f", {u} urgent" if u else "") + (f", {cw} who can't walk" if cw else "")
                     + (f", {lost} not answering" if lost else "") + ".")
        if boat:
            parts.append(f"{boat} of them have water at or above {BOAT_M:.1f} m at the house: bring a boat.")
        top = open_[:3]
        parts.append("Start with " + ", ".join(f"{r['id']} ({', '.join(r['needs']) or 'no special needs'})" for r in top) + ".")
    else:
        parts.append("No family here is waiting for help right now.")
    if z.get("gap"):
        parts.append(z["gap"])
    if z.get("plans"):
        p = z["plans"][-1]
        parts.append(f"{p.get('team') or 'A team'} plans to come" + (f" about {p['eta']}" if p.get("eta") else "") + ".")
    return " ".join(parts)


# --- plan a trip ---
def trip(st: dict, zones: list[str], team: str | None = None) -> dict:
    w = st["world"]
    out = []
    for zid in zones:
        z = st["zones"].get(zid)
        if z is None:
            continue
        open_ = [r for r in _rows(st, zid) if r["status"] not in CLOSED]
        others = [{k: p.get(k) for k in ("team", "vehicle", "seats", "eta", "at")} for p in w.plans
                  if zid in (p.get("zones") or []) and (p.get("team") or "").strip().lower() != (team or "").strip().lower()]
        out.append({"id": zid, "district": z.get("district"), "depthM": (z.get("level") or {}).get("depthM"),
                    "families": open_[:30], "count": len(open_), "people": sum(r["people"] or 1 for r in open_),
                    "cannotWalk": sum(r["cannotWalk"] for r in open_), "elderly": sum(r["elderly"] for r in open_),
                    "children": sum(r["children"] for r in open_), "boat": sum(1 for r in open_ if r["boat"]),
                    "urgent": sum(1 for r in open_ if r["urgent"]), "otherTeams": others, "gap": z.get("gap")})
    total = sum(z["people"] for z in out)
    return {"zones": out, "people": total, "boatNeeded": any(z["boat"] for z in out),
            "now": {"atH": w.now_h, "at": P.label_time(w.now_h)}}


# --- blocks (data/scripts/build_v2_zoning.py): streets-bounded areas of ~150-700 people, named by their soi ---
WALK_M, TRUCK_M = 0.25, 0.6   # walk out below ankle-shin water; a high truck up to ~0.6 m; above that, a boat


def access_of(d: float | None) -> str:
    if d is None:
        return "unknown"
    return "walk" if d < WALK_M else "truck" if d < TRUCK_M else "boat"


def blocks(st: dict, zid: str | None = None, geometry: bool = True) -> list[dict]:
    """Every block with its families' need and its access now (walk / truck / boat) from the water at its buildings."""
    geo = G.load()
    w = st["world"]
    cache = st.setdefault("_blocks", {})
    if "all" not in cache:
        by_block: dict = {}
        for h in w.households.values():
            b = geo.buildings.get(h.building_id) if h.building_id else None
            if b and b.block_id:
                by_block.setdefault(b.block_id, []).append(h)
        sample: dict = {}
        for b in geo.buildings.values():
            if b.block_id and len(sample.setdefault(b.block_id, [])) < 6:
                sample[b.block_id].append(b)
        out = []
        for f in geo.blocks:
            p = f["properties"]
            hs = by_block.get(p["id"], [])
            rs = [row(st, h) for h in hs]
            open_ = [r for r in rs if r["status"] not in CLOSED]
            # where families have reported: the model corrected at their houses; elsewhere the model at a few houses
            ds = sorted(r["depth"]["m"] for r in rs if r["depth"]) or sorted(S.depth(b.lon, b.lat, w.now_h) or 0.0 for b in sample.get(p["id"], []))
            d = round(ds[len(ds) // 2], 2) if ds else None
            out.append({"id": p["id"], "zoneId": p["zoneId"], "name": p.get("name"), "people": p.get("people"),
                        "geometry": f["geometry"], "depthM": d, "access": access_of(d),
                        "open": len(open_), "urgent": sum(1 for r in open_ if r["urgent"]),
                        "lostContact": sum(1 for r in open_ if r["status"] == "lostContact"),
                        "cannotWalk": sum(r["cannotWalk"] for r in open_), "need": sum(r["priority"] for r in open_),
                        "households": [r["id"] for r in sorted(open_, key=lambda r: -r["priority"])][:12]})
        cache["all"] = out
    rows = [b for b in cache["all"] if zid is None or b["zoneId"] == zid]
    return rows if geometry else [{k: v for k, v in b.items() if k != "geometry"} for b in rows]


def subareas(st: dict, zid: str | None = None) -> list[dict]:
    """The blocks, most help missing first (kept under the old name for the pages that list them)."""
    return sorted(blocks(st, zid, geometry=False), key=lambda b: -b["need"])
