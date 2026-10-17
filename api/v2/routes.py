"""v2 API (docs/product/v2-spec.md §8). Each demo room (X-Demo-Room) keeps its own clock, live messages and plans."""

from __future__ import annotations

import json
import re
import threading
from dataclasses import dataclass, field

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from api.v2 import ai, board as B, geo as G, intake as I, pipeline as P
from api.v2.reader import Fact, Read

router = APIRouter(prefix="/api/v2")
DEFAULT_NOW_H = 96.0  # 25 Nov 06:00: the water is rising toward the peak (9.97 m at 10:00)
_rooms_ref = None


@dataclass
class V2Room:
    now_h: float = DEFAULT_NOW_H
    messages: list[dict] = field(default_factory=list)
    plans: list[dict] = field(default_factory=list)
    alerts: list[dict] = field(default_factory=list)
    pulled: dict = field(default_factory=dict)
    sessions: dict = field(default_factory=dict)
    first: dict = field(default_factory=dict)   # household id -> {"team", "at"}: a team marked the case "do first"
    lock: threading.Lock = field(default_factory=threading.Lock)
    seq: int = 0


def bind(rooms) -> None:
    global _rooms_ref
    _rooms_ref = rooms

    def warm():  # load the city, the scenario and the time-lapse, and wake Gemini, before the first judge arrives
        try:
            G.load()
            P.run(80)
            ai.read("น้ำถึงเข่า อยู่กัน 2 คน")
            B.timeline()
        except Exception:
            pass
    threading.Thread(target=warm, daemon=True).start()


def room() -> V2Room:
    r = _rooms_ref.get(_rooms_ref.current_id.get())
    if not hasattr(r, "v2"):
        r.v2 = V2Room()
    return r.v2


def _state(v: V2Room, at_h: float | None = None) -> dict:
    """The board at a moment; reused until the room changes (polling never recomputes an unchanged board)."""
    at = min(at_h if at_h is not None else v.now_h, v.now_h)
    sig = (round(at, 2), v.now_h, len(v.messages), len(v.plans), len(v.alerts), len(v.pulled))
    cache = v.__dict__.setdefault("_cache", {})
    if sig not in cache:
        if len(cache) > 40:
            cache.clear()
        cache[sig] = B.state(at, v.messages, v.plans, v.alerts, v.pulled)
    return cache[sig]


def _public(s: dict) -> dict:
    s = dict(s)
    s.pop("world", None)
    return s


@router.get("/geo")
def geo_view():
    geo = G.load()
    feats = [{"type": "Feature", "properties": {"id": z["properties"]["id"], "district": z["properties"].get("district"),
                                                 "label": z["properties"].get("label"), "sector": z["properties"].get("sector")},
              "geometry": z["geometry"]} for z in geo.zones]
    sectors = [{"type": "Feature", "properties": {"id": f["properties"]["id"], "name": f["properties"].get("name")},
                "geometry": f["geometry"]} for f in (geo.sectors or [])]
    return {"zones": {"type": "FeatureCollection", "features": feats}, "center": [100.4705, 7.0085],
            "sectors": {"type": "FeatureCollection", "features": sectors},
            "sources": {"zones": "ReachPoint zones cut along roads, rail and canals (OSM)",
                        "buildings": "Google Open Buildings v3", "ground": "FABDEM v1.2"}}


@router.get("/buildings")
def buildings_near(lon: float, lat: float, r: float = 70):
    geo = G.load()
    x, y = G.to_m(lon, lat)
    return {"buildings": [{"id": b.id, "outline": b.outline, "groundM": b.ground_m} for b in geo.near(x, y, min(r, 150))[:80]]}


@router.get("/sim")
def sim_meta():
    from api.v2 import sim as S
    m = dict(S.meta())
    m.pop("zones", None)
    m.pop("groundDm", None)
    return m


@router.get("/sim.bin")
def sim_frames():
    from fastapi.responses import Response
    data = (G.PKG / "v2-sim.bin.gz").read_bytes()
    return Response(data, media_type="application/octet-stream",
                    headers={"Content-Encoding": "gzip", "Cache-Control": "public, max-age=86400"})


@router.get("/terrain")
def terrain():
    """The 30 m ground heights under the flood layer (decimetres), so the map can let reported water follow the ground."""
    import json as _j
    from api.v2 import sim as S
    t = _j.loads((G.PKG / "v2-terrain.json").read_text())
    g = S.meta().get("groundDm")  # the ground the simulation used (street level in dense blocks)
    return {"rows": t["rows"], "cols": t["cols"], "bbox": t["bbox"],
            "zDm": g or [-9999 if v is None else int(round(v * 10)) for r in t["z"] for v in r]}


@router.get("/analysis")
def analysis(at: float | None = None):
    """Corrections from the reports for the map at a moment (a 150 m lattice over the city)."""
    from api.v2 import assim as A
    v = room()
    st = _state(v, at)
    w = st["world"]
    m = (G.PKG / "v2-sim.json")
    import json as _j
    meta = _j.loads(m.read_text())
    rows, cols = max(1, meta["rows"] // 5), max(1, meta["cols"] // 5)
    idx = getattr(w, "assim_index", None)
    obs = [o for o in (idx.obs if idx else []) if not o.doubtful]
    from api.v2 import sim as S
    ground = {o.message_id: o.ground_m for o in w.obs}
    to_m = lambda lon, lat: ((lon - G.LON0) * G.MX, (lat - G.LAT0) * G.MY)
    # the same ground the map's water is drawn on, so a report's water surface lands at its reported depth
    grounds = [S.ground(o.x / G.MX + G.LON0, o.y / G.MY + G.LAT0) or ground.get(o.id, 0.0) for o in obs]
    f = A.field(obs, grounds, meta["bbox"], rows, cols, st["atH"], to_m)
    return {"atH": st["atH"], "bbox": meta["bbox"], "rows": rows, "cols": cols, "incStepM": 0.05, "wseStepM": 0.1, **f}


@router.get("/timeline")
def timeline():
    return B.timeline()


@router.get("/state")
def state(at: float | None = None):
    v = room()
    s = _public(_state(v, at))
    s["now"] = {"atH": v.now_h, "at": P.label_time(v.now_h)}
    return s


class ClockIn(BaseModel):
    action: str = Field(pattern="^(advance|morning|rain|river|flood|reset)$")


@router.post("/clock")
def clock(body: ClockIn):
    v = room()
    with v.lock:
        if body.action == "reset":
            v.__init__()
        elif body.action == "advance":
            v.now_h += 0.5
        elif body.action == "morning":
            h = int(v.now_h) + 1
            while (h + 6) % 24 != 7:
                h += 1
            v.now_h = float(h)
        elif body.action in ("rain", "river"):
            v.alerts.append({"atH": v.now_h, "kind": body.action})
        elif body.action == "flood":
            later = [m for m in P.scenario()["messages"] if v.now_h < m["atH"] <= v.now_h + 30 and m["channel"] != "bulletin"
                     and m["id"] not in v.pulled][:40]
            for i, m in enumerate(later):
                v.pulled[m["id"]] = round(v.now_h - 0.2 + i * 0.005, 3)
    return {"now": {"atH": v.now_h, "at": P.label_time(v.now_h)}, "action": body.action}


# --- the intake agent ---
class PinIn(BaseModel):
    lon: float = Field(ge=-180, le=180)
    lat: float = Field(ge=-90, le=90)
    method: str = Field(default="map", pattern="^(gps|map)$")
    accuracyM: float | None = Field(default=None, ge=0, le=100000)


class TurnIn(BaseModel):
    text: str = Field(min_length=1, max_length=600)
    channel: str = Field(default="chat", pattern="^(chat|voice)$")
    pin: PinIn | None = None  # the phone's GPS, or a pin the person moved on the map
    replyTo: str | None = Field(default=None, max_length=24)  # the kind of agent message a button answers


@router.post("/chat/sessions")
def new_chat(lang: str = "th"):
    v = room()
    s = I.new_session("en" if lang == "en" else "th")
    v.sessions[s.id] = s
    return s.view()


def _household_of(w, session) -> str | None:
    ids = {m["id"] for m in room().messages if m.get("sessionId") == session.id and not m.get("neighbourOnly")}
    for h in w.households.values():
        if ids & set(h.message_ids):
            return h.id
    return None


def _hold_neighbour(s, r):
    """In a live chat every neighbour waits in a queue: the agent asks its direction if missing, then shows the house
    on the satellite picture to confirm, before it is matched."""
    for f in r.all("neighbour"):
        if isinstance(f.value, dict) and not any(q["quote"] == f.quote for q in s.nb_queue):
            s.nb_queue.append({"nb": dict(f.value), "quote": f.quote, "cands": None, "i": 0})
    r.facts = [f for f in r.facts if f.field != "neighbour"]
    return r


def _candidates(s, item) -> list[str]:
    geo = G.load()
    b = geo.buildings.get(s.building_id) if s.building_id else None
    if b is None or item["nb"].get("side") not in G.DIRECTIONS:
        return []
    return geo.neighbours(b)[item["nb"]["side"]][:3]


def _confirm_effect(s, item) -> dict:
    geo = G.load()
    me = geo.buildings.get(s.building_id)
    c = geo.buildings.get(item["cands"][item["i"]])
    return {"side": item["nb"]["side"], "quote": item["quote"], "candidate": {"id": c.id, "outline": c.outline, "lon": c.lon, "lat": c.lat},
            "me": me and {"id": me.id, "outline": me.outline, "lon": me.lon, "lat": me.lat}, "n": item["i"] + 1, "of": len(item["cands"])}


def _add_neighbour(v, s, channel: str, lang: str, building_id: str | None = None):
    """The first queued neighbour goes in as its own message, matched to the confirmed building (or the nearest one
    in its direction, marked not sure)."""
    held = s.nb_queue.pop(0)
    nb = held["nb"]
    v.seq += 1
    msg = {"id": f"L{v.seq}", "atH": v.now_h, "channel": channel, "text": held["quote"], "live": True, "pin": s.pin,
           "sessionId": s.id, "householdHint": s.household_id, "neighbourOnly": True, "neighbourBuildingId": building_id,
           "_read": Read([Fact("neighbour", nb, held["quote"])], reader="rules")}
    v.messages.append(msg)
    st = _state(v)
    eff = msg.get("_effects", {}).get("neighbour")
    s.neighbour_results.append({"side": nb.get("side"), "result": "known" if eff and eff["known"] else "new" if eff else "unmatched",
                                "buildingId": eff and eff["buildingId"], "confirmed": bool(building_id)})
    if not eff:
        return None, ""
    nz = st["world"].households[eff["householdId"]].zone_id
    has_plan = any(nz in p.get("zones", []) for p in st["world"].plans)
    where = (I.side_word(nb.get("side"), lang) + ": ") if nb.get("side") in G.DIRECTIONS else ""
    return eff, where + (I.say("known" if has_plan else "known_noplan", lang) if eff["known"] else I.say("new", lang)) + " "


@router.post("/chat/sessions/{sid}/turn")
def chat_turn(sid: str, body: TurnIn):
    return turn(sid, body.text, body.channel, body.pin.model_dump() if body.pin else None, body.replyTo)


def _pin_to_house(pin: dict, geo) -> dict | None:
    """A GPS fix or a map pin → the building under it (or the nearest within 60 m); outside the city, nothing."""
    lon, lat = pin["lon"], pin["lat"]
    b = geo.snap(lon, lat, 60)  # zone outlines leave gaps along roads, so the building decides the zone
    if b is None or not b.zone_id:
        return None
    return {"lon": b.lon, "lat": b.lat, "precision": pin.get("method", "map"), "buildingId": b.id, "zoneId": b.zone_id,
            "label": None, "by": "your GPS" if pin.get("method") == "gps" else "your pin on the map",
            "accuracyM": pin.get("accuracyM")}


def turn(sid: str, said: str, channel: str = "chat", pin: dict | None = None, reply_to: str | None = None) -> dict:
    """One turn of the intake agent: typed, held-mic, or Gemini Live voice (api/v2/live.py)."""
    v = room()
    s = v.sessions.get(sid)
    if s is None:
        raise HTTPException(404, "No such conversation")
    text = said.strip()
    with v.lock:
        lang = I.lang_of(text, s.lang)
        s.lang = lang
        s.transcript.append({"role": "person", "text": text, "channel": channel})
        pending = s.pending
        geo = G.load()
        effects = {}
        prefix = ""
        main_msg = None
        if pin:  # a pin always wins over address words: it is where the phone (or the person's finger) is
            loc = _pin_to_house(pin, geo)
            if loc:
                s.pin, s.building_id, s.zone_id = {"lon": loc["lon"], "lat": loc["lat"], "precision": loc["precision"]}, loc["buildingId"], loc["zoneId"]
                effects["located"] = loc
            else:
                effects["pinOutside"] = True
        follow = None
        # a button under one of our own messages answers that message, even if an intake question is still open
        if s.household_id and not s.nb_queue and (reply_to or (pending != "shelter" and (s.follow or s.finished))):
            from api.v2 import followup as F
            follow = F.answer(v, s, _state(v)["world"], text, reply_to or s.follow, lang)
            if follow:
                for k in ("shelterRoute", "checklist"):
                    if follow.get(k):
                        effects[k] = follow[k]
                if follow.get("choices"):
                    effects["choices"] = {"kind": follow["kind"], "options": [{"label": a, "send": b} for a, b in follow["choices"]]}
                if follow["kind"] not in ("evacWalk", "leaveAsk"):
                    s.follow = None
        # an answer to the shelter question only when it is one: anything else (a neighbour, a new problem) is read as usual
        shelter_answer = re.search(r"ไป|ได้|โอเค|อยู่บ้าน|ต้องการทีม|ไม่|\b(ok|okay|yes|go|stay|no|can.?t|need|i can)\b", text, re.I)
        if follow:
            pass
        elif pending == "shelter" and s.shelter_offer and shelter_answer and len(text) <= 40:
            go = re.search(r"^\s*(ไป|ได้|โอเค|ok|okay|yes|go|ไปได้|ไปค่ะ|ไปครับ|ไปเองได้|i can)", text, re.I) and not re.search(r"ไม่|อยู่บ้าน|ต้องการทีม|stay|no\b|can.?t|need", text, re.I)
            if go:
                v.seq += 1
                v.messages.append({"id": f"L{v.seq}", "atH": v.now_h, "channel": channel, "text": text, "live": True, "pin": s.pin,
                                   "sessionId": s.id, "householdHint": s.household_id, "toShelter": True,
                                   "shelterId": s.shelter_offer["shelterId"], "_read": Read([], reader="rules")})
                effects["shelter"] = {**s.shelter_offer, "going": True}
                prefix = I.say("shelter_go", lang, name=s.shelter_offer["name"]) + " "
            else:
                effects["shelter"] = {**s.shelter_offer, "going": False}
                prefix = I.say("shelter_stay", lang) + " "
                if not s.shelter_offer.get("walkable") and re.search(r"ต้องการทีม|need", text, re.I):
                    v.seq += 1  # they can't get there on their own: teams see "wants to leave, needs a ride"
                    v.messages.append({"id": f"L{v.seq}", "atH": v.now_h, "channel": "safetyReply", "text": text, "live": True,
                                       "pin": s.pin, "sessionId": s.id, "householdHint": s.household_id, "wantsOut": True,
                                       "_read": Read([], reader="rules")})
                    effects["checklist"] = __import__("api.v2.followup", fromlist=["READY"]).READY
        elif pending == "nb_dir" and s.nb_queue:
            from api.v2.reader import direction_of
            side = direction_of(text)
            item = s.nb_queue[0]
            if side:
                item["nb"]["side"] = side
            else:  # they don't know which way: match the nearest building, marked not sure
                effects["neighbour"], prefix = _add_neighbour(v, s, channel, lang)
        elif pending == "nb_confirm" and s.nb_queue:
            item = s.nb_queue[0]
            yes = re.search(r"^\s*(ใช่|ถูก|yes|yeah|yep|correct|ใช่ค่ะ|ใช่ครับ)", text, re.I) and not re.search(r"ไม่ใช่|^\s*no\b|not", text, re.I)
            if yes:
                effects["neighbour"], prefix = _add_neighbour(v, s, channel, lang, item["cands"][item["i"]])
            elif item["i"] + 1 < len(item["cands"]):
                item["i"] += 1  # show the next building that way
            else:
                effects["neighbour"], prefix = _add_neighbour(v, s, channel, lang)
                prefix = I.say("nb_unsure", lang) + " " + prefix
        else:
            from concurrent.futures import ThreadPoolExecutor
            with ThreadPoolExecutor(2) as ex:  # Gemini reads while Pinpoint looks up the address
                f_read = ex.submit(ai.read, text, channel)
                f_loc = ex.submit(I.locate, text, geo) if not s.pin else None
                r = f_read.result()
                pre_loc = f_loc.result() if f_loc else None
            if pending == "people" and r.get("people") is None:
                m = re.search(r"\d+", text)
                if m:
                    r.facts.append(Fact("people", int(m.group(0)), m.group(0)))
            if pending == "vulnerable" and I.NONE_WORDS.search(text):
                s.facts["vulnerable"] = {"value": "none", "quote": text}
            if not s.pin:
                loc = pre_loc or (I.locate(r.get("address"), geo) if r.get("address") and r.get("address") != text else None)
                if loc:
                    s.pin, s.building_id, s.zone_id = {"lon": loc["lon"], "lat": loc["lat"], "precision": "address"}, loc["buildingId"], loc["zoneId"]
                    effects["located"] = loc
            _hold_neighbour(s, r)
            I._merge(s, r)
            effects["facts"] = [{"field": f.field, "value": f.value, "quote": f.quote} for f in r.facts if f.field != "neighbour"]
            effects["reader"] = r.reader
            if s.pin:
                # everything said before the house was found goes in with this message
                earlier = " ".join(t["text"] for t in s.transcript if t["role"] == "person") if not s.household_id else text
                v.seq += 1
                rr = r if s.household_id or earlier == text else _hold_neighbour(s, ai.read(earlier, channel))
                msg = {"id": f"L{v.seq}", "atH": v.now_h, "channel": "safetyReply" if s.finished else channel, "text": earlier,
                       "live": True, "pin": s.pin, "sessionId": s.id, "householdHint": s.household_id, "_read": rr}
                v.messages.append(msg)
                main_msg = msg
        st = _state(v)
        w = st["world"]
        s.household_id = _household_of(w, s) or s.household_id
        if follow:
            reply = follow["reply"]
            if follow.get("kind") != "shelter":
                s.pending = None
            if "shelter" not in s.asked:
                s.asked.append("shelter")  # the evacuation flow covered it
        elif s.finished and not s.nb_queue:  # a neighbour mentioned after the questions still gets its own check
            reply = prefix + I.say("reply_ok", lang)
            s.pending = None
        else:
            if s.pin and s.shelter_offer is None and "shelter" not in s.asked and s.facts.get("urgent", {}).get("value") is not True:
                from api.v2 import shelters as SH
                opts = SH.options(w, s.pin["lon"], s.pin["lat"])
                walk = [o for o in opts if o["walkable"]]
                # the nearest walkable shelter; if none, the nearest one anyway: they may have a boat or a high truck
                s.shelter_offer = (walk or opts or [{}])[0]
                s.shelter_nearest = opts[0] if opts else None
            while s.nb_queue and s.pin and s.nb_queue[0]["nb"].get("side") in G.DIRECTIONS and not s.nb_queue[0]["cands"]:
                s.nb_queue[0]["cands"] = _candidates(s, s.nb_queue[0])
                if not s.nb_queue[0]["cands"]:  # no building that way within 60 m: nearest one, not sure
                    effects["neighbour"], p2 = _add_neighbour(v, s, channel, lang)
                    prefix += p2
                    st = _state(v)
                    w = st["world"]
            nxt = I._next(s)
            if nxt == "nb_confirm":
                effects["nbConfirm"] = _confirm_effect(s, s.nb_queue[0])
            if nxt in ("where", "where_again"):
                effects["askLocation"] = True  # the phone opens the map pin and GPS button
            if nxt:
                s.asked.append(nxt)
                s.pending = nxt
                o = s.shelter_offer or {}
                if nxt == "shelter":
                    key = "shelter" if o.get("walkable") else "shelter_deep"
                    reply = prefix + I.say(key, lang, name=o.get("name"), km=o.get("km"), minutes=o.get("minutes"), deep=o.get("deepestM"))
                    # the phone shows the route on the flood map, a Google Maps link and the two answers
                    effects["shelterRoute"] = {**o, "from": [s.pin["lon"], s.pin["lat"]],
                                               "googleMaps": "https://www.google.com/maps/dir/?api=1&origin="
                                               f"{s.pin['lat']},{s.pin['lon']}&destination={o['lat']},{o['lon']}&travelmode=walking"}
                elif nxt == "nb_confirm":
                    side = s.nb_queue[0]["nb"]["side"]
                    reply = prefix + I.say("nb_confirm" if s.nb_queue[0]["i"] == 0 else "nb_confirm_next", lang, side=I.side_word(side, lang))
                else:
                    reply = prefix + I.say(nxt, lang)
            else:
                s.pending = None
                s.finished = True
                near = getattr(s, "shelter_nearest", None)
                if s.shelter_offer == {} and near and s.facts.get("urgent", {}).get("value") is not True:
                    prefix += I.say("shelter_none", lang, name=near["name"], deep=near["deepestM"]) + " "
                while s.nb_queue and s.pin:  # urgent: no more questions; neighbours go in unconfirmed
                    effects["neighbour"], _ = _add_neighbour(v, s, channel, lang)
                    st = _state(v)
                    w = st["world"]
                reply = prefix + I.say("urgent_done" if s.facts.get("urgent", {}).get("value") is True else "done", lang)
        s.transcript.append({"role": "agent", "text": reply})
        hh = w.households.get(s.household_id) if s.household_id else None
        zone = st["zones"].get(hh.zone_id) if hh and hh.zone_id else None
        effects["household"] = hh.view() if hh else None
        if hh and hh.lon is not None:
            b = geo.buildings.get(hh.building_id) if hh.building_id else None
            d, sd, n, prior = P.local_depth(w, hh.lon, hh.lat, v.now_h)
            if n:
                effects["depthHere"] = [d, round(max(0.0, d - sd), 2), round(d + sd, 2)]
            effects["simHere"] = prior
        from api.v2 import followup as F
        return {"session": s.view(), "reply": reply, "effects": effects, "zone": zone, "status": F.status(v, s, st),
                "overall": st["overall"], "activity": st["activity"][:8]}


class SimIn(BaseModel):
    event: str = Field(pattern="^(rain|river|teamPlan|teamVisit|checkin)$")


@router.post("/chat/sessions/{sid}/simulate")
def simulate(sid: str, body: SimIn):
    """'What happens next' on the family's phone: more rain, the river rising, a team planning to come, the team's
    visit, a check-in. Goes through the same paths as the real events, so the board changes too."""
    from api.v2 import followup as F
    v = room()
    s = v.sessions.get(sid)
    if s is None:
        raise HTTPException(404, "No such conversation")
    with v.lock:
        out = F.simulate(v, s, body.event, s.lang)
    if out.get("error"):
        raise HTTPException(409, out["error"])
    out["status"] = F.status(v, s, _state(v))
    return out


@router.get("/chat/sessions/{sid}/status")
def session_status(sid: str):
    from api.v2 import followup as F
    v = room()
    s = v.sessions.get(sid)
    if s is None:
        raise HTTPException(404, "No such conversation")
    return F.status(v, s, _state(v))


STALE_PLAN_H = 4  # a zone plan older than this is not news to a family that has just written in (its time has passed)


@router.get("/me/{token}")
def me(token: str):
    v = room()
    s = next((x for x in v.sessions.values() if x.token == token), None)
    if s is None:
        raise HTTPException(404, "No such status page")
    st = _state(v)
    w = st["world"]
    hh = w.households.get(s.household_id) if s.household_id else None
    zone = st["zones"].get(hh.zone_id) if hh and hh.zone_id else None
    from api.v2 import followup as F
    # A team's plan for the zone waits until the agent has finished taking the report: a family mid-conversation
    # should not get "a boat is coming" before it has said who is in the house. A demo "team plans" click is shown.
    holding = not s.finished
    inbox = sorted([o for o in w.outbound if hh and o["householdId"] == hh.id and o["atH"] <= v.now_h
                    and not (o["kind"] == "planUpdate" and o.get("team") != F.SIM_TEAM
                             and (holding or o["atH"] < v.now_h - STALE_PLAN_H))], key=lambda o: o["atH"])
    inbox = [{**o, "text": o.get("en") or o["text"]} if s.lang == "en" else dict(o) for o in inbox]
    for o in inbox:
        o.pop("en", None)
        o["at"] = P.label_time(o["atH"])
        # the answers the phone offers under this message, sent back with replyTo = its kind
        o["choices"] = [{"label": a, "send": b} for a, b in F.CHOICES.get(o["kind"], [])]
    return {"session": s.view(), "household": hh.view() if hh else None, "zone": zone, "inbox": inbox,
            "now": {"atH": v.now_h, "at": P.label_time(v.now_h)}}


class PlanIn(BaseModel):
    text: str = Field(min_length=3, max_length=300)
    team: str | None = Field(default=None, max_length=80)   # the plan page sends the team's own name


@router.post("/plans")
def post_plan(body: PlanIn):
    v = room()
    parsed = ai.read_plan(body.text)
    with v.lock:
        v.seq += 1
        p = {"id": f"LP{v.seq}", "atH": v.now_h, "text": body.text, "_parsed": {k: parsed.get(k) for k in ("team", "vehicle", "seats", "zones", "eta", "offers")}}
        if body.team and body.team.strip():
            p["_parsed"]["team"] = body.team.strip()
        v.plans.append(p)
    st = _state(v)
    mine = next((x for x in st["world"].plans if x["id"] == p["id"]), None)
    return {"plan": mine, "reader": parsed.get("reader")}


# --- volunteer pages (docs/product/v2-volunteer-pages.md) ---
@router.get("/v/overview")
def v_overview():
    from api.v2 import cases as C
    return C.overview(_state(room()))


@router.get("/v/feed")
def v_feed(kind: str | None = None, team: str | None = None, limit: int = 80):
    from api.v2 import cases as C
    v = room()
    return C.feed(_state(v), v.messages, kind, min(max(limit, 1), 300), team)


@router.get("/v/zones/{zid}")
def v_zone(zid: str, team: str | None = None):
    from api.v2 import cases as C
    out = C.zone(_state(room()), zid, team)
    if out is None:
        raise HTTPException(404, "No such zone")
    return out


@router.get("/v/cases/{hid}")
def v_case(hid: str, team: str | None = None):
    from api.v2 import cases as C
    v = room()
    out = C.case(_state(v), v.messages, hid, team)
    if out is None:
        raise HTTPException(404, "No such household")
    return out


class OutcomeIn(BaseModel):
    outcome: str = Field(pattern="^(pickedUp|nobodyThere|atShelter)$")
    team: str = Field(min_length=1, max_length=80)
    shelterId: str | None = Field(default=None, max_length=8)


@router.post("/v/cases/{hid}/outcome")
def v_outcome(hid: str, body: OutcomeIn):
    """A team's one tap: picked up, or nobody there. The family's phone is told; the board counts it."""
    from api.v2 import cases as C
    v = room()
    with v.lock:
        if hid not in _state(v)["world"].households:
            raise HTTPException(404, "No such household")
        v.seq += 1
        v.messages.append({"id": f"L{v.seq}", "atH": v.now_h, "channel": "team", "outcome": body.outcome, "team": body.team.strip(),
                           "householdHint": hid, "live": True, "shelterId": body.shelterId,
                           "text": f"{body.team.strip()}: " + {"pickedUp": "picked them up", "nobodyThere": "went there, nobody there",
                                                               "atShelter": "checked them in at the shelter"}[body.outcome]})
    return C.case(_state(v), v.messages, hid, body.team)


@router.get("/v/urgent")
def v_urgent():
    """Every urgent open case, grouped by zone, most urgent zone first: what a team should pick from.
    Teams can mark a case "do first"; every team sees the mark."""
    from api.v2 import cases as C
    v = room()
    return C.urgent(_state(v), v.first)


class FirstIn(BaseModel):
    team: str = Field(min_length=1, max_length=80)
    first: bool = True


@router.post("/v/cases/{hid}/first")
def v_first(hid: str, body: FirstIn):
    from api.v2 import cases as C
    v = room()
    with v.lock:
        if hid not in _state(v)["world"].households:
            raise HTTPException(404, "No such household")
        if body.first:
            v.first[hid] = {"team": body.team.strip(), "at": P.label_time(v.now_h)}
        else:
            v.first.pop(hid, None)
    return C.urgent(_state(v), v.first)


@router.get("/v/trip")
def v_trip(zones: str, team: str | None = None):
    from api.v2 import cases as C
    return C.trip(_state(room()), [z.strip() for z in zones.split(",") if z.strip()][:6], team)


class CopilotIn(BaseModel):
    question: str = Field(min_length=1, max_length=600)


@router.post("/v/copilot")
def v_copilot(body: CopilotIn):
    """The volunteer copilot: Gemini answers with ReachPoint's tools; every number is checked against a tool result."""
    from api.v2 import copilot
    return copilot.ask(_state(room()), body.question)


@router.get("/depth-series")
def depth_series(lon: float, lat: float):
    """The water at one house, hour by hour from the flood model, and now corrected by nearby reports: for the
    victim's-view scene and the case page."""
    from api.v2 import sim as S
    v = room()
    st = _state(v)
    w = st["world"]
    hours = int(min(S.meta()["hours"], v.now_h + 24))
    model = [round(S.depth(lon, lat, h) or 0.0, 2) for h in range(hours + 1)]
    d, sd, n, prior = P.local_depth(w, lon, lat, v.now_h)
    b = G.load().snap(lon, lat, 40)
    return {"start": S.meta()["start"], "nowH": v.now_h, "now": P.label_time(v.now_h), "model": model,
            "corrected": {"m": round(d, 2), "lo": round(max(0.0, d - sd), 2), "hi": round(d + sd, 2), "reports": n, "model": round(prior, 2)},
            "groundM": b.ground_m if b else None, "buildingId": b.id if b else None}


@router.get("/v/blocks")
def v_blocks(zone: str | None = None):
    """Blocks with their outline, need and access now (walk / truck / boat), for the maps."""
    from api.v2 import cases as C
    return {"blocks": C.blocks(_state(room()), zone), "thresholds": {"walkM": C.WALK_M, "truckM": C.TRUCK_M}}
