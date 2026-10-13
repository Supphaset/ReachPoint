"""Structured facts and the next intake topic; no dispatch integration."""

from pydantic import BaseModel, Field

DISPATCH_NOTICE = "ยังไม่ได้ส่งคำขอให้หน่วยงาน และยังไม่มีการยืนยันทีมเข้าช่วยเหลือหรือเวลาถึงพื้นที่"


class FloodCase(BaseModel):
    """Facts reported by the user, with unknown values kept explicit."""

    reporter_name: str | None = None
    reporter_age: int | None = Field(default=None, ge=0, le=130)
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
    if missing("reporter_name") and not case.immediate_danger:
        return "ถามชื่อและอายุ พร้อมบอกว่าไม่สะดวกแจ้งก็ข้ามได้"
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
    return "สรุปคำขอจากข้อมูลทั้งหมดให้ตรวจแก้ ระบุข้อมูลที่ยังไม่ทราบ ช่องทางติดต่อกลับเป็นทางเลือก และย้ำว่ายังไม่ได้ส่งเรื่อง/ไม่มีทีมยืนยัน"


def render_summary(case: FloodCase) -> str:
    """Render reported fields directly, without model-generated count breakdowns."""
    def value(field: str) -> str:
        content = getattr(case, field)
        return "ยังไม่ทราบ / ยังไม่ได้แจ้ง" if content is None else str(content)

    rows = [
        ("ผู้แจ้ง", value("reporter_name")),
        ("อายุ", value("reporter_age") + (" ปี" if case.reporter_age is not None else "")),
        ("จำนวนคนรวม", value("people_count") + (" คน" if case.people_count is not None else "")),
        ("รายละเอียดผู้ประสบภัย", value("people_details")),
        ("เด็ก", value("children_count") + (" คน" if case.children_count is not None else "")),
        ("ผู้สูงอายุ", value("elderly_count") + (" คน" if case.elderly_count is not None else "")),
        ("การเคลื่อนไหว / ความช่วยเหลือพิเศษ", value("mobility_needs")),
        ("ตำแหน่ง", value("location")), ("จุดสังเกต", value("landmark")),
        ("พิกัด", value("coordinates")), ("ระดับน้ำ", value("water_level")),
        ("แนวโน้มน้ำ", value("water_trend")), ("จุดที่พักอยู่", value("current_shelter")),
        ("การบาดเจ็บ", value("injuries")), ("ความช่วยเหลือที่ต้องการ", value("urgent_needs")),
        ("ติดต่อกลับ (ไม่บังคับ)", value("callback_contact")),
    ]
    summary = "สรุปคำขอความช่วยเหลือ กรุณาตรวจทานข้อมูลค่ะ\n\n"
    summary += "\n\n".join(f"{label}: {content}" for label, content in rows)
    summary += "\n\n" + DISPATCH_NOTICE
    summary += "\n\nหากมีข้อมูลที่ต้องแก้ไข หรือสถานการณ์เปลี่ยนไป แจ้งได้เลยค่ะ ช่องทางติดต่อกลับแจ้งเพิ่มได้หากสะดวก เพื่อใส่ในข้อความที่คุณคัดลอกเองค่ะ"
    if case.immediate_danger:
        summary = "ผู้แจ้งระบุอันตรายเฉียบพลัน หากโทรได้ให้ติดต่อ 1784 หรือ 1669 เมื่อมีเหตุเจ็บป่วยฉุกเฉิน โดยไม่ต้องรอกรอกข้อมูลครบค่ะ\n\n" + summary
    return summary
