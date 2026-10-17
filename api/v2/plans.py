"""A volunteer's one-line plan → team, vehicle, seats, zones (in order), time and what they offer.

Rules first (zone codes, times, seat counts, known vehicles); Gemini reads looser wording in api/v2/ai.py.
"""

from __future__ import annotations

import re

VEHICLES = {"เรือ": "boat", "boat": "boat", "เจ็ทสกี": "jet ski", "jet ski": "jet ski", "รถยกสูง": "high truck",
            "รถบรรทุก": "truck", "truck": "truck", "รถกระบะ": "pickup", "pickup": "pickup"}
OFFERS = {"อพยพผู้ป่วย": "medical evacuation", "การแพทย์": "medical", "แพทย์": "medical", "medical": "medical",
          "อพยพ": "evacuation", "evacuat": "evacuation", "อาหาร": "food and water", "food": "food and water", "น้ำดื่ม": "food and water"}


def parse_plan(text: str) -> dict:
    t = text or ""
    # team zones are radio-style codes: a sector letter (no I or O) and a number, "A3", "C14" (old "B-7" still read)
    zones = [z.upper().replace("-", "") for z in re.findall(r"(?<![A-Za-z0-9])([A-HJ-NP-Za-hj-np-z]-?\d{1,2})(?![0-9])", t)]
    m = re.search(r"(\d{1,2})[:.](\d{2})", t)
    eta = f"{int(m.group(1)):02d}:{m.group(2)}" if m else None
    if not eta:
        m2 = re.search(r"บ่าย\s*(สอง|สาม|สี่|โมง)|(\d{1,2})\s*(pm|am)", t, re.I)
        if m2:
            eta = {"สอง": "14:00", "สาม": "15:00", "สี่": "16:00", "โมง": "13:00"}.get(m2.group(1) or "") or \
                  f"{(int(m2.group(2)) % 12) + (12 if (m2.group(3) or '').lower() == 'pm' else 0):02d}:00"
    seats = re.search(r"(\d+)\s*(ที่นั่ง|ที่|seats?)", t)
    vehicle = next((v for k, v in VEHICLES.items() if k in t.lower()), None)
    offer = next((v for k, v in OFFERS.items() if k in t.lower()), None)
    team = re.split(r"\s*(\d|จะ|ไป|เข้า|ประมาณ|going|will|plans?\b|,)", t)[0].strip()[:40] or None
    return {"team": team, "vehicle": vehicle, "seats": int(seats.group(1)) if seats else None, "zones": zones,
            "eta": eta, "offers": offer}


def _norm(s: str) -> str:
    """Street names as people say them: no "ถนน"/"ซอย"/"Thanon"/"Soi", no spaces, the two common spellings of ราษฎร์."""
    s = re.sub(r"ถนน|ถ\.|ซอย|ซ\.|thanon|soi|road|rd\.?", "", (s or "").lower())
    return re.sub(r"\s+", "", s.replace("ฏ", "ฎ"))


def _named(k: str, t: str) -> bool:
    """k appears in t as a whole name: not the start of a longer numbered soi ("ราษฎร์อุทิศ" in "ราษฎร์อุทิศ15")."""
    i = t.find(k)
    while i >= 0:
        nxt = t[i + len(k): i + len(k) + 1]
        if not nxt.isdigit() and nxt not in ("/",):
            return True
        i = t.find(k, i + 1)
    return False


def places(text: str, geo) -> tuple[list[str], list[str]]:
    """Zones and blocks a plan line names by street: "เรือเข้าซอยราษฎร์อุทิศ 15" → the block(s) on that soi and their
    zone. The longest names are tried first, so "ราษฎร์อุทิศ 15" wins over "ราษฎร์อุทิศ"."""
    # times and seat counts are not soi numbers: "แสงอาทิตย์ 15:00", "8 ที่"
    t = _norm(re.sub(r"\d{1,2}[:.]\d{2}|\d+\s*(ที่นั่ง|ที่|seats?|คน|people)|(?<![A-Za-z0-9])[A-HJ-NP-Z]-?\d{1,2}(?![0-9])", " ", text or "", flags=re.I))
    blocks, zones = [], []
    names = sorted({(b["properties"].get("name") or "") for b in geo.blocks if b["properties"].get("name")}, key=len, reverse=True)
    hit = []
    for n in names:
        k = _norm(n)
        if len(k) >= 4 and _named(k, t) and not any(k in h for h in hit):
            hit.append(k)
            for b in geo.blocks:
                if b["properties"].get("name") == n:
                    blocks.append(b["properties"]["id"])
                    if b["properties"]["zoneId"] not in zones:
                        zones.append(b["properties"]["zoneId"])
    # any street by name: the blocks it runs through ("ซอยราษฎร์อุทิศ 15" even when no block is named after it)
    for k, bids in sorted(_street_blocks(geo).items(), key=lambda kv: len(kv[0]), reverse=True):
        if len(k) >= 5 and _named(k, t) and not any(k in h for h in hit):
            hit.append(k)
            for bid in bids:
                if bid not in blocks:
                    blocks.append(bid)
                z = bid.split("·")[0]
                if z not in zones:
                    zones.append(z)
    for z in geo.zones:  # a zone named by its road ("แถวถนนแสงอาทิตย์") counts as the whole zone
        k = _norm(z["properties"].get("name") or "")
        if len(k) >= 4 and _named(k, t) and z["properties"]["id"] not in zones and not any(k in h for h in hit):
            zones.append(z["properties"]["id"])
    return zones, blocks


_SB: dict | None = None


def _street_blocks(geo) -> dict[str, list[str]]:
    """Street name (normalised) → the blocks of the buildings along it (within ~25 m of its line)."""
    global _SB
    if _SB is None:
        from api.v2 import geo as G
        out: dict[str, set] = {}
        for st in geo.streets:
            name = st.get("nameTh") or st.get("name")
            if not name:
                continue
            k = _norm(name)
            coords = st["coordinates"] if isinstance(st["coordinates"][0][0], float) else [p for part in st["coordinates"] for p in part]
            for lon, lat in coords[:: max(1, len(coords) // 12)]:
                for b in geo.near(*G.to_m(lon, lat), 25):
                    if b.block_id:
                        out.setdefault(k, set()).add(b.block_id)
        _SB = {k: sorted(v) for k, v in out.items()}
    return _SB
