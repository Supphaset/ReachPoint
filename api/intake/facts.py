"""Caller-reported flood facts and the next intake topic."""

from pydantic import ConfigDict, Field

from api.intake.schema import HelpRequestDetails

DISPATCH_NOTICE = "ยังไม่ได้ส่งคำขอ และยังไม่มีทีมยืนยันค่ะ"
LOCATION_QUESTION = "ตอนนี้อยู่ที่ไหนคะ? ส่งลิงก์ Google Maps หรือบอกจุดสังเกตได้ค่ะ"
OPTIONAL_FIELDS = ("people_details", "situation_details", "water_level")
OPTIONAL_QUESTIONS = {
    "people_situation": "มีใครอยู่ด้วย และสถานการณ์ตอนนี้เป็นอย่างไรคะ? ตอบสั้น ๆ หรือบอกว่าข้ามได้ค่ะ",
    "people": "มีเด็ก ผู้สูงอายุ ผู้ป่วย หรือสัตว์เลี้ยงอยู่ด้วยไหมคะ? ข้ามได้ค่ะ",
    "situation": "สถานการณ์ตอนนี้เป็นอย่างไรคะ? ข้ามได้ค่ะ",
    "people_water": "มีใครอยู่ด้วย และตอนนี้น้ำสูงถึงไหนคะ? ข้ามได้ค่ะ",
    "water": "ตอนนี้น้ำสูงถึงไหนคะ? ข้ามได้ค่ะ",
}


def is_optional_prompt(text: str) -> bool:
    return any(text.endswith(question) for question in OPTIONAL_QUESTIONS.values())


class FloodCase(HelpRequestDetails):
    """Request details plus conversation-only state; unknown values stay explicit."""

    # Older saved conversations may contain removed fields.
    model_config = ConfigDict(extra="ignore")
    immediate_danger: bool | None = None
    unavailable_fields: list[str] = Field(default_factory=list)
    contradictions: list[str] = Field(default_factory=list)


def next_question(case: FloodCase) -> str | None:
    """Three essentials and at most one optional people/situation prompt."""
    def missing(field: str) -> bool:
        return getattr(case, field) is None and field not in case.unavailable_fields

    if not case.location:
        return LOCATION_QUESTION
    if case.contradictions:
        return "ขอยืนยันข้อมูลนี้ค่ะ: " + case.contradictions[0]
    if case.type is None:
        return "ต้องการอาหาร หรืออพยพคะ?"
    if not case.phone_number:
        return "ขอเบอร์โทรศัพท์ที่ติดต่อได้ค่ะ"
    if case.immediate_danger:
        return None
    if missing("water_level"):
        return OPTIONAL_QUESTIONS["people_water" if missing("people_details") else "water"]
    if missing("people_details"):
        return OPTIONAL_QUESTIONS["people_situation" if missing("situation_details") else "people"]
    return OPTIONAL_QUESTIONS["situation"] if missing("situation_details") else None


def render_fields(case: HelpRequestDetails, *, concise: bool = False) -> str:
    """Render the shared fields directly, without model-generated count breakdowns."""
    def value(field: str) -> str:
        content = getattr(case, field)
        return "ยังไม่ทราบ / ยังไม่ได้แจ้ง" if content is None else str(content)

    rows = [
        ("เบอร์โทรศัพท์", value("phone_number")),
        ("ประเภทความช่วยเหลือ", {"food": "อาหาร", "evacuation": "อพยพ"}.get(case.type, "ยังไม่ทราบ / ยังไม่ได้แจ้ง")),
        ("รายละเอียดผู้ประสบภัย", value("people_details")),
        ("เด็ก", value("n_children") + (" คน" if case.n_children is not None else "")),
        ("ผู้สูงอายุ", value("n_elders") + (" คน" if case.n_elders is not None else "")),
        ("สัตว์เลี้ยง", value("n_pets") + (" ตัว" if case.n_pets is not None else "")),
        ("ตำแหน่ง", value("location")),
        ("พิกัด", value("coordinates")), ("ระดับน้ำ", value("water_level")),
        ("รายละเอียดตำแหน่ง", value("location_details")),
        ("สถานการณ์", value("situation_details")),
        ("เหตุฉุกเฉิน", value("emergency_detail")),
        ("ข้อมูลอื่น", value("other_details")),
    ]
    if concise:
        # Review the same five form fields; retain extra details only when supplied.
        by_label = dict(rows)
        primary = ("เบอร์โทรศัพท์", "ประเภทความช่วยเหลือ", "ตำแหน่ง", "รายละเอียดผู้ประสบภัย", "สถานการณ์")
        rows = [(label, by_label[label]) for label in primary] + [
            (label, by_label[label]) for field, label in (
                ("n_children", "เด็ก"), ("n_elders", "ผู้สูงอายุ"), ("n_pets", "สัตว์เลี้ยง"),
                ("coordinates", "พิกัด"), ("water_level", "ระดับน้ำ"), ("location_details", "รายละเอียดตำแหน่ง"),
                ("emergency_detail", "เหตุฉุกเฉิน"), ("other_details", "ข้อมูลอื่น"),
            ) if getattr(case, field) is not None
        ]
    return ("\n" if concise else "\n\n").join(f"{label}: {content}" for label, content in rows)


def render_summary(case: FloodCase) -> str:
    summary = "สรุปคำขอค่ะ\n" + render_fields(case, concise=True)
    summary += "\n\n" + DISPATCH_NOTICE
    summary += "\nหากถูกต้อง กดยืนยันหรือพูดว่า ยืนยันส่งคำขอ แก้ไขข้อมูลได้ค่ะ"
    if case.immediate_danger:
        summary = "ผู้แจ้งระบุอันตรายเฉียบพลัน หากโทรได้ให้ติดต่อ 1784 หรือ 1669 เมื่อมีเหตุเจ็บป่วยฉุกเฉิน โดยไม่ต้องรอกรอกข้อมูลครบค่ะ\n\n" + summary
    return summary
