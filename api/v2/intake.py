"""Intake agent: a short conversation with a victim, one question at a time, by chat or voice.

It asks only for what is missing: where (address → Pinpoint → the building), how many people, who is vulnerable,
how deep the water is (with one concrete check question when the words are vague), then the neighbours, side by
side. It skips the neighbour questions when the case is life-threatening. Every answer goes into the same
pipeline as every other message, so the board updates in front of the judge.
"""

from __future__ import annotations

import re
import secrets
from dataclasses import dataclass, field

from api.v2 import geo as G
from api.v2.reader import Fact, Read

Q = {
    "intro": ("ฉันเป็นผู้ช่วย AI ของ ReachPoint ค่ะ ตอนนี้เกิดอะไรขึ้นบ้าง และบ้านคุณอยู่ที่ไหนคะ",
              "I'm ReachPoint's AI assistant. What's happening, and where is your house?"),
    "where": ("บ้านอยู่ที่ไหนคะ บอกบ้านเลขที่และซอย หรือจุดสังเกตใกล้ๆ ก็ได้", "Where is your house? A house number and soi, or a nearby landmark, is fine."),
    "where_again": ("ยังหาไม่เจอค่ะ ช่วยบอกชื่อซอยหรือถนน หรือสถานที่ใกล้ๆ เพิ่มได้ไหมคะ", "I couldn't find that yet. Can you tell me the soi or road name, or a place nearby?"),
    "people": ("ตอนนี้มีกี่คนอยู่ด้วยกันคะ", "How many people are with you?"),
    "vulnerable": ("มีผู้สูงอายุ เด็กเล็ก คนป่วย หรือคนที่เดินไม่ได้ไหมคะ", "Is anyone elderly, a small child, sick, or unable to walk?"),
    "depth": ("ตอนนี้น้ำสูงแค่ไหนคะ เทียบกับร่างกายก็ได้ เช่น ถึงเข่า ถึงเอว", "How high is the water now? Compared with your body is fine, like knee or waist."),
    "askBack": ("น้ำอยู่สูงกว่าหรือต่ำกว่าลูกบิดประตูคะ", "Is the water above or below your door handle?"),
    "nb_confirm": ("บ้าน{side}ของคุณ คือหลังที่ขอบสีส้มในรูปนี้ใช่ไหมคะ (บ้านคุณสีเหลือง) ตอบ ใช่ / ไม่ใช่",
                   "Is your neighbour's house to the {side} the one outlined orange in this picture? (Yours is yellow.) Reply yes / no"),
    "nb_confirm_next": ("แล้วหลังนี้ล่ะคะ ใช่ไหม", "What about this one?"),
    "nb_unsure": ("ไม่เป็นไรค่ะ เราจะใช้บ้านที่ใกล้ที่สุดทางนั้นไว้ก่อน และทีมจะตรวจอีกที", "That's fine. We'll use the nearest house that way for now, and a team will check."),
    "nb_dir": ("บ้านที่คุณพูดถึง อยู่ทิศไหนของบ้านคุณคะ เหนือ ใต้ ตะวันออก หรือตะวันตก",
               "Which direction is the house you mentioned from yours: north, south, east or west?"),
    "shelter": ("ถ้าออกจากบ้านเองได้ ศูนย์พักพิงที่ใกล้ที่สุดคือ {name} ห่างราว {km} กม. (เดินราว {minutes} นาที) ทางที่ลึกที่สุดราว {deep} ม. ไปเองได้ไหมคะ ตอบ \"ไป\" หรือ \"อยู่บ้าน\"",
                "If you can leave on your own, the nearest shelter is {name}, about {km} km away (about {minutes} min on foot). The deepest water on the way is about {deep} m. Can you go there? Reply \"go\" or \"stay\"."),
    "shelter_go": ("ดีค่ะ เดินไปทาง {name} ช้าๆ อยู่ห่างคลองและท่อระบายน้ำ ถ้าน้ำลึกเกินเข่าให้หยุดและบอกเรา เมื่อถึงแล้วพิมพ์ว่า \"ถึงแล้ว\" นะคะ",
                   "Good. Walk slowly towards {name}, away from canals and drains. If the water goes above your knees, stop and tell us. When you arrive, type \"arrived\"."),
    "shelter_stay": ("ได้ค่ะ อยู่ที่บ้าน ขึ้นที่สูง ปิดไฟฟ้าชั้นล่าง เราแจ้งทีมอาสาให้แล้ว", "OK. Stay at home, go to the highest floor and switch off the power downstairs. We've told the volunteer teams."),
    "shelter_none": ("ตอนนี้ทางไปศูนย์พักพิงที่ใกล้ที่สุด ({name}) มีน้ำลึกราว {deep} ม. ยังไม่ควรเดินไปเองค่ะ ขึ้นที่สูงไว้ก่อน เราแจ้งทีมเรือแล้ว",
                     "The way to the nearest shelter ({name}) has water about {deep} m deep, so please don't walk there now. Go to the highest floor; we've told the boat teams."),
    "urgent_done": ("รับทราบค่ะ เป็นกรณีด่วน เรื่องของคุณขึ้นเป็นลำดับแรกแล้ว หากมีคนหายใจไม่ออกหรือบาดเจ็บ โทร 1669 ทันทีค่ะ",
                    "Understood. This is urgent, and your case is at the top now. If anyone can't breathe or is injured, call 1669 now."),
    "done": ("ขอบคุณค่ะ ข้อมูลของคุณอยู่ในระบบแล้ว เมื่อมีทีมวางแผนเข้าโซนของคุณ เราจะแจ้งทันที และจะถามไถ่เป็นระยะนะคะ",
             "Thank you. You're in our system. When a team plans to come to your zone we'll tell you right away, and we'll check on you regularly."),
    "known": ("บ้านหลังนั้นอยู่ในระบบแล้วค่ะ และมีคนวางแผนช่วยอยู่ ขอบคุณที่บอกนะคะ", "We already know about that house, and help is planned. Thank you."),
    "known_noplan": ("บ้านหลังนั้นอยู่ในระบบแล้วค่ะ ขอบคุณที่บอกนะคะ", "We already know about that house. Thank you."),
    "new": ("เพิ่มบ้านหลังนั้นให้แล้วค่ะ เราจะพยายามติดต่อพวกเขา", "We've added that house. We'll try to contact them."),
    "none": ("รับทราบค่ะ", "Got it."),
    "reply_ok": ("ขอบคุณที่ตอบค่ะ เราอัปเดตข้อมูลแล้ว", "Thanks for answering. We've updated your details."),
}
NONE_WORDS = re.compile(r"^(ไม่มี|ไม่|ว่าง|ไม่รู้|ไม่ทราบ|ไม่แน่ใจ|ออกไปแล้ว|no|none|nobody|empty|don'?t know|not sure|left already)\b", re.I)
VAGUE = re.compile(r"เยอะ|มาก|สูง(มาก)?$|ท่วม(หนัก)?$|a lot|deep|high", re.I)
CITY_HINT = " หาดใหญ่ สงขลา"


SIDE_TH = {"north": "ทางทิศเหนือ", "south": "ทางทิศใต้", "east": "ทางทิศตะวันออก", "west": "ทางทิศตะวันตก"}


def side_word(side: str, lang: str) -> str:
    return SIDE_TH.get(side, "") if lang == "th" else side


def say(key: str, lang: str, **kw) -> str:
    text = Q[key][0 if lang == "th" else 1]
    return text.format(**kw) if kw else text


def lang_of(text: str, default="th") -> str:
    if re.search(r"[฀-๿]", text or ""):
        return "th"
    return "en" if re.search(r"[A-Za-z]{2,}", text or "") else default


@dataclass
class Session:
    id: str
    token: str
    lang: str = "th"
    household_id: str | None = None
    pin: dict | None = None
    building_id: str | None = None
    zone_id: str | None = None
    facts: dict = field(default_factory=dict)
    asked: list[str] = field(default_factory=list)
    pending: str | None = "intro"
    transcript: list[dict] = field(default_factory=list)
    neighbour_results: list[dict] = field(default_factory=list)
    shelter_offer: dict | None = None  # the walkable shelter the agent suggested
    nb_queue: list = field(default_factory=list)   # neighbours mentioned, waiting for direction / picture confirmation
    finished: bool = False

    def view(self):
        return {"id": self.id, "token": self.token, "lang": self.lang, "householdId": self.household_id, "pin": self.pin,
                "buildingId": self.building_id, "zoneId": self.zone_id, "facts": self.facts, "transcript": self.transcript,
                "neighbours": self.neighbour_results, "pending": self.pending, "finished": self.finished}


def new_session(lang: str = "th") -> Session:
    s = Session(secrets.token_hex(4), secrets.token_urlsafe(9), lang)
    s.transcript.append({"role": "agent", "text": say("intro", lang)})
    return s


def locate(text: str, geo: G.Geo) -> dict | None:
    """Address words → a point on a building. Pinpoint first; a street-name match in the city as the stand-in."""
    from api.location.pinpoint import geocode
    g = geocode(text + CITY_HINT)
    if g:
        lon, lat = g["at"]
        if geo.zone_at(lon, lat):
            b = geo.snap(lon, lat, 60)
            if b:
                return {"lon": b.lon, "lat": b.lat, "precision": "address", "buildingId": b.id, "zoneId": b.zone_id,
                        "label": g.get("label"), "by": "pinpoint"}
    # stand-in: the longest street name in the city that appears in the words, then a house on it
    low = text.lower()
    best = None
    for s in geo.streets:
        for name in (s.get("nameTh"), s.get("name")):
            if name and len(name) >= 6 and name.lower() in low and (best is None or len(name) > len(best[0])):
                best = (name, s)
    if best:
        name, s = best
        num = re.search(r"(\d+)\s*/\s*(\d+)|เลขที่\s*(\d+)", text)
        pts = s["_m"]
        k = (int(num.group(1) or num.group(3)) % len(pts)) if num else len(pts) // 2
        x, y = pts[k]
        lon, lat = G.to_ll(x, y)
        b = geo.snap(lon, lat, 80)
        if b and b.zone_id:
            return {"lon": b.lon, "lat": b.lat, "precision": "address", "buildingId": b.id, "zoneId": b.zone_id,
                    "label": name, "by": "street match (stand-in)"}
    return None


def _merge(s: Session, r: Read):
    for f in r.facts:
        if f.field in ("neighbour", "about", "forwarded"):
            continue
        s.facts[f.field] = {"value": f.value, "quote": f.quote}


def _next(s: Session) -> str | None:
    f = s.facts
    if not s.pin:
        return "where" if "where" not in s.asked else "where_again"
    if "people" not in f and "people" not in s.asked:
        return "people"
    if not any(k in f for k in ("elderly", "children", "cannotWalk")) and "vulnerable" not in s.asked:
        return "vulnerable"
    if "depthRange" not in f and "depth" not in s.asked:
        return "depth"
    if "depthRange" in f and VAGUE.search(f["depthRange"]["quote"]) and "askBack" not in s.asked:
        return "askBack"
    if f.get("urgent", {}).get("value") is True:
        return None
    # neighbours only come up when the person mentions one: then ask which way that house is
    if s.nb_queue:
        return "nb_dir" if s.nb_queue[0]["nb"].get("side") not in G.DIRECTIONS else "nb_confirm"
    # people who can leave on their own: offer the nearest shelter they can walk to
    if s.shelter_offer and "shelter" not in s.asked and not f.get("cannotWalk", {}).get("value"):
        return "shelter"
    return None
