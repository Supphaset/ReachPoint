"""Thai wording for the lines the server writes (victim and volunteer screens).

Each English line keeps its meaning exactly; free text typed by people (flag reasons, medical notes, quotes) is
never translated here and stays as written.
"""

from __future__ import annotations

TITLE = {"red": "ทำไมจึงเป็นเหตุฉุกเฉิน", "yellow": "ทำไมจึงด่วน", "green": "ทำไมจึงรอได้"}
WITHHELD = "ข้อมูลทางการแพทย์จะแสดงในงาน เฉพาะทีมที่รับงานนี้"
MEDICAL_CATEGORY = "มีความต้องการทางการแพทย์: มีผลต่อวิธีเคลื่อนย้าย"
MEDICAL_URGENT = "ผู้ประเมินที่มีคุณวุฒิระบุว่ามีคนที่นี่ต้องการความช่วยเหลือทางการแพทย์ด่วน"
CANT_WALK = "เดินไม่ได้: ต้องหามหรืออุ้ม"
STRETCHER_KIT = "เปลหาม และคนช่วยหามอย่างน้อย 2 คน"
BOAT_KIT = "ต้องใช้เรือ (น้ำลึก 1.2 ม. ขึ้นไป)"
WADE_KIT = "ผู้แจ้งบอกว่าน้ำต่ำกว่า 1.2 ม. ตรวจความลึกเมื่อไปถึง"
WATER_UNKNOWN = "ความลึกของน้ำที่นี่: ไม่ทราบ (ยังไม่มีรายงานที่ตรวจสอบแล้ว)"
BANDS = {"knee": "น้ำถึงเข่า", "waist": "น้ำถึงเอว", "chest": "น้ำถึงอก", "over_head": "น้ำท่วมหัว",
         "second_floor": "น้ำถึงชั้น 2"}
DESTINATIONS = {"D1": "D1 ศูนย์พักพิง (ที่สูง)", "H1": "H1 โรงพยาบาล (สมมติ)"}
DESTINATION_REASONS = {
    "Shelter": "ศูนย์พักพิง",
    "One person needs urgent medical care; the medical team meets you at H1": "มีผู้ต้องการการรักษาด่วน 1 คน ทีมแพทย์จะรอรับที่ H1",
    "Needs oxygen and power": "ต้องใช้ออกซิเจนและไฟฟ้า",
}


def party(p: dict) -> str:
    names = {"adults": "ผู้ใหญ่", "children": "เด็ก", "infants": "ทารก", "stretcher": "ผู้ป่วยที่ต้องใช้เปล"}
    return " ".join(f"{names[k]} {p[k]} คน" for k in names if p.get(k))


def family(label: str) -> str:
    return label.replace("Family", "ครอบครัว", 1) if label.startswith("Family") else label


def team(team_id: str) -> str:
    return f"ทีม {team_id}"
