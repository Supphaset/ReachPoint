"""Caller-reported flood facts and the next intake topic."""

from pydantic import BaseModel, Field

DISPATCH_NOTICE = "ยังไม่ได้บันทึกคำขอ กรุณายืนยันสรุปก่อนส่งให้ผู้ประสานงานตรวจสอบ ยังไม่มีทีมเข้าช่วยเหลือหรือเวลาถึงพื้นที่ที่ยืนยันแล้ว"


class FloodCase(BaseModel):
    """Facts reported by the user, with unknown values kept explicit."""

    reporter_name: str | None = None
    people_details: str | None = None
    n_children: int | None = Field(default=None, ge=0)
    n_elders: int | None = Field(default=None, ge=0)
    n_pets: int | None = Field(default=None, ge=0)
    location: str | None = None
    coordinates: str | None = None
    location_details: str | None = None
    water_level: str | None = None
    situation_details: str | None = None
    emergency_detail: str | None = None
    other_details: str | None = None
    # Used for the emergency notice; the structured help_requests table has the 14 reviewed fields only.
    immediate_danger: bool | None = None
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
        return "ถามชื่อผู้แจ้ง พร้อมบอกว่าไม่สะดวกแจ้งก็ข้ามได้"
    if missing("people_details"):
        return "ถามรายละเอียดคนที่ต้องการความช่วยเหลือ รวมจำนวนคน ถ้ามีเด็ก ผู้สูงอายุ หรือสัตว์เลี้ยงให้แจ้งด้วย"
    if any(missing(field) for field in ("n_children", "n_elders", "n_pets")):
        return "ถามจำนวนเด็ก ผู้สูงอายุ และสัตว์เลี้ยงที่ยังไม่ทราบ บอกว่า 0 หรือไม่ทราบได้"
    if missing("location"):
        return "ถามที่อยู่ จังหวัด จุดสังเกต และรายละเอียดตำแหน่งเพิ่มเติม พิกัดเป็นทางเลือก"
    fields = {
        "water_level": "ระดับน้ำ",
        "situation_details": "สถานการณ์ตอนนี้ น้ำยังเพิ่มหรือไม่ ทุกคนอยู่ตรงไหน",
        "emergency_detail": "มีอันตรายเฉียบพลันหรือผู้บาดเจ็บหรือไม่ ต้องการความช่วยเหลืออะไรเร่งด่วน",
        "other_details": "ข้อมูลอื่นที่ต้องการแจ้ง (ถ้าไม่มีให้บอกว่าไม่มี)",
    }
    needed = [label for field, label in fields.items() if missing(field)]
    if needed:
        return "ถามสถานการณ์เฉพาะข้อมูลที่ยังขาด: " + ", ".join(needed)
    return "สรุปคำขอจากข้อมูลทั้งหมดให้ตรวจแก้ ระบุข้อมูลที่ยังไม่ทราบ และขอการยืนยันก่อนบันทึกให้ผู้ประสานงานตรวจสอบ"


def render_summary(case: FloodCase) -> str:
    """Render reported fields directly, without model-generated count breakdowns."""
    def value(field: str) -> str:
        content = getattr(case, field)
        return "ยังไม่ทราบ / ยังไม่ได้แจ้ง" if content is None else str(content)

    rows = [
        ("ผู้แจ้ง", value("reporter_name")),
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
    summary = "สรุปคำขอความช่วยเหลือ กรุณาตรวจทานข้อมูลค่ะ\n\n"
    summary += "\n\n".join(f"{label}: {content}" for label, content in rows)
    summary += "\n\n" + DISPATCH_NOTICE
    summary += "\n\nหากต้องแก้ไขข้อมูลหรือสถานการณ์เปลี่ยนไป แจ้งได้เลยค่ะ หากถูกต้อง กรุณากดยืนยันส่งคำขอค่ะ"
    if case.immediate_danger:
        summary = "ผู้แจ้งระบุอันตรายเฉียบพลัน หากโทรได้ให้ติดต่อ 1784 หรือ 1669 เมื่อมีเหตุเจ็บป่วยฉุกเฉิน โดยไม่ต้องรอกรอกข้อมูลครบค่ะ\n\n" + summary
    return summary
