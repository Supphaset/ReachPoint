"""Reader: one message → facts, each with the exact words it came from.

`read_rules` is the deterministic reader: it never stalls and runs in tests. `api/v2/ai.py` asks Gemini for the same
schema; the pipeline uses Gemini's facts when they exist (cached for the scenario, live for the judge) and these
rules otherwise. Facts never include anything not in the words: no guessed counts, places or names.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field

from api.v2.depth_words import depth_from_words

THAI_DIGITS = str.maketrans("๐๑๒๓๔๕๖๗๘๙", "0123456789")
NUM_TH = {"หนึ่ง": 1, "สอง": 2, "สาม": 3, "สี่": 4, "ห้า": 5, "หก": 6, "เจ็ด": 7, "แปด": 8}


@dataclass
class Fact:
    field: str
    value: object
    quote: str


@dataclass
class Read:
    facts: list[Fact] = field(default_factory=list)
    reader: str = "rules"

    def get(self, name, default=None):
        for f in self.facts:
            if f.field == name:
                return f.value
        return default

    def quote(self, name) -> str | None:
        for f in self.facts:
            if f.field == name:
                return f.quote
        return None

    def to_json(self):
        return {"reader": self.reader, "facts": [asdict(f) for f in self.facts]}


def _num(s: str) -> int | None:
    s = s.translate(THAI_DIGITS)
    if s.isdigit():
        return int(s)
    return NUM_TH.get(s)


NEIGHBOUR = re.compile(r"(บ้าน(ทาง)?(ซ้ายมือ|ขวามือ|ฝั่งตรงข้าม|ตรงข้าม|ติดกัน|ข้างหลัง|ด้านหลัง)|the house (on (our|my) (left|right)|across the street|next door|behind))(.{0,80})", re.I)
SIDE = {"ซ้ายมือ": "left", "ขวามือ": "right", "ฝั่งตรงข้าม": "across", "ตรงข้าม": "across", "ติดกัน": "next",
        "ข้างหลัง": "behind", "ด้านหลัง": "behind", "left": "left", "right": "right", "across the street": "across",
        "next door": "next", "behind": "behind"}


def read_rules(text: str, channel: str = "chat") -> Read:
    t = (text or "").strip()
    r = Read()
    low = t.lower()
    own, nb_text = t, None
    m = NEIGHBOUR.search(t)
    if m:
        own, nb_text = t[:m.start()], t[m.start():]
    d = depth_from_words(own)
    if d:
        r.facts.append(Fact("depthRange", [d[0], d[1]], d[2]))
    m2 = re.search(r"อยู่คนเดียว|I'?m alone|alone", own, re.I)
    if m2:
        r.facts.append(Fact("people", 1, m2.group(0)))
    else:
        m2 = re.search(r"(อยู่(กัน)?|มี(คน)?)\s*([0-9๐-๙]+|หนึ่ง|สอง|สาม|สี่|ห้า|หก|เจ็ด|แปด)\s*คน|(\d+) of us|(\d+) people", own, re.I)
        if m2:
            n = _num(m2.group(4) or m2.group(5) or m2.group(6) or "")
            if n:
                r.facts.append(Fact("people", n, m2.group(0)))
    for name, pat in (("elderly", r"(ผู้สูงอายุ|คนแก่|ผู้สูงวัย)\s*([0-9๐-๙]+)?\s*คน?|(\d+) elderly|grandma|grandpa|ยาย|ตา\b"),
                      ("children", r"(เด็ก(เล็ก)?)\s*([0-9๐-๙]+)\s*คน|(\d+) (kids|children)")):
        m3 = re.search(pat, own, re.I)
        if m3:
            nums = [g for g in m3.groups() if g and (g.isdigit() or g.translate(THAI_DIGITS).isdigit())]
            r.facts.append(Fact(name, _num(nums[0]) if nums else 1, m3.group(0)))
    m4 = re.search(r"เดินไม่ได้|ติดเตียง|can'?t walk|bedridden|wheelchair", own, re.I)
    if m4:
        r.facts.append(Fact("cannotWalk", 1, m4.group(0)))
    m5 = re.search(r"ด่วน|หายใจไม่|ไม่ไหวแล้ว|need help now|urgent|can'?t breathe|drowning", t, re.I)
    if m5:
        r.facts.append(Fact("urgent", True, m5.group(0)))
    m6 = re.search(r"ยังปลอดภัย|ปลอดภัยดี|ทุกคนปลอดภัย|อพยพแล้ว|ออกมาแล้ว|still ok|we('re| are)( all)? safe|evacuated", t, re.I)
    if m6:
        r.facts.append(Fact("safe", "evacuated" if re.search(r"อพยพแล้ว|ออกมาแล้ว|evacuated", m6.group(0), re.I) else True, m6.group(0)))
    m7 = re.search(r"(ยัง)?ขึ้น(อยู่|เรื่อยๆ)|น้ำขึ้น|still rising|rising", t, re.I)
    if m7:
        r.facts.append(Fact("trend", "rising", m7.group(0)))
    elif re.search(r"ทรงตัว|steady|holding", t, re.I):
        q = re.search(r"ทรงตัว|steady|holding", t, re.I).group(0)
        r.facts.append(Fact("trend", "steady", q))
    elif re.search(r"ลดลง|falling|going down", t, re.I):
        r.facts.append(Fact("trend", "falling", re.search(r"ลดลง|falling|going down", t, re.I).group(0)))
    m8 = re.search(r"ส่งต่อ|forwarded|fwd", t, re.I)
    if m8:
        r.facts.append(Fact("forwarded", True, m8.group(0)))
    if channel == "post" or re.search(r"ญาติ|แม่ของเพื่อน|ยายผม|ครอบครัวพี่|เพื่อนบ้าน|my (mom|mother|grandma|relative)", own, re.I):
        rel = re.search(r"ญาติ\S*|แม่ของเพื่อน|ยายผม|ครอบครัวพี่สาว|เพื่อนบ้าน|my \w+", own, re.I)
        if rel:
            r.facts.append(Fact("about", "relative", rel.group(0)))
    m9 = re.search(r"(บ้านเลขที่\s*[0-9/]+[^ใ]*?)(?=\s*ใกล้|$)|(house [0-9/]+[^.]*)", own)
    if m9:
        r.facts.append(Fact("address", (m9.group(1) or m9.group(2)).strip(), (m9.group(1) or m9.group(2)).strip()))
    if nb_text:
        side_word = m.group(3) or m.group(5) or ""
        side = SIDE.get(side_word.lower(), SIDE.get(side_word, "next"))
        nb = {"side": side}
        rest = m.group(0)
        if re.search(r"ยาย|old lady|grandma", rest, re.I) and re.search(r"คนเดียว|alone", rest, re.I):
            nb.update(people=1, elderly=1)
        mm = re.search(r"ครอบครัว\s*([0-9]+)\s*คน|family of (\d+)", rest, re.I)
        if mm:
            nb["people"] = int(mm.group(1) or mm.group(2))
        mk = re.search(r"เด็ก\s*([0-9]+)\s*คน|(\d+) kids", rest, re.I)
        if mk:
            nb["children"] = int(mk.group(1) or mk.group(2))
        r.facts.append(Fact("neighbour", nb, rest.strip()))
    return r


COUNT_FIELDS = ("people", "elderly", "children", "cannotWalk")


def normalise(field: str, value):
    """A model's value in the shape the pipeline expects; None drops the fact. Counts become integers (a vague
    'some' / 'yes' counts as at least 1 for vulnerable groups, never for the total); flags become booleans."""
    if field in COUNT_FIELDS:
        if isinstance(value, bool):
            return (1 if value else None) if field != "people" else None
        if isinstance(value, (int, float)):
            return int(value) if value >= 0 else None
        if isinstance(value, str):
            m = re.search(r"\d+", value.translate(THAI_DIGITS))
            if m:
                return int(m.group(0))
            if field != "people" and re.search(r"some|yes|มี|true|one|person|people", value, re.I):
                return 1
        return None
    if field == "urgent":
        return value is True or (isinstance(value, str) and value.lower() in ("true", "yes"))
    if field == "safe":
        if isinstance(value, str):
            return "evacuated" if "evac" in value.lower() else value.lower() in ("true", "yes", "safe")
        return value
    if field == "forwarded":
        return value is True or (isinstance(value, str) and value.lower() == "true")
    if field == "trend":
        return value if value in ("rising", "steady", "falling") else None
    if field == "neighbour":
        if not isinstance(value, dict):
            return None
        out = {"side": value.get("side") if value.get("side") in ("left", "right", "across", "behind", "next") else "next"}
        for k in ("people", "elderly", "children"):
            v = normalise(k, value.get(k)) if value.get(k) is not None else None
            if v:
                out[k] = v
        return out
    return value
