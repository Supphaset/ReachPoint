"""The v2 pipeline: every message up to a moment → households, water levels, labels, plans, outreach and the AI
activity log. Deterministic and fast (it replays the whole scenario in well under a second), so the board can be
computed for any point on the time-lapse.

Steps per message, in time order (the agents in docs/product/v2-spec.md §4):
    Reader     facts with quotes (Gemini facts when cached or live; rules otherwise)
    Locator    pin → building (address precision) or candidate buildings (landmark precision); neighbour words → building
    Dedupe     same household? building or phone = sure; nearby + same makeup = probably; forwarded text = duplicate
    Analyst    depth words → water-surface observation with a weight; zone levels; labels; satellite and bulletin evidence
    Planner    check questions for doubtful or vague reports; quiet-zone questions; early warnings; lost contact
    Notifier   the outbound messages (text from api/v2/messages.py)
"""

from __future__ import annotations

import json
import math
from bisect import bisect_left, bisect_right
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from api.v2 import geo as G
from api.v2 import sim as S
from api.v2 import assim as A
from api.v2.level import Level, Obs, estimate
from api.v2.reader import Read, read_rules

PKG = G.PKG
CHECK_HOURS = (7, 19)
LOCAL_M = 400.0  # reports this close share roughly one water surface
POST_MATCH_M = {"landmark": 250, "area": 400}  # how far a post pinned to a landmark or an area may sit from the house
SOURCE_WEIGHT = {"self": 1.0, "reply": 1.0, "neighbour": 0.7, "relative": 0.5, "post": 0.5, "forward": 0.2}
PRECISION_WEIGHT = {"address": 1.0, "landmark": 0.6, "area": 0.3}
SATELLITE_PASSES = [("2025-11-24T06:03+07:00", "extent-2025-11-23-o164.geojson"),   # file names keep the UTC date
                    ("2025-11-30T06:01+07:00", "extent-2025-11-29-o164.geojson")]


@dataclass
class Household:
    id: str
    building_id: str | None
    zone_id: str | None
    lon: float
    lat: float
    precision: str
    people: int | None = None
    elderly: int = 0
    children: int = 0
    cannot_walk: int = 0
    urgent: bool = False
    status: str = "open"            # open, safe, evacuated, lostContact
    first_hand: bool = False
    reported_by_others_only: bool = True
    message_ids: list[str] = field(default_factory=list)
    possible_duplicate_of: str | None = None
    first_at_h: float = 0.0
    last_heard_h: float = 0.0
    last_depth: list[float] | None = None
    phone_key: str | None = None
    checks_unanswered: int = 0
    outcome: dict | None = None     # a team's one tap: {"kind": "pickedUp" | "nobodyThere", "team", "atH"}

    def view(self):
        return {"id": self.id, "buildingId": self.building_id, "zoneId": self.zone_id, "lon": self.lon, "lat": self.lat,
                "precision": self.precision, "people": self.people, "elderly": self.elderly, "children": self.children,
                "cannotWalk": self.cannot_walk, "urgent": self.urgent, "status": self.status, "firstHand": self.first_hand,
                "reportedByOthersOnly": self.reported_by_others_only, "messages": len(self.message_ids),
                "possibleDuplicateOf": self.possible_duplicate_of, "lastDepth": self.last_depth,
                "firstAtH": self.first_at_h, "lastHeardH": self.last_heard_h, "outcome": self.outcome}


@dataclass
class Observation:
    id: str
    message_id: str
    household_id: str | None
    zone_id: str
    at_h: float
    ground_m: float
    lo: float
    hi: float
    weight: float
    source: str
    quote: str
    label: str = "unconfirmed"
    x: float = 0.0
    y: float = 0.0
    sim_wse: float | None = None   # what the physics says the water surface is here, then
    prior: float = 0.0             # the model's depth here, then


@dataclass
class World:
    """Everything the agents know at one moment."""
    now_h: float
    households: dict[str, Household] = field(default_factory=dict)
    obs: list[Observation] = field(default_factory=list)
    activity: list[dict] = field(default_factory=list)
    outbound: list[dict] = field(default_factory=list)
    plans: list[dict] = field(default_factory=list)
    bulletin: dict | None = None
    messages_in: int = 0
    channels: dict = field(default_factory=dict)
    duplicates: int = 0
    by_building: dict = field(default_factory=dict)
    by_phone: dict = field(default_factory=dict)
    texts: dict = field(default_factory=dict)
    threads: dict = field(default_factory=dict)
    msg_link: dict = field(default_factory=dict)    # message id → {"householdId", "how", "kind"}: why it joined
    nb_links: list = field(default_factory=list)    # neighbour reports: who reported which house, which way


@lru_cache(maxsize=1)
def scenario() -> dict:
    return json.loads((PKG / "v2-scenario.json").read_text())


@lru_cache(maxsize=1)
def cached_facts() -> dict:
    """Gemini's facts for the scenario messages, from the batch run (api/scripts/v2_batch_read.py), if present."""
    p = PKG / "v2-facts.json"
    return json.loads(p.read_text())["facts"] if p.exists() else {}


@lru_cache(maxsize=1)
def satellite_by_zone() -> dict:
    """For each satellite pass, the share of each zone's buildings inside the mapped flood extent."""
    geo = G.load()
    out = []
    for at, fname in SATELLITE_PASSES:
        p = PKG / fname
        if not p.exists():
            continue
        polys = []
        for f in json.loads(p.read_text())["features"]:
            g = f["geometry"]
            for poly in ([g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]):
                ring = [tuple(c) for c in poly[0]]
                xs, ys = [c[0] for c in ring], [c[1] for c in ring]
                polys.append((min(xs), min(ys), max(xs), max(ys), ring))
        counts: dict[str, list[int]] = {}
        for b in list(geo.buildings.values())[::5]:
            hit = any(x0 <= b.lon <= x1 and y0 <= b.lat <= y1 and G._inside((b.lon, b.lat), ring) for x0, y0, x1, y1, ring in polys)
            c = counts.setdefault(b.zone_id, [0, 0])
            c[0] += hit
            c[1] += 1
        out.append({"at": at, "atH": hours(at), "file": fname, "share": {z: round(a / n, 2) for z, (a, n) in counts.items()}})
    return {"passes": out}


def hours(iso: str) -> float:
    from datetime import datetime
    return (datetime.fromisoformat(iso) - datetime.fromisoformat(scenario()["start"])).total_seconds() / 3600


def label_time(h: float) -> str:
    from datetime import datetime, timedelta
    t = datetime.fromisoformat(scenario()["start"]) + timedelta(hours=h)
    return t.strftime("%d %b %H:%M")


_READS: dict = {}
_CHECKED: dict = {}  # observation id -> (doubtful, expectation), for settled scenario reports
_SNAPS: dict = {}


def facts_for(msg: dict) -> Read:
    if not msg.get("live") and msg["id"] in _READS:
        return _READS[msg["id"]]
    r = _facts_for(msg)
    if not msg.get("live"):
        _READS[msg["id"]] = r
    return r


def _facts_for(msg: dict) -> Read:
    cached = cached_facts().get(msg["id"])
    if cached:
        from api.v2.reader import Fact, normalise
        facts = []
        for f in cached["facts"]:
            v = normalise(f["field"], f["value"])
            if v is not None and not (f["field"] in ("urgent", "forwarded") and v is False):
                facts.append(Fact(f["field"], v, f["quote"]))
        from api.v2.ai import ADD_BACK
        have = {f.field for f in facts}
        facts += [f for f in read_rules(msg["text"], msg.get("channel", "chat")).facts if f.field in ADD_BACK and f.field not in have]
        return Read(facts, reader=cached.get("reader", "model"))
    return read_rules(msg["text"], msg.get("channel", "chat"))


def _log(w: World, agent: str, text: str, tool: str, at_h: float, ref=None, key=None):
    w.activity.append({"atH": round(at_h, 2), "at": label_time(at_h), "agent": agent, "text": text, "tool": tool, "ref": ref, "key": key})


def _new_household(w: World, b, lon, lat, precision, at_h, zone_id=None) -> Household:
    hid = f"HH{len(w.households) + 1:03d}"
    hh = Household(hid, b.id if b else None, zone_id or (b.zone_id if b else None), lon, lat, precision, first_at_h=at_h, last_heard_h=at_h)
    w.households[hid] = hh
    if b and precision == "address":
        w.by_building[b.id] = hid
    return hh


def _merge_people(hh: Household, r: Read, first_hand: bool):
    p = r.get("people")
    if p and (first_hand or hh.people is None):
        hh.people = max(p, hh.elderly + hh.children) if first_hand else p
    for k, attr in (("elderly", "elderly"), ("children", "children"), ("cannotWalk", "cannot_walk")):
        v = r.get(k)
        if v and (first_hand or not getattr(hh, attr)):
            setattr(hh, attr, int(v))
    if r.get("urgent"):
        hh.urgent = True


def _same_family(r: Read, cand: "Household", strict: bool = False) -> bool:
    p = r.get("people")
    if p is not None and cand.people is not None and p != cand.people:
        return False
    if strict:
        if p is None or cand.people is None:
            return False
        # the whole makeup must match: who is elderly, children, who can't walk
        for k, attr in (("elderly", "elderly"), ("children", "children"), ("cannotWalk", "cannot_walk")):
            if int(r.get(k) or 0) != int(getattr(cand, attr) or 0):
                return False
        return True
    if bool(r.get("cannotWalk")) != bool(cand.cannot_walk) and r.get("cannotWalk") is not None and cand.people is not None:
        return False
    c = r.get("children")
    if c and cand.children and c != cand.children:
        return False
    return True


def _posted_about(w: World, pin: dict, zone_id: str, r: Read):
    """A family's own report after a relative posted about them: adopt that household only if exactly one fits."""
    x, y = G.to_m(pin["lon"], pin["lat"])
    fits = []
    for h in w.households.values():
        if h.zone_id != zone_id or h.first_hand or h.precision == "address":
            continue
        hx, hy = G.to_m(h.lon, h.lat)
        if math.hypot(hx - x, hy - y) <= POST_MATCH_M.get(h.precision, 150) and _same_family(r, h, strict=True):
            fits.append(h)
    return fits[0] if len(fits) == 1 else None


def _near_first_hand(w: World, pin: dict, zone_id: str, r_m: float):
    x, y = G.to_m(pin["lon"], pin["lat"])
    best = None
    for h in w.households.values():
        if h.zone_id == zone_id and h.first_hand and h.lon is not None:
            hx, hy = G.to_m(h.lon, h.lat)
            d = math.hypot(hx - x, hy - y)
            if d <= r_m and (best is None or d < best[0]):
                best = (d, h)
    return best[1] if best else None


def _outcome(w: World, msg: dict):
    """A team's one tap on a case: picked up, or nobody there. The family's phone is told."""
    hh = w.households.get(msg.get("householdHint") or "")
    if hh is None:
        return
    kind, team, at = msg["outcome"], msg.get("team") or "A team", msg["atH"]
    hh.outcome = {"kind": kind, "team": team, "atH": at, "at": label_time(at)}
    hh.status = "evacuated" if kind == "pickedUp" else "nobodyThere"
    if kind == "pickedUp":
        hh.urgent = False
    hh.message_ids.append(msg["id"])
    w.msg_link[msg["id"]] = {"householdId": hh.id, "how": "team visit", "kind": "team"}
    from api.v2.messages import say
    w.outbound.append({"atH": at, "householdId": hh.id, "kind": kind, "text": say(kind, team=team)})
    _log(w, "Team", f"{team}: {'picked up' if kind == 'pickedUp' else 'nobody there at'} {hh.id} ({hh.zone_id}).",
         "volunteer tap", at, msg["id"], kind)


def _way(side: str | None) -> str:
    return f"{side} of" if side in G.DIRECTIONS else "nearest to"


def process(w: World, msg: dict, geo: G.Geo, live: bool = False):
    at = msg["atH"]
    w.messages_in += 1
    w.channels[msg["channel"]] = w.channels.get(msg["channel"], 0) + 1
    if msg["channel"] == "bulletin":
        t = msg.get("truth") or {}
        w.bulletin = {"atH": at, "text": msg["text"], "gaugeM": t.get("gaugeM"), "rateMh": t.get("rateMh")}
        if t.get("gaugeM") and t["gaugeM"] > 7.4 and (t.get("rateMh") or 0) > 0:
            _log(w, "Reader", f"Bulletin read: gauge X.44 at {t['gaugeM']:.2f} m, over the 7.40 m bank and rising "
                              f"{t['rateMh'] * 100:.0f} cm/h.", "gemini · read bulletin", at, msg["id"], "bulletin")
        return
    if msg.get("outcome"):
        _outcome(w, msg)
        return
    r = msg.get("_read") or facts_for(msg)
    kind = "self" if msg["channel"] in ("chat", "voice") else ("reply" if msg["channel"] == "safetyReply" else "post")
    if r.get("about") == "relative":
        kind = "relative"
    base = " ".join(msg["text"].replace("ส่งต่อ:", "").split())
    if r.get("forwarded") or (kind != "reply" and base in w.texts):
        kind = "forward"
    pin = msg.get("pin") or {}
    precision = pin.get("precision", "area")
    key = (pin.get("lon"), pin.get("lat"), precision) if pin else None
    if key in _SNAPS:
        b = _SNAPS[key]
    else:
        b = geo.snap(pin["lon"], pin["lat"], 40 if precision == "address" else 120) if pin else None
        if key:
            _SNAPS[key] = b

    # --- Locator + Dedupe: whose message is this?
    hh = None
    how = None
    if msg.get("householdHint") and msg["householdHint"] in w.households:
        hh, how = w.households[msg["householdHint"]], "same conversation"
    elif msg.get("thread") and msg["thread"] in w.threads:
        hh, how = w.households[w.threads[msg["thread"]]], "reply in the same conversation"
    elif kind == "forward" and base in w.texts:
        hh, how = w.households.get(w.texts[base]), "forwarded copy of an earlier post"
        w.duplicates += 1
    elif b and precision == "address" and b.id in w.by_building:
        hh, how = w.households[w.by_building[b.id]], "same building"
    elif b and precision == "address" and kind in ("self", "reply") and (post := _posted_about(w, pin, b.zone_id, r)):
        hh, how = post, "the family a relative posted about earlier"
        w.duplicates += 1
    elif msg.get("phoneKey") and msg["phoneKey"] in w.by_phone:
        hh, how = w.households[w.by_phone[msg["phoneKey"]]], "same phone"
    elif b and precision != "address":
        # a post near a known household with the same makeup is probably the same family
        x, y = G.to_m(pin["lon"], pin["lat"])
        matches = []
        for cand in w.households.values():
            if cand.zone_id != b.zone_id or cand.lon is None:
                continue
            d = math.hypot(*(a - c for a, c in zip(G.to_m(cand.lon, cand.lat), (x, y))))
            if d <= POST_MATCH_M.get(precision, 150) and _same_family(r, cand, strict=True):
                matches.append((d, cand))
        matches.sort(key=lambda m: m[0])
        if len(matches) == 1:
            hh, how = matches[0][1], "probably the same family: nearby, same people"
            w.duplicates += 1
        elif matches:
            possible = matches[0][1].id  # several families fit: keep it separate, count it as a range
    if hh is None:
        hh = _new_household(w, b, pin.get("lon"), pin.get("lat"), precision, at)
        how = "new household" + (" (possibly the same as " + possible + ")" if kind not in ("self", "reply") and "possible" in locals() else "")
        if kind not in ("self", "reply") and "possible" in locals():
            hh.possible_duplicate_of = possible
        if kind in ("self", "reply"):
            hh.first_hand = True
        if live or (kind == "self" and len(w.households) % 9 == 0):
            _log(w, "Locator", f"New household {hh.id} in {hh.zone_id}" + (f", pinned to a building ({precision})" if b else ""),
                 "pinpoint · building outlines", at, msg["id"], "new")
    else:
        if kind in ("relative", "post", "forward") and how and (live or w.duplicates % 6 == 1):
            _log(w, "Dedupe", f"Merged a {msg['channel']} into {hh.id}: {how}. Count unchanged.", "building index · compare", at, msg["id"], "merge")
    first_hand = kind in ("self", "reply")
    if first_hand:
        hh.first_hand = True
        hh.reported_by_others_only = False
        if hh.building_id is None and b and precision == "address":
            hh.building_id, hh.lon, hh.lat, hh.precision = b.id, pin["lon"], pin["lat"], "address"
            w.by_building[b.id] = hh.id
    if msg.get("phoneKey"):
        hh.phone_key = msg["phoneKey"]
        w.by_phone[msg["phoneKey"]] = hh.id
    hh.message_ids.append(msg["id"])
    w.msg_link[msg["id"]] = {"householdId": hh.id, "how": how, "kind": kind}
    if kind == "self":
        w.threads.setdefault(msg["id"], hh.id)
    hh.last_heard_h = at
    if kind == "reply":
        hh.checks_unanswered = 0
    if kind != "forward":
        w.texts.setdefault(base, hh.id)
    _merge_people(hh, r, first_hand)
    safe = r.get("safe")
    if hh.outcome:
        pass  # a team was there: its tap stands over later messages
    elif safe == "evacuated":
        hh.status = "evacuated"
    elif safe and not r.get("urgent"):
        hh.status = "safe" if (r.get("depthRange") or [0, 0])[0] < 1.0 else "open"
    elif hh.status == "lostContact" or r.get("urgent"):
        hh.status = "open"

    # --- neighbour words → building → known or new household
    nb = r.get("neighbour")
    if nb and nb.get("side") not in G.DIRECTIONS and kind not in ("self", "reply"):
        nb = None  # "my neighbour, a family of 5" in a post is about that family itself, like a relative's post
    if nb and b:
        side = nb.get("side")
        nbid, sure = geo.neighbour_on(b, side)
        if nbid:
            known = w.by_building.get(nbid)
            if known:
                _log(w, "Locator", f"\"{r.quote('neighbour')}\" → the building {_way(side)} {hh.id}: already household "
                                   f"{known}. Count unchanged.", "compass direction · building outlines", at, msg["id"], "neighbourKnown")
                nh = w.households[known]
                if nb.get("elderly") and not nh.elderly:
                    nh.elderly = nb["elderly"]
            else:
                nbld = geo.buildings[nbid]
                nh = _new_household(w, nbld, nbld.lon, nbld.lat, "address", at)
                nh.people = nb.get("people")
                nh.elderly = nb.get("elderly", 0)
                nh.children = nb.get("children", 0)
                _log(w, "Locator", f"\"{r.quote('neighbour')}\" → the building {_way(side)} {hh.id}: nobody had reported. "
                                   f"New household {nh.id}, reported by a neighbour.", "compass direction · building outlines", at, msg["id"], "neighbourNew")
            w.nb_links.append({"from": hh.id, "to": known or nh.id, "side": side, "sure": sure, "messageId": msg["id"],
                               "atH": at, "quote": r.quote("neighbour"), "known": bool(known)})
            msg.setdefault("_effects", {})["neighbour"] = {"side": side, "known": bool(known), "householdId": known or nh.id,
                                                           "buildingId": nbid, "sure": sure}

    # --- Analyst: a depth observation
    d = r.get("depthRange")
    if d and hh.zone_id:
        ground = b.ground_m if (b and b.ground_m is not None) else None
        if ground is None:
            continue_ground = [n.ground_m for n in geo.near(*G.to_m(pin["lon"], pin["lat"]), 120) if n.ground_m is not None][:20]
            ground = sorted(continue_ground)[len(continue_ground) // 2] if continue_ground else None
        if ground is not None:
            wt = SOURCE_WEIGHT[kind] * PRECISION_WEIGHT.get(precision, 0.3)
            ox, oy = G.to_m(pin["lon"], pin["lat"])
            sd = S.depth(pin["lon"], pin["lat"], at)
            o = Observation(f"O{len(w.obs) + 1}", msg["id"], hh.id, hh.zone_id, at, ground, d[0], d[1], round(wt, 2), kind,
                            r.quote("depthRange") or "", x=ox, y=oy,
                            sim_wse=None if sd is None or sd < 0.05 else ground + sd, prior=sd or 0.0)
            if kind == "forward":
                o.at_h = msg.get("truth", {}).get("staleFromH", at - 24) if not live else at
            w.obs.append(o)
            hh.last_depth = d


def local_depth(w: World, lon: float, lat: float, at_h: float) -> tuple[float, float, int, float]:
    """(most likely depth, its standard deviation, reports used, model depth) at a point: the flood model corrected
    by the reports around it (api/v2/assim.py)."""
    prior = S.depth(lon, lat, at_h) or 0.0
    idx = getattr(w, "assim_index", None)
    if idx is None:
        return round(prior, 2), A.SB, 0, round(prior, 2)
    x, y = G.to_m(lon, lat)
    d, sd, n = A.analyse(idx, x, y, at_h, prior)
    return round(d, 2), round(sd, 2), n, round(prior, 2)


def local_level(w: World, x: float, y: float, at_h: float, r_m: float = LOCAL_M, pool: list | None = None) -> Level:
    """Water surface at a point (for callers that work in surfaces): ground + local_depth, with a +-1 sd range."""
    lon, lat = G.to_ll(x, y)
    geo = G.load()
    b = _SNAPS.get((round(lon, 6), round(lat, 6), "local"))
    if b is None:
        b = _SNAPS[(round(lon, 6), round(lat, 6), "local")] = geo.snap(lon, lat, 40)
    if b is None or b.ground_m is None:
        return Level(None, None, None)
    d, sd, n, _ = local_depth(w, lon, lat, at_h)
    if n == 0 and d < 0.05:
        return Level(None, None, None)
    return Level(round(b.ground_m + d, 2), round(b.ground_m + max(0.0, d - sd), 2), round(b.ground_m + d + sd, 2), n, float(n), [], None, 0.0)


def estimate_around(obs: list[Obs], at_h: float) -> Level:
    """The level the other reports point to around one moment (no freshness: reports either side count alike)."""
    if not obs:
        return Level(None, None, None)
    return estimate([Obs(o.id, at_h, o.ground_m, o.lo_m, o.hi_m, o.base_weight) for o in obs], at_h)


def w_burst(o) -> bool:
    return bool(getattr(o, "burst", False))


def assimilate(w: World) -> None:
    """Check every report against the model and the reports around it, then index them for local estimates."""
    obs = []
    for o in w.obs:
        if o.at_h > w.now_h or o.source == "forward":  # a forwarded copy adds no independent evidence
            continue
        obs.append(A.Ob(o.message_id, o.x, o.y, o.at_h, o.lo, o.hi, o.source, o.prior))  # keyed by message: stable across runs
    # a report's verdict depends only on reports within CHECK_H of it, so once those are all in the past it is final
    settled = {o.message_id for o in w.obs if not o.message_id.startswith("L") and not w_burst(o) and o.at_h < w.now_h - A.CHECK_H}
    known = {k: v for k, v in _CHECKED.items() if k in settled}
    expect = A.check(obs, known=known)
    for a in obs:
        if a.id in settled and a.id not in _CHECKED:
            _CHECKED[a.id] = (a.doubtful, expect[a.id])
    by = {a.id: a for a in obs}
    for o in w.obs:
        a = by.get(o.message_id)
        if a is None:
            o.label = "unchecked"
        elif a.doubtful:
            o.label = "doubtful"
        else:
            e, sd, n = expect.get(o.message_id, (None, None, 0))
            o.label = "consistent" if (n >= 2 and o.source in ("self", "reply") and abs(a.mid - e) <= max(0.4, 1.5 * a.sigma)) else "unchecked"
    w.assim_index = A.Index(obs)


def zone_levels(w: World, geo: G.Geo) -> dict[str, Level]:
    assimilate(w)
    out = {}
    by_zone: dict[str, list[Observation]] = {}
    for o in w.obs:
        by_zone.setdefault(o.zone_id, []).append(o)
    for z in geo.zones:
        zid = z["properties"]["id"]
        os_ = sorted(by_zone.get(zid, []), key=lambda o: o.at_h)
        all_obs = [Obs(o.id, o.at_h, o.ground_m, o.lo, o.hi, o.weight) for o in os_]
        bad = {o.id for o in os_ if o.label == "doubtful"}
        lvl = estimate(all_obs, w.now_h, exclude=bad)
        lvl.doubtful = sorted(bad & {o.id for o in os_ if w.now_h - 12 <= o.at_h <= w.now_h})
        out[zid] = lvl
        w.zone_obs = getattr(w, "zone_obs", {})
        w.zone_obs[zid] = (all_obs, bad)
    return out


def plans_until(w: World, now_h: float, extra: list[dict] | None = None):
    from api.v2.plans import parse_plan
    for p in scenario()["plans"] + (extra or []):
        if p["atH"] <= now_h:
            parsed = p.get("_parsed") or parse_plan(p["text"])
            w.plans.append({"id": p["id"], "atH": p["atH"], "at": label_time(p["atH"]), "text": p["text"], **parsed})


def run(now_h: float, extra_messages: list[dict] | None = None, extra_plans: list[dict] | None = None,
        alerts: list[dict] | None = None, pulled: dict | None = None) -> World:
    """The world at now_h. `pulled` moves some scenario messages earlier (the "Flood the system" burst)."""
    geo = G.load()
    w = World(now_h)
    w.alerts = [a for a in (alerts or []) if a["atH"] <= now_h]
    pulled = pulled or {}
    base = []
    for m in scenario()["messages"]:
        if m["id"] in pulled:
            m = {**m, "atH": pulled[m["id"]], "burst": True}
        if m["atH"] <= now_h:
            base.append(m)
    msgs = base + [m for m in (extra_messages or []) if m["atH"] <= now_h]
    msgs.sort(key=lambda m: m["atH"])
    for m in msgs:
        process(w, m, geo, live=bool(m.get("live")))
    plans_until(w, now_h, extra_plans)
    w.levels = zone_levels(w, geo)
    from api.v2.planner import plan_outreach
    plan_outreach(w, geo)
    return w
