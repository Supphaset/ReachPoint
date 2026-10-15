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
    zones = re.findall(r"\b([ABC]-\d{1,2})\b", t)
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
