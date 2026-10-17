"""After the first report the agent stays with the family until they are safe.

Every message ReachPoint sends a household ends in a choice the phone shows as buttons, and every answer leads
somewhere: wanting to leave opens an evacuation flow (can everyone walk? the shelter route, or a boat request), a
safety check reads the answer and replies to it, a team's visit is confirmed or reopened. The status card tells the
family where they stand: water now and in 6 hours, who plans to come, the nearest shelter, the next check-in.

`simulate` lets a judge play what happens next from the family's phone: more rain, the river rising, a team
planning to come, the team's visit, a check-in two hours later. Each one goes through the same paths as the real
thing (rain response map, plan line, a team's one tap), so the board and the volunteer pages change too.
"""

from __future__ import annotations

from api.v2 import pipeline as P, rain as RN, shelters as SH, sim as S
from api.v2.reader import Fact, Read

CHECKIN_H = 2.0

# the answers the phone offers after each kind of message: (button label, the text it sends)
LEAVE = [("ต้องการออกจากบ้าน · I need to leave", "ต้องการออกจากบ้าน"), ("อยู่บ้านก่อน · We'll stay for now", "อยู่บ้านก่อน")]
CHECK = [("ปลอดภัยดี · We're safe", "ปลอดภัยดี"), ("น้ำขึ้นอีก · Water is rising", "น้ำขึ้นอีกแล้ว"),
         ("ต้องการช่วยด่วน · Need help now", "ต้องการความช่วยเหลือด่วน")]
VISIT = [("ออกมาแล้ว ปลอดภัย · We're out and safe", "ออกมาแล้ว ปลอดภัย"), ("ยังมีคนติดอยู่ · Someone is still inside", "ยังมีคนติดอยู่"),
         ("ออกมาเองแล้ว · We left on our own", "ออกมาเองแล้ว")]
WALK = [("เดินได้ทุกคน · Everyone can walk", "เดินได้ทุกคน"), ("มีคนเดินไม่ได้ · Someone can't walk", "มีคนเดินไม่ได้")]
PLAN = [("รับทราบ · OK", "รับทราบ"), ("มีอะไรเปลี่ยน · Something changed", "มีอะไรเปลี่ยน")]
CHOICES = {"river": LEAVE, "rain": LEAVE, "rainRise": LEAVE, "leaveAsk": LEAVE, "earlyWarning": LEAVE,
           "check": CHECK, "morning": CHECK, "lostCall": CHECK, "checkin": CHECK,
           "pickedUp": VISIT, "nobodyThere": VISIT, "planUpdate": PLAN, "evacWalk": WALK}

READY = [("บัตรประชาชนและเอกสารสำคัญ ใส่ถุงกันน้ำ", "ID cards and papers in a waterproof bag"),
         ("ยาประจำตัว 3 วัน", "3 days of regular medicines"),
         ("โทรศัพท์และพาวเวอร์แบงก์", "Phone and power bank"),
         ("ปิดเบรกเกอร์ไฟฟ้าชั้นล่าง", "Switch off the power downstairs"),
         ("ขึ้นชั้นบน แขวนผ้าขาวที่หน้าต่างให้เรือเห็น", "Go upstairs; hang a white cloth from a window so boats see you")]

T = {
    "leave_walk": ("ได้ค่ะ ทุกคนในบ้านเดินลุยน้ำเองได้ไหมคะ", "OK. Can everyone at home walk through water on their own?"),
    "leave_stay": ("ได้ค่ะ อยู่ชั้นบน เก็บของสำคัญไว้ที่สูง ปิดไฟฟ้าชั้นล่าง เราจะถามอีกครั้งราว {at} ถ้าน้ำขึ้นเร็ว กดปุ่ม \"น้ำขึ้น\" ได้ทันที",
                   "OK. Stay upstairs, keep important things high and switch off the power downstairs. We'll check again around {at}. If the water rises fast, tap \"Water is rising\" any time."),
    "leave_ride": ("เราแจ้งทีมเรือและรถยกสูงแล้วว่าบ้านคุณต้องการออก{who} ระหว่างรอ เตรียมของตามรายการนี้และอยู่ชั้นบนนะคะ เมื่อมีทีมวางแผนมา เราจะบอกทันที",
                   "We've told the boat and high-truck teams your home needs to get out{who}. While you wait, get ready with this list and stay upstairs. We'll tell you as soon as a team plans to come."),
    "ride_again": ("เราได้รับคำขอของคุณแล้วค่ะ ทีมเรือและรถยกสูงเห็นบ้านคุณในรายการ 'ต้องการรถรับ' อยู่ ไม่ต้องขอใหม่ เตรียมของแล้ว {done}/{total} อย่าง{left} เมื่อมีทีมวางแผนมา เราจะบอกทันที",
                   "We already have your request: the boat and high-truck teams see your home as 'needs a ride'. No need to ask again. You have {done} of {total} things ready{left_en}. We'll tell you as soon as a team plans to come."),
    "check_safe": ("ดีใจที่ปลอดภัยค่ะ เราจะถามอีกครั้งราว {at}", "Glad you're safe. We'll check again around {at}."),
    "check_rising": ("น้ำที่บ้านคุณตอนนี้ราว {now} ม. แบบจำลองคาดว่าอีก 6 ชั่วโมงราว {later} ม. ต้องการออกจากบ้านไหมคะ",
                     "The water at your house is about {now} m now; the model expects about {later} m in 6 hours. Do you want to leave?"),
    "check_urgent": ("บันทึกเป็นเคสเร่งด่วนแล้วค่ะ ทุกทีมเห็นบ้านคุณ ถ้ามีคนบาดเจ็บหรือหายใจไม่ออก โทร 1669 ทันที ขึ้นที่สูงที่สุดไว้ก่อนนะคะ",
                     "Marked urgent. Every team can see your house. If anyone is hurt or can't breathe, call 1669 now. Get to the highest point you can."),
    "visit_out": ("ขอให้ปลอดภัยนะคะ เราปิดเคสบ้านคุณแล้ว ถ้ามีอะไรเปลี่ยน ตอบกลับได้เสมอ",
                  "Stay safe. We've closed your home's case. If anything changes, reply any time."),
    "visit_still": ("เราแจ้งทุกทีมแล้วว่ายังมีคนติดอยู่ เปิดเคสเร่งด่วนอีกครั้ง ใครยังอยู่บ้าง และน้ำถึงไหนแล้วคะ",
                    "We've told every team someone is still inside, and reopened your case as urgent. Who is still there, and how high is the water?"),
    "visit_self": ("ดีใจค่ะ เราบันทึกว่าคุณออกมาเองแล้ว ทีมจะได้ไม่ต้องไปที่บ้าน ตอนนี้อยู่ที่ไหนคะ",
                   "Good to hear. We've noted you got out on your own, so no team goes to the house. Where are you now?"),
    "plan_ok": ("รับทราบค่ะ ทีมยังไม่ยืนยันเวลาถึง อยู่ชั้นบนและเปิดโทรศัพท์ไว้นะคะ",
                "Noted. The team hasn't confirmed an arrival time. Stay upstairs and keep your phone on."),
    "plan_changed": ("เกิดอะไรขึ้นคะ เล่าได้เลย", "What happened? Tell us."),
    "rain_sim": ("ฝนหนักราว {mm} มม. กำลังจะตก แบบจำลองน้ำท่วมคาดว่าน้ำที่บ้านคุณจะสูงขึ้นราว {cm} ซม. ในอีกราว {h} ชั่วโมง ต้องการออกจากบ้านไหมคะ",
                 "Heavy rain (about {mm} mm) is coming. The flood model expects the water at your house to rise about {cm} cm in about {h} hours. Do you want to leave?"),
    "river_sim": ("ระดับน้ำแม่น้ำต้นทางสูงขึ้น อาจถึงบริเวณบ้านคุณในราว 6 ชั่วโมง ต้องการออกจากบ้านไหมคะ",
                  "The river upstream is rising and may reach your area in about 6 hours. Do you want to leave?"),
    "checkin_sim": ("ทุกคนในบ้านยังปลอดภัยไหมคะ ตอนนี้น้ำสูงแค่ไหน", "Is everyone at home still safe? How high is the water now?"),
}


def say(key: str, lang: str = "th", **kw) -> str:
    th, en = T[key]
    return (th if lang == "th" else en).format(**kw)


def kind_of(text: str, kind: str | None) -> str | None:
    """Which answer this is: the kind of the message it replies to, else guessed from the button words."""
    if kind:
        return kind
    for k, opts in (("leaveAsk", LEAVE), ("evacWalk", WALK), ("pickedUp", VISIT), ("planUpdate", PLAN)):
        if any(text.strip() == send for _, send in opts):
            return k
    return None


def ride_again(s, lang: str) -> dict:
    """A second "we need to leave" from a family that already asked: no new request, no second checklist."""
    done, total = len(set(s.ready)), len(READY)
    left = [READY[i] for i in range(total) if i not in s.ready]
    th = f" ที่ยังเหลือ: {', '.join(x[0] for x in left[:2])}" if left else " ครบแล้ว"
    en = f"; still to do: {', '.join(x[1] for x in left[:2])}" if left else ", all done"
    return {"reply": say("ride_again", lang, done=done, total=total, left=th, left_en=en), "kind": "ride"}


def _ride(s, reply: str) -> dict:
    """The first ride request: the checklist comes with it, once."""
    s.ride_requested = True
    return {"reply": reply, "checklist": READY, "kind": "ride"}


def _post(v, s, text: str, read: Read, **flags) -> dict:
    """The family's answer goes onto the board like any message, with what it means."""
    v.seq += 1
    msg = {"id": f"L{v.seq}", "atH": v.now_h, "channel": "safetyReply", "text": text, "live": True, "pin": s.pin,
           "sessionId": s.id, "householdHint": s.household_id, "_read": read, **flags}
    v.messages.append(msg)
    return msg


def water(w, s) -> dict | None:
    """Water at the house now (model corrected by reports) and in 6 hours (the model's change added)."""
    if not s.pin:
        return None
    lon, lat = s.pin["lon"], s.pin["lat"]
    d, sd, n, prior = P.local_depth(w, lon, lat, w.now_h)
    later_model = S.depth(lon, lat, w.now_h + 6)
    later = max(0.0, d + ((later_model or prior) - prior))
    return {"nowM": round(d, 2), "loM": round(max(0.0, d - sd), 2), "hiM": round(d + sd, 2), "in6hM": round(later, 2),
            "trend": "rising" if later - d > 0.05 else "falling" if d - later > 0.05 else "steady", "reports": n}


def answer(v, s, w, text: str, kind: str | None, lang: str) -> dict | None:
    """The agent's reply to an answer about one of its own messages: {reply, choices, effects}, or None if this
    isn't one (then the message is read as usual)."""
    from api.v2 import ai
    k = kind_of(text, kind)
    low = text.lower()
    yes = any(x in low for x in ("ต้องการออก", "ออกจากบ้าน", "อยากออก", "need to leave", "want to leave", "leave")) or text.strip() in ("ต้องการ", "ต้องการค่ะ", "ต้องการครับ", "ใช่", "yes")
    if k in ("river", "rain", "rainRise", "leaveAsk", "earlyWarning"):
        if yes and s.ride_requested:
            return ride_again(s, lang)
        if yes:
            s.follow = "evacWalk"
            return {"reply": say("leave_walk", lang), "choices": WALK, "kind": "evacWalk"}
        _post(v, s, text, Read([Fact("safe", True, text)], reader="rules"), wantsOut=False)
        return {"reply": say("leave_stay", lang, at=P.label_time(v.now_h + CHECKIN_H)[-5:]), "kind": "stay"}
    if k == "evacWalk":
        s.follow = None
        if "ไม่ได้" in text or "can't" in low or "cannot" in low:
            if s.ride_requested:
                return ride_again(s, lang)
            _post(v, s, text, Read([Fact("cannotWalk", 1, text)], reader="rules"), wantsOut=True)
            return _ride(s, say("leave_ride", lang, who=" มีคนเดินไม่ได้" if lang == "th" else ", with someone who can't walk"))
        if not s.pin:
            return None
        opts = SH.options(w, s.pin["lon"], s.pin["lat"])
        best = next((o for o in opts if o["walkable"]), opts[0] if opts else None)
        if best is None:
            if s.ride_requested:
                return ride_again(s, lang)
            _post(v, s, text, Read([], reader="rules"), wantsOut=True)
            return _ride(s, say("leave_ride", lang, who=""))
        s.shelter_offer, s.pending = best, "shelter"
        route = {**best, "from": [s.pin["lon"], s.pin["lat"]],
                 "googleMaps": "https://www.google.com/maps/dir/?api=1&origin="
                 f"{s.pin['lat']},{s.pin['lon']}&destination={best['lat']},{best['lon']}&travelmode=walking"}
        from api.v2 import intake as I
        key = "shelter" if best["walkable"] else "shelter_deep"
        return {"reply": I.say(key, lang, name=best["name"], km=best["km"], minutes=best["minutes"], deep=best["deepestM"]),
                "shelterRoute": route, **({} if s.ready_shown else {"checklist": READY}), "kind": "shelter"}
    if k in ("pickedUp", "nobodyThere"):
        if "ติด" in text or "still" in low or "inside" in low:
            _post(v, s, text, Read([Fact("urgent", True, text)], reader="rules"), stillThere=True)
            return {"reply": say("visit_still", lang), "kind": "still"}
        if "เอง" in text or "own" in low:
            _post(v, s, text, Read([Fact("safe", "evacuated", text)], reader="rules"), selfEvacuated=True)
            return {"reply": say("visit_self", lang), "kind": "self"}
        _post(v, s, text, Read([Fact("safe", "evacuated", text)], reader="rules"))
        return {"reply": say("visit_out", lang), "kind": "out"}
    if k == "planUpdate":
        if "เปลี่ยน" in text or "changed" in low:
            return {"reply": say("plan_changed", lang), "kind": "changed"}
        return {"reply": say("plan_ok", lang), "kind": "ok"}
    if k in ("check", "morning", "lostCall", "checkin") or s.finished:
        # a safety reply: read what it says, put it on the board, and answer what it says
        r = ai.read(text, "safetyReply")
        _post(v, s, text, r)
        if r.get("urgent") or "ด่วน" in text or "help now" in low:
            return {"reply": say("check_urgent", lang), "kind": "urgent"}
        if r.get("trend") == "rising" or "ขึ้น" in text or "rising" in low or r.get("depthRange"):
            st_w = w
            wat = water(st_w, s) or {"nowM": "?", "in6hM": "?"}
            s.follow = "leaveAsk"
            return {"reply": say("check_rising", lang, now=wat["nowM"], later=wat["in6hM"]), "choices": LEAVE, "kind": "leaveAsk"}
        if r.get("safe") or "ปลอดภัย" in text or "safe" in low:
            return {"reply": say("check_safe", lang, at=P.label_time(v.now_h + CHECKIN_H)[-5:]), "kind": "safe"}
        return None
    return None


def status(v, s, st: dict) -> dict:
    """What the family should know right now, for the card at the top of their chat."""
    w = st["world"]
    hh = w.households.get(s.household_id) if s.household_id else None
    zone_id = (hh.zone_id if hh else None) or s.zone_id
    plans = [p for p in w.plans if zone_id and zone_id in (p.get("zones") or [])]
    near = None
    if s.pin:
        opts = SH.options(w, s.pin["lon"], s.pin["lat"], k=2)
        near = next((o for o in opts if o["walkable"]), opts[0] if opts else None)
    last_agent = max((t.get("atH", 0) for t in s.transcript if t["role"] == "agent"), default=v.now_h)
    return {"householdId": hh.id if hh else None, "zoneId": zone_id, "status": hh.status if hh else "new",
            "urgent": bool(hh and hh.urgent), "wantsOut": bool(hh and hh.wants_out), "people": hh.people if hh else None,
            "water": water(w, s),
            "team": plans[-1] and {k: plans[-1].get(k) for k in ("team", "vehicle", "seats", "eta", "at")} if plans else None,
            "outcome": hh.outcome if hh else None,
            "shelter": near and {k: near[k] for k in ("name", "nameEn", "km", "deepestM", "walkable", "minutes")},
            "nextCheck": P.label_time(max(v.now_h, last_agent) + CHECKIN_H)[-5:], "now": P.label_time(v.now_h),
            "rideRequested": s.ride_requested, "ready": sorted(set(s.ready)), "readyTotal": len(READY)}


SIM_TEAM = "ทีมเรืออาสาจำลอง"


def simulate(v, s, event: str, lang: str) -> dict:
    """One click of 'what happens next' on the family's phone. Returns the agent message to show, if any."""
    if not s.household_id or not s.pin:
        return {"error": "Report first: the agent needs to know where your house is."}
    lon, lat = s.pin["lon"], s.pin["lat"]
    msg = None
    if event == "rain":
        r = RN.rise(lon, lat, RN.FORECAST_MM)
        cm, h = (int(round(r[0] * 100 / 5) * 5), max(1, int(r[1]))) if r else (20, 6)
        msg = {"text": say("rain_sim", lang, mm=int(RN.FORECAST_MM), cm=max(cm, 5), h=h), "kind": "rainRise", "choices": LEAVE}
    elif event == "river":
        msg = {"text": say("river_sim", lang), "kind": "river", "choices": LEAVE}
    elif event == "checkin":
        msg = {"text": say("checkin_sim", lang), "kind": "checkin", "choices": CHECK}
    elif event in ("teamPlan", "teamVisit"):
        zone = s.zone_id
        if event == "teamPlan" or not any(p.get("_parsed", {}).get("team") == SIM_TEAM for p in v.plans):
            v.seq += 1
            eta = P.label_time(v.now_h + 1)[-5:]
            text = f"{SIM_TEAM} เรือ 6 ที่นั่ง จะเข้าโซน {zone} ประมาณ {eta} (อพยพ)"
            v.plans.append({"id": f"LP{v.seq}", "atH": v.now_h, "text": text,
                            "_parsed": {"team": SIM_TEAM, "vehicle": "boat", "seats": 6, "zones": [zone], "eta": eta, "offers": "evacuation"}})
        if event == "teamVisit":
            v.seq += 1
            v.messages.append({"id": f"L{v.seq}", "atH": v.now_h, "channel": "team", "outcome": "pickedUp", "team": SIM_TEAM,
                               "householdHint": s.household_id, "live": True, "text": f"{SIM_TEAM}: picked them up"})
        # the family hears it through their inbox (plan update / the team's one tap), like a real team's message
        return {"event": event, "inbox": True}
    else:
        return {"error": f"unknown event {event}"}
    s.transcript.append({"role": "agent", "text": msg["text"], "kind": msg["kind"], "atH": v.now_h})
    s.follow = msg["kind"]
    return {"event": event, "message": msg}
