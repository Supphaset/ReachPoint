"""v2 API (docs/product/v2-spec.md §8). Each demo room (X-Demo-Room) keeps its own clock, live messages and plans."""

from __future__ import annotations

import json
import threading
from dataclasses import dataclass, field

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from api.v2 import ai, board as B, geo as G, intake as I, pipeline as P
from api.v2.reader import Fact, Read

router = APIRouter(prefix="/api/v2")
DEFAULT_NOW_H = 80.0  # 24 Nov 14:00: the water is rising fast, before the peak
_rooms_ref = None


@dataclass
class V2Room:
    now_h: float = DEFAULT_NOW_H
    messages: list[dict] = field(default_factory=list)
    plans: list[dict] = field(default_factory=list)
    alerts: list[dict] = field(default_factory=list)
    pulled: dict = field(default_factory=dict)
    sessions: dict = field(default_factory=dict)
    lock: threading.Lock = field(default_factory=threading.Lock)
    seq: int = 0


def bind(rooms) -> None:
    global _rooms_ref
    _rooms_ref = rooms


def room() -> V2Room:
    r = _rooms_ref.get(_rooms_ref.current_id.get())
    if not hasattr(r, "v2"):
        r.v2 = V2Room()
    return r.v2


def _state(v: V2Room, at_h: float | None = None) -> dict:
    return B.state(min(at_h if at_h is not None else v.now_h, v.now_h), v.messages, v.plans, v.alerts, v.pulled)


def _public(s: dict) -> dict:
    s = dict(s)
    s.pop("world", None)
    return s


@router.get("/geo")
def geo_view():
    geo = G.load()
    feats = [{"type": "Feature", "properties": {"id": z["properties"]["id"], "district": z["properties"].get("district")},
              "geometry": z["geometry"]} for z in geo.zones]
    return {"zones": {"type": "FeatureCollection", "features": feats}, "center": [100.4705, 7.0085],
            "sources": {"zones": "ReachPoint zones cut along roads, rail and canals (OSM)",
                        "buildings": "Google Open Buildings v3", "ground": "FABDEM v1.2"}}


@router.get("/buildings")
def buildings_near(lon: float, lat: float, r: float = 70):
    geo = G.load()
    x, y = G.to_m(lon, lat)
    return {"buildings": [{"id": b.id, "outline": b.outline, "groundM": b.ground_m} for b in geo.near(x, y, min(r, 150))[:80]]}


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
class TurnIn(BaseModel):
    text: str = Field(min_length=1, max_length=600)
    channel: str = Field(default="chat", pattern="^(chat|voice)$")


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


@router.post("/chat/sessions/{sid}/turn")
def chat_turn(sid: str, body: TurnIn):
    v = room()
    s = v.sessions.get(sid)
    if s is None:
        raise HTTPException(404, "No such conversation")
    text = body.text.strip()
    with v.lock:
        lang = I.lang_of(text, s.lang)
        s.lang = lang
        s.transcript.append({"role": "person", "text": text, "channel": body.channel})
        pending = s.pending
        geo = G.load()
        effects = {}
        prefix = ""
        if pending in ("left", "right", "across") and s.pin:
            if I.NONE_WORDS.search(text):
                prefix = I.say("none", lang) + " "
                s.neighbour_results.append({"side": pending, "result": "none"})
            else:
                r = ai.read(text, body.channel)
                nb = {"side": pending, "people": r.get("people"), "elderly": r.get("elderly") or (1 if "ยาย" in text or "old" in text.lower() else 0),
                      "children": r.get("children")}
                v.seq += 1
                msg = {"id": f"L{v.seq}", "atH": v.now_h, "channel": body.channel, "text": text, "live": True,
                       "pin": s.pin, "sessionId": s.id, "householdHint": s.household_id, "neighbourOnly": True,
                       "_read": Read([Fact("neighbour", {k: x for k, x in nb.items() if x}, text)], reader=r.reader)}
                v.messages.append(msg)
                st = _state(v)
                eff = msg.get("_effects", {}).get("neighbour")
                effects["neighbour"] = eff
                s.neighbour_results.append({"side": pending, "result": "known" if eff and eff["known"] else "new" if eff else "unmatched",
                                            "buildingId": eff and eff["buildingId"]})
                if eff:
                    nz = st["world"].households[eff["householdId"]].zone_id
                    has_plan = any(nz in p.get("zones", []) for p in st["world"].plans)
                    prefix = I.say("known" if has_plan else "known_noplan", lang) if eff["known"] else I.say("new", lang)
                    prefix += " "
        else:
            r = ai.read(text, body.channel)
            if pending == "people" and r.get("people") is None:
                import re
                m = re.search(r"\d+", text)
                if m:
                    r.facts.append(Fact("people", int(m.group(0)), m.group(0)))
            if pending == "vulnerable" and I.NONE_WORDS.search(text):
                s.facts["vulnerable"] = {"value": "none", "quote": text}
            if not s.pin:
                loc = I.locate(r.get("address") or text, geo)
                if loc:
                    s.pin, s.building_id, s.zone_id = {"lon": loc["lon"], "lat": loc["lat"], "precision": "address"}, loc["buildingId"], loc["zoneId"]
                    effects["located"] = loc
            I._merge(s, r)
            effects["facts"] = [{"field": f.field, "value": f.value, "quote": f.quote} for f in r.facts if f.field != "neighbour"]
            effects["reader"] = r.reader
            if s.pin:
                # everything said before the house was found goes in with this message
                earlier = " ".join(t["text"] for t in s.transcript if t["role"] == "person") if not s.household_id else text
                v.seq += 1
                msg = {"id": f"L{v.seq}", "atH": v.now_h, "channel": "safetyReply" if s.finished else body.channel, "text": earlier,
                       "live": True, "pin": s.pin, "sessionId": s.id, "householdHint": s.household_id,
                       "_read": r if s.household_id else ai.read(earlier, body.channel) if earlier != text else r}
                v.messages.append(msg)
        st = _state(v)
        w = st["world"]
        s.household_id = _household_of(w, s) or s.household_id
        if s.finished:
            reply = I.say("reply_ok", lang)
            s.pending = None
        else:
            nxt = I._next(s)
            if nxt:
                s.asked.append(nxt)
                s.pending = nxt
                reply = prefix + I.say(nxt, lang)
            else:
                s.pending = None
                s.finished = True
                reply = prefix + I.say("urgent_done" if s.facts.get("urgent", {}).get("value") is True else "done", lang)
        s.transcript.append({"role": "agent", "text": reply})
        hh = w.households.get(s.household_id) if s.household_id else None
        zone = st["zones"].get(hh.zone_id) if hh and hh.zone_id else None
        effects["household"] = hh.view() if hh else None
        if hh and zone and zone.get("level"):
            from api.v2.planner import _ground_p50  # noqa
            b = geo.buildings.get(hh.building_id) if hh.building_id else None
            lvl = w.levels[hh.zone_id]
            effects["depthHere"] = lvl.depth_at(b.ground_m) if b and b.ground_m is not None else None
        return {"session": s.view(), "reply": reply, "effects": effects, "zone": zone,
                "overall": st["overall"], "activity": st["activity"][:8]}


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
    inbox = sorted([o for o in w.outbound if hh and o["householdId"] == hh.id and o["atH"] <= v.now_h], key=lambda o: o["atH"])
    for o in inbox:
        o["at"] = P.label_time(o["atH"])
    return {"session": s.view(), "household": hh.view() if hh else None, "zone": zone, "inbox": inbox,
            "now": {"atH": v.now_h, "at": P.label_time(v.now_h)}}


class PlanIn(BaseModel):
    text: str = Field(min_length=3, max_length=300)


@router.post("/plans")
def post_plan(body: PlanIn):
    v = room()
    parsed = ai.read_plan(body.text)
    with v.lock:
        v.seq += 1
        p = {"id": f"LP{v.seq}", "atH": v.now_h, "text": body.text, "_parsed": {k: parsed.get(k) for k in ("team", "vehicle", "seats", "zones", "eta", "offers")}}
        v.plans.append(p)
    st = _state(v)
    mine = next((x for x in st["world"].plans if x["id"] == p["id"]), None)
    return {"plan": mine, "reader": parsed.get("reader")}
