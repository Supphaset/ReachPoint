"""Caller-reported flood facts and the next intake topic.

Order of questions: what is happening and where, who is there, the situation, then an optional callback number
and last an optional name for the team to call out on arrival. A name is not needed to verify a request (teams
verify by calling back), so it never delays help; age is not asked (children, elderly and mobility cover it).
"""

from pydantic import BaseModel, Field

DISPATCH_NOTICE = {
    "th": "ยังไม่ได้บันทึกคำขอ กรุณายืนยันสรุปก่อนส่งให้ผู้ประสานงานตรวจสอบ ยังไม่มีทีมเข้าช่วยเหลือหรือเวลาถึงพื้นที่ที่ยืนยันแล้ว",
    "en": "Your request is not saved yet. Confirm the summary to send it to a coordinator for review. No team or arrival time is confirmed yet.",
}
SUMMARY_TOPIC = "SUMMARY"


class FloodCase(BaseModel):
    """Facts reported by the user, with unknown values kept explicit."""

    reporter_name: str | None = None
    people_count: int | None = Field(default=None, ge=1)
    people_details: str | None = None
    children_count: int | None = Field(default=None, ge=0)
    elderly_count: int | None = Field(default=None, ge=0)
    mobility_needs: str | None = None
    location: str | None = None
    landmark: str | None = None
    coordinates: str | None = None
    water_level: str | None = None
    water_trend: str | None = None
    current_shelter: str | None = None
    injuries: str | None = None
    urgent_needs: str | None = None
    immediate_danger: bool | None = None
    danger_details: str | None = None
    callback_contact: str | None = None
    unavailable_fields: list[str] = Field(default_factory=list)
    contradictions: list[str] = Field(default_factory=list)


def next_topic(case: FloodCase) -> str:
    """Ask only for missing facts; prioritize location for explicit danger."""
    def missing(field: str) -> bool:
        return getattr(case, field) is None and field not in case.unavailable_fields

    if case.immediate_danger and missing("location"):
        return "ฉุกเฉิน: ถามตำแหน่ง/จังหวัด/จุดสังเกตก่อน และแนะนำช่องทางฉุกเฉินตามอาการที่แจ้ง ไม่ถามชื่อก่อน"
    if case.contradictions:
        return "ขอให้ยืนยันข้อมูลที่ขัดกัน: " + "; ".join(case.contradictions)
    if missing("people_count") or missing("people_details"):
        return "ถามเฉพาะข้อมูลที่ขาดเรื่องจำนวนคนรวมผู้แจ้ง และเด็ก/ผู้สูงอายุ/ผู้ที่ต้องการความช่วยเหลือพิเศษ"
    if missing("location"):
        return "ถามที่อยู่ จังหวัด จุดสังเกต และพิกัดถ้าสะดวก ไม่ต้องรอพิกัดถ้ามีที่อยู่แล้ว"
    fields = {
        "water_level": "ระดับน้ำ",
        "water_trend": "น้ำยังเพิ่มขึ้นหรือไม่",
        "current_shelter": "ตอนนี้ทุกคนอยู่ส่วนไหน",
        "injuries": "มีผู้บาดเจ็บหรือไม่",
        "urgent_needs": "ต้องการความช่วยเหลืออะไรเร่งด่วน",
    }
    needed = [label for field, label in fields.items() if missing(field)]
    if needed:
        return "ถามสถานการณ์เฉพาะข้อมูลที่ยังขาด: " + ", ".join(needed)
    if missing("callback_contact"):
        return "ถามเบอร์โทรติดต่อกลับ (ไม่บังคับ ข้ามได้) เพื่อให้ทีมโทรยืนยันก่อนออกไป"
    if missing("reporter_name"):
        return "ถามชื่อที่ให้ทีมเรียกเมื่อไปถึง (ไม่บังคับ ข้ามได้)"
    return SUMMARY_TOPIC


LABELS = {
    "reporter_name": ("ชื่อที่ให้ทีมเรียก", "Name for the team to call out"),
    "people_count": ("จำนวนคนรวม", "People in total"), "people_details": ("รายละเอียดผู้ประสบภัย", "Who is there"),
    "children_count": ("เด็ก", "Children"), "elderly_count": ("ผู้สูงอายุ", "Elderly"),
    "mobility_needs": ("การเคลื่อนไหว / ความช่วยเหลือพิเศษ", "Mobility / special help"),
    "location": ("ตำแหน่ง", "Location"), "landmark": ("จุดสังเกต", "Landmark"), "coordinates": ("พิกัด", "Coordinates"),
    "water_level": ("ระดับน้ำ", "Water level"), "water_trend": ("แนวโน้มน้ำ", "Water rising?"),
    "current_shelter": ("จุดที่พักอยู่", "Where everyone is now"), "injuries": ("การบาดเจ็บ", "Injuries"),
    "urgent_needs": ("ความช่วยเหลือที่ต้องการ", "Help needed"), "callback_contact": ("ติดต่อกลับ (ไม่บังคับ)", "Callback (optional)"),
}
UNIT = {"people_count": ("คน", "people"), "children_count": ("คน", ""), "elderly_count": ("คน", "")}


def render_summary(case: FloodCase, lang: str = "th") -> str:
    """Render reported fields directly, without model-generated count breakdowns, in the caller's language."""
    i = 0 if lang == "th" else 1
    unknown = ("ยังไม่ทราบ / ยังไม่ได้แจ้ง", "not known / not given")[i]

    def value(field: str) -> str:
        content = getattr(case, field)
        if content is None:
            return unknown
        unit = UNIT.get(field, ("", ""))[i]
        return f"{content} {unit}".strip()

    head = ("สรุปคำขอความช่วยเหลือ กรุณาตรวจทานข้อมูลค่ะ", "Summary of your request. Please check it.")[i]
    summary = head + "\n\n" + "\n\n".join(f"{LABELS[f][i]}: {value(f)}" for f in LABELS)
    summary += "\n\n" + DISPATCH_NOTICE["th" if i == 0 else "en"]
    summary += "\n\n" + ("หากต้องแก้ไขข้อมูลหรือสถานการณ์เปลี่ยนไป แจ้งได้เลยค่ะ หากถูกต้อง กรุณากดยืนยันส่งคำขอค่ะ",
                          "If anything is wrong or changes, just tell me. If it is right, press Confirm and send.")[i]
    if case.immediate_danger:
        summary = ("ผู้แจ้งระบุอันตรายเฉียบพลัน หากโทรได้ให้ติดต่อ 1784 หรือ 1669 เมื่อมีเหตุเจ็บป่วยฉุกเฉิน โดยไม่ต้องรอกรอกข้อมูลครบค่ะ",
                   "You reported immediate danger. If you can call, phone 1784 (disaster) or 1669 (medical) now; don't wait to finish this.")[i] \
            + "\n\n" + summary
    return summary
