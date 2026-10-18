"""Everyday words about water → a depth range in metres. The rule fallback for the Analyst; Gemini does the same
job live and is checked against these bands in the evaluation.

Body references assume an adult standing on the ground floor. Ranges are deliberately wide.
"""

from __future__ import annotations

import re

# (pattern, lo, hi, label). Order matters: more specific first.
BANDS: list[tuple[str, float, float, str]] = [
    (r"หลังคา|roof", 3.0, 4.0, "roof"),
    (r"ชั้น\s*(สอง|2)|second floor|upstairs|2nd floor", 2.5, 3.2, "second floor"),
    (r"มิดหัว|ท่วมหัว|เหนือหัว|over (my|our) heads?|above (my )?head", 1.8, 2.3, "over head"),
    (r"(ถึง|แค่|ระดับ)?\s*คอ\b|ถึงคอ|neck", 1.4, 1.6, "neck"),
    (r"หน้าอก|ถึงอก|chest", 1.2, 1.4, "chest"),
    (r"ลูกบิด|door ?handle", 0.9, 1.1, "door handle"),
    (r"เอว|waist", 0.9, 1.1, "waist"),
    (r"ต้นขา|thigh", 0.6, 0.8, "thigh"),
    (r"เข่า|knee", 0.4, 0.6, "knee"),
    (r"หน้าแข้ง|แข้ง|shin|calf|น่อง", 0.2, 0.4, "shin"),
    (r"ข้อเท้า|ตาตุ่ม|ankle", 0.05, 0.2, "ankle"),
    (r"เข้าบ้าน|เข้ามาในบ้าน|ธรณีประตู|inside the house|coming in|through the door", 0.2, 0.5, "at the door"),
    (r"พื้นถนน|ท่วมถนน|on the road|road is flooded|street is flooded", 0.1, 0.4, "street"),
]
_METRES = re.compile(r"(\d+(?:[.,]\d+)?)\s*(เมตร|ม\.|m\b|metres?|meters?)", re.I)
_CM = re.compile(r"(\d+)\s*(ซม\.?|เซน(ติเมตร)?|cm)", re.I)
_BELOW = re.compile(r"ต่ำกว่า|ไม่ถึง|below|under|almost|เกือบ")
_ABOVE = re.compile(r"สูงกว่า|เกิน|เลย|above|over|more than")


def water_context(text: str, start: int = 0, end: int | None = None) -> bool:
    """Only nearby water words support a reported depth, not an unrelated body part or instruction."""
    window = text[max(0, start - 45): (end if end is not None else len(text)) + 45]
    return bool(re.search(r"\bwater\b|\bflood\w*|น้ำ|ท่วม", window, re.I))


def depth_from_words(text: str) -> tuple[float, float, str] | None:
    """The depth range a description implies, with the words it was read from; None when it says nothing."""
    t = (text or "").lower()
    m = _CM.search(t)
    if m and water_context(t, m.start(), m.end()):
        v = int(m.group(1)) / 100
        return round(max(0, v - 0.1), 2), round(v + 0.1, 2), m.group(0)
    m = _METRES.search(t)
    if m and water_context(t, m.start(), m.end()):
        v = float(m.group(1).replace(",", "."))
        return round(max(0, v - 0.2), 2), round(v + 0.2, 2), m.group(0)
    for pat, lo, hi, label in BANDS:
        m = re.search(pat, t)
        if m and water_context(t, m.start(), m.end()):
            # "a little below the handle" shifts down; "above the knee" shifts up.
            window = t[max(0, m.start() - 20): m.end() + 12]
            if _BELOW.search(window):
                lo, hi = round(lo - 0.2, 2), round(hi - 0.15, 2)
            elif _ABOVE.search(window):
                lo, hi = round(lo + 0.1, 2), round(hi + 0.2, 2)
            return max(0.0, lo), hi, m.group(0)
    return None


def words_for(depth_m: float, lang: str = "th") -> str:
    """The everyday phrase a person would use for a depth (used by the scenario generator)."""
    table = [(0.15, "น้ำถึงข้อเท้า", "water up to my ankles"), (0.35, "น้ำถึงหน้าแข้ง", "water up to my shins"),
             (0.55, "น้ำถึงเข่า", "water up to my knees"), (0.75, "น้ำถึงต้นขา", "water up to my thighs"),
             (1.05, "น้ำถึงเอว", "water up to my waist"), (1.35, "น้ำถึงหน้าอก", "water up to my chest"),
             (1.6, "น้ำถึงคอ", "water up to my neck"), (2.3, "น้ำท่วมมิดหัว", "water over our heads"),
             (3.2, "น้ำท่วมถึงชั้นสอง", "water up to the second floor"), (99, "น้ำท่วมถึงหลังคา", "water up to the roof")]
    for limit, th, en in table:
        if depth_m <= limit:
            return th if lang == "th" else en
    return table[-1][1]
