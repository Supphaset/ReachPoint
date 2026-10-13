"""Caller-reported flood facts and the next intake topic."""

from pydantic import ConfigDict, Field

from api.intake.schema import HelpRequestDetails

DISPATCH_NOTICE = "ยังไม่ได้บันทึกคำขอ กรุณายืนยันสรุปก่อนส่งให้ผู้ประสานงานตรวจสอบ ยังไม่มีทีมเข้าช่วยเหลือหรือเวลาถึงพื้นที่ที่ยืนยันแล้ว"


class FloodCase(HelpRequestDetails):
    """Request details plus conversation-only state; unknown values stay explicit."""

    # Older saved conversations may contain removed fields.
    model_config = ConfigDict(extra="ignore")
    immediate_danger: bool | None = None
    unavailable_fields: list[str] = Field(default_factory=list)
    contradictions: list[str] = Field(default_factory=list)


def next_question(case: FloodCase) -> str | None:
    """One question at a time; an urgent caller can submit without completing optional fields."""
    def missing(field: str) -> bool:
        return getattr(case, field) is None and field not in case.unavailable_fields

    if case.immediate_danger and missing("location"):
        return "ตอนนี้อยู่ที่ไหนคะ? หากมีผู้บาดเจ็บฉุกเฉิน โทร 1669 หรือแจ้งเหตุสาธารณภัย โทร 1784 ได้เลยค่ะ"
    if case.contradictions:
        return "ขอให้ช่วยยืนยันข้อมูลที่ขัดกันนี้ค่ะ: " + "; ".join(case.contradictions)
    if case.immediate_danger:
        if missing("emergency_detail"):
            return "เกิดอันตรายอะไรขึ้นตอนนี้ และต้องการความช่วยเหลือเร่งด่วนอย่างไรคะ?"
        if missing("people_details"):
            return "มีใครต้องการความช่วยเหลือบ้าง และประมาณกี่คนคะ?"
        if not case.phone_number:
            return "ขอเบอร์โทรศัพท์ที่ติดต่อได้ เพื่อส่งข้อความสอบถามว่าคุณได้รับความช่วยเหลือแล้วหรือยังค่ะ จำเป็นต้องมีเบอร์โทรก่อนส่งคำขอค่ะ"
        if case.type is None:
            return "ต้องการอาหาร หรือให้อพยพออกจากพื้นที่คะ? กรุณาเลือกประเภทคำขอค่ะ"
        return None
    if case.type is None:
        return "ต้องการอาหาร หรือให้อพยพออกจากพื้นที่คะ? กรุณาเลือกประเภทคำขอค่ะ"
    if not case.phone_number:
        return "ขอเบอร์โทรศัพท์ที่ติดต่อได้ เพื่อส่งข้อความสอบถามว่าคุณได้รับความช่วยเหลือแล้วหรือยังค่ะ จำเป็นต้องมีเบอร์โทรก่อนส่งคำขอค่ะ"
    if missing("people_details"):
        return "มีใครต้องการความช่วยเหลือบ้าง และทั้งหมดประมาณกี่คนคะ?"
    if any(missing(field) for field in ("n_children", "n_elders", "n_pets")):
        return "ในกลุ่มนี้มีเด็ก ผู้สูงอายุ และสัตว์เลี้ยงอย่างละกี่คนหรือกี่ตัวคะ? ถ้าไม่มีบอกศูนย์ หรือถ้าไม่ทราบบอกได้ค่ะ"
    if missing("location"):
        return "ตอนนี้อยู่ที่ไหนคะ? บอกจังหวัด อำเภอ หรือจุดสังเกตใกล้เคียงได้ค่ะ"
    if missing("location_details"):
        return "มีรายละเอียดตำแหน่งเพิ่มเติม เช่น อาคาร ชั้น หรือทางเข้าที่ทีมควรรู้ไหมคะ? ถ้าไม่มีบอกได้ค่ะ"
    if missing("water_level"):
        return "น้ำสูงประมาณไหนแล้วคะ? ถ้าไม่ทราบระดับน้ำ บอกว่าไม่ทราบได้ค่ะ"
    if missing("situation_details"):
        return "ตอนนี้สถานการณ์เป็นอย่างไร น้ำยังเพิ่มอยู่ไหม และทุกคนอยู่ตรงไหนคะ?"
    if missing("emergency_detail"):
        return "มีผู้บาดเจ็บหรืออันตรายเร่งด่วนไหม และต้องการความช่วยเหลืออะไรคะ? ถ้าไม่มีเหตุฉุกเฉินบอกได้ค่ะ"
    if missing("other_details"):
        return "มีข้อมูลอื่นที่อยากแจ้งผู้ประสานงานไหมคะ? ถ้าไม่มีบอกว่าไม่มีได้ค่ะ"
    return None


def render_fields(case: HelpRequestDetails) -> str:
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
    return "\n\n".join(f"{label}: {content}" for label, content in rows)


def render_summary(case: FloodCase) -> str:
    summary = "สรุปคำขอความช่วยเหลือ กรุณาตรวจทานข้อมูลค่ะ\n\n" + render_fields(case)
    summary += "\n\n" + DISPATCH_NOTICE
    summary += "\n\nหากต้องแก้ไขข้อมูลหรือสถานการณ์เปลี่ยนไป แจ้งได้เลยค่ะ หากถูกต้อง กรุณากดยืนยันส่งคำขอค่ะ"
    if case.immediate_danger:
        summary = "ผู้แจ้งระบุอันตรายเฉียบพลัน หากโทรได้ให้ติดต่อ 1784 หรือ 1669 เมื่อมีเหตุเจ็บป่วยฉุกเฉิน โดยไม่ต้องรอกรอกข้อมูลครบค่ะ\n\n" + summary
    return summary
