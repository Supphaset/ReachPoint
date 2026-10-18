"""Outbound browser calls use stored facts and the normal report history."""

import re

from api.v2 import pipeline as P


def opening(s, hh=None, kind="safetyCheck"):
    th = s.lang == "th"
    fact = lambda k: s.facts.get(k, {}).get("value")
    address = fact("address")
    depth = s.facts.get("depthRange", {}).get("quote")
    if depth:
        for pattern, th_word, en_word in ((r"เอว|waist", "เอว", "waist"), (r"อก|chest", "อก", "chest"),
                                         (r"เข่า|knee", "เข่า", "knees"), (r"คอ|neck", "คอ", "neck"),
                                         (r"ข้อเท้า|ankle", "ข้อเท้า", "ankles")):
            if re.search(pattern, depth, re.I):
                depth = f"น้ำถึง{th_word}" if th else f"the water was at your {en_word}"
                break
        else:
            value = hh.last_depth if hh else fact("depthRange")
            depth = (f"ระดับน้ำ {value[0]}–{value[1]} เมตร" if th else f"water depth {value[0]}–{value[1]} m") if value else None
    people = hh.people if hh else fact("people")
    cannot = hh.cannot_walk if hh else fact("cannotWalk")
    parts = ["สวัสดีค่ะ ReachPoint โทรมาถามความปลอดภัย" if th else "Hello, this is ReachPoint calling to check on you"]
    if address:
        parts[0] += f" ที่ {address}" if th else f" at {address}"
    parts[0] += "ค่ะ" if th else "."
    if kind == "lostContact" and hh:
        at = P.label_time(hh.last_heard_h)
        parts.append(f"เราไม่ได้รับข่าวจากคุณตั้งแต่ {at} ค่ะ" if th else f"We haven't heard from you since {at}.")
    if depth:
        parts.append(f"ครั้งก่อนคุณบอกว่า {depth}" if th else f"Last time you said: {depth}.")
    if people is not None:
        parts.append(f"เราบันทึกไว้ {people} คนค่ะ" if th else f"We recorded {people} people.")
    if cannot:
        parts.append(f"มีคนเดินไม่ได้ {cannot} คนค่ะ" if th else f"{cannot} person cannot walk.")
    parts.append("ตอนนี้น้ำสูงขึ้นไหมคะ" if th else "Is the water higher now?")
    return " ".join(parts)


def event(v, s, state, missed=False):
    v.seq += 1
    v.messages.append({"id": f"L{v.seq}", "atH": v.now_h, "channel": "callEvent", "text": state,
                       "householdHint": s.household_id, "callMissed": missed, "live": True})


def fallback(v, s):
    from api.v2 import routes as R
    hh = R._state(v)["world"].households.get(s.household_id)
    text = ("โทรด้วยเสียงไม่ได้ตอนนี้ ขอถามผ่านแชทแทนค่ะ " if s.lang == "th" else
            "Gemini Live is unavailable. We'll check in by text instead. ") + opening(s, hh, s.call_kind or "safetyCheck")
    s.transcript.append({"role": "agent", "text": text, "kind": "checkin", "atH": v.now_h})
    s.follow = "checkin"
    s.incoming = None
    s.call_kind = None
    event(v, s, "unavailable; text check-in sent")
    return text
