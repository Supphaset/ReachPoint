"""English place labels for the bundled Hat Yai data.

Prefer OSM name:en, then the intake alias table reversed, then reviewed RTGS
words. This small romaniser covers this package, not arbitrary Thai prose.
Never use it to translate source quotes or change household matching.
"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

ROMAN_STREETS = {
    "phetkasem": "เพชรเกษม",
    "petchkasem": "เพชรเกษม",
    "phet kasem": "เพชรเกษม",
    "kanjanavanich": "กาญจนวณิชย์",
    "kanchanawanit": "กาญจนวณิชย์",
    "sriphuwanart": "ศรีภูวนารถ",
    "si phuwanat": "ศรีภูวนารถ",
    "ratyindee": "ราษฎร์ยินดี",
    "rat yindi": "ราษฎร์ยินดี",
    "lopburi ramesuan": "ลพบุรีราเมศวร์",
    "lop buri ramet": "ลพบุรีราเมศวร์",
    "sajjakul": "สัจจกุล",
    "thamnoonvithi": "ธรรมนูญวิถี",
    "thamnun withi": "ธรรมนูญวิถี",
    "supasarnrangsan": "ศุภสารรังสรรค์",
    "suphasan rangsan": "ศุภสารรังสรรค์",
    "nuankaew uthit": "นวลแก้วอุทิศ",
    "niphat songkhro": "นิพัทธ์สงเคราะห์",
    "niphat uthit": "นิพัทธ์อุทิศ",
    "nipat uthit": "นิพัทธ์อุทิศ",
    "samchai": "สามชัย",
    "saeng si": "แสงศรี",
    "saengsri": "แสงศรี",
    "pracha yindee": "ประชายินดี",
    "rat uthit": "ราษฎร์อุทิศ",
    "punnakan": "ปุณณกัณฑ์",
    "phadung phakdi": "ผดุงภักดี",
    "thung sao": "ทุ่งเสา",
    "chi uthit": "ชีอุทิศ",
    "rattakarn": "รัถการ",
    "rattakan": "รัถการ",
    "nipan songkhro": "นิพันธ์สงเคราะห์",
    "hoi muk": "หอยมุกต์",
    "chuti anusorn": "จุติอนุสรณ์",
    "suan siri": "สวนศิริ",
    "khlong hae": "คลองแห",
    "prachathipat": "ประชาธิปัตย์",
    "kim pradit": "กิมประดิษฐ์",
    "chan niwet": "จันทร์นิเวศน์",
    "wit withi": "วิทย์วิถี",
    "yen sira": "เย็นศิระ",
    "khlong rian": "คลองเรียน",
    "sakhon mongkhon": "สาครมงคล",
    "lamai songkhro": "ละม้ายสงเคราะห์",
    "niyom rat": "นิยมรัฐ",
    "ruam phatthana": "ร่วมพัฒนา",
    "ban cha": "บ้านจ่า",
    "chokesaman": "โชคสมาน",
    "nipatpukdee": "นิพัทธ์ภักดี"
}

RTGS_WORDS = {
    "กระจ่างอุทิศ": "Krachang Uthit",
    "กาญจนวนิช": "Kanchanawanit",
    "กาญจนวนิช-ทุ่งโดน": "Kanchanawanit-Thung Don",
    "กุลวัฒน์อุทิศ": "Kunlawat Uthit",
    "ขจรอุทิศ": "Khachon Uthit",
    "คลองวาด": "Khlong Wat",
    "คลองเตย": "Khlong Toei",
    "คลองเตยพัฒนา": "Khlong Toei Phatthana",
    "คลองแห-คูเต่า": "Khlong Hae-Khu Tao",
    "ควนสันติ": "Khuan Santi",
    "คึกฤทธิ์": "Khuek Rit",
    "จันทร์วิโรจน์": "Chan Wirot",
    "จันทร์สุวรรณวงษ์": "Chan Suwan Wong",
    "จันท์ราชอนุสรณ์": "Chan Rat Anuson",
    "จิระนคร": "Chira Nakhon",
    "จุติอุทิศ": "Chuti Uthit",
    "ฉัยยากุล": "Chaiyakun",
    "ฉัยยากุลอุทิศ": "Chaiyakun Uthit",
    "ชนตารา": "Chon Tara",
    "ชลประธาน": "Chonlaprathan",
    "ชีวานุสรณ์": "Chiwa Nuson",
    "ชุมอุทิศ": "Chum Uthit",
    "ดำเนิน": "Damnoen",
    "ดีศรีศักดิ์": "Di Si Sak",
    "ตรอกจิระพัทธ์": "Trok Chira Phat",
    "ตรอกสุคนธหงส์": "Trok Sukhontha Hong",
    "ตันรัตนากร": "Tan Rattanakon",
    "ถาวระ": "Thawara",
    "ทวีรัตน์อุทิศ": "Thawi Rat Uthit",
    "ทางคู่ขนาน": "Thang Khu Khanan",
    "ทินกร": "Thinnakon",
    "ทิพรัตน์": "Thippharat",
    "ทุ่งทอง": "Thung Thong",
    "ทุ่งรี": "Thung Ri",
    "โคกวัด": "Khok Wat",
    "นวลศรี": "Nuan Si",
    "น้ำทิพย์": "Nam Thip",
    "บุญรองอุทิศ": "Bun Rong Uthit",
    "บุญราช": "Bun Rat",
    "บ้านทุ่งรี": "Ban Thung Ri",
    "บ้านโคกเมา": "Ban Khok Mao",
    "ประชาชื่นใจ": "Pracha Chuen Chai",
    "ประชารมย์": "Pracha Rom",
    "ประสานมิตร": "Prasan Mit",
    "ปราสานใจ": "Prasan Chai",
    "ปรีดารมย์": "Prida Rom",
    "ปานอนุสรณ์": "Pan Anuson",
    "พรหมสุวรรณ": "Phrom Suwan",
    "พรหมอุทิศ": "Phrom Uthit",
    "พลพิชัย": "Phon Phichai",
    "พัฒโน": "Phatthano",
    "พัฒโนอุทิศ": "Phatthano Uthit",
    "พินอุทิศ": "Phin Uthit",
    "พูลสุวรรณ": "Phun Suwan",
    "ภราดร": "Pharadon",
    "ภาสว่าง": "Pha Sawang",
    "มงคลสุข": "Mongkhon Suk",
    "มนตรี": "Montri",
    "มุสลิม": "Muslim",
    "ยกอุทิศ": "Yok Uthit",
    "ยินดี": "Yindi",
    "รวมมิตร": "Ruam Mit",
    "รัตนอุทิศ": "Rattan Uthit",
    "รัศมี": "Ratsami",
    "ศรีเฉลิม": "Si Chaloem",
    "ราฎร์ยินดี": "Rat Yindi",
    "ราษฎร์ดำริ": "Rat Damri",
    "ราษฎร์บูรณะ": "Rat Burana",
    "ราษฏร์ยินดี": "Rat Yindi",
    "ราษฏร์อุทิศ": "Rat Uthit",
    "ริมอ่าง": "Rim Ang",
    "ร่วมอุทิศ": "Ruam Uthit",
    "ลีพัฒนา": "Li Phatthana",
    "ลุงคิ้น": "Lung Khin",
    "วงศ์วานิช": "Wong Wanit",
    "วังหงส์": "Wang Hong",
    "ศรนรินทร์": "Son Narin",
    "ศรีตรัง": "Si Trang",
    "ศรีนิล": "Si Nin",
    "ศรีผดุงวิถี": "Si Phadung Withi",
    "ศิริสมบัติ": "Siri Sombat",
    "สงขลานครินทร์": "Songkhla Nakharin",
    "สยามซิตี้เซ็นเตอร์": "Siam City Center",
    "สองพี่น้อง": "Song Phi Nong",
    "สะพานดำ": "Saphan Dam",
    "สันติราษฎร์": "Santi Rat",
    "สามมิตร": "Sam Mit",
    "สุทธิสมิทธิ์": "Sutthi Samit",
    "สุธา": "Sutha",
    "สุธาทิพย์": "Sutha Thip",
    "สุนทรวิถี": "Sunthon Withi",
    "สุภาพ": "Suphap",
    "สุมาลี": "Sumali",
    "สุวรรณหงษ์": "Suwan Hong",
    "สุะาทิพย์": "Sutha Thip",
    "เฟส": "Phase",
    "สเน่หานุสรณ์": "Saneha Nuson",
    "หงส้ทิพย์": "Hong Thip",
    "หนองแฟบ": "Nong Faep",
    "หน้าพระรูป": "Na Phra Rup",
    "หน้าสถานี": "Na Sathani",
    "หอมนวล": "Hom Nuan",
    "หาดใหญ่นคร": "Hat Yai Nakhon",
    "อรรถกระวี": "Atthakrawi",
    "อรรถกระวีสุนทร": "Atthakrawi Sunthon",
    "อัมพวัน": "Amphawan",
    "อาคาร": "Akhan",
    "อำนวยวิทย์": "Amnuai Wit",
    "อุโมงค์กัลยาณมิตร": "Umong Kanlayanamit",
    "เฉลียวอุทิศ": "Chaliao Uthit",
    "เชื่อมรัฐ": "Chueam Rat",
    "เชื่อมรัฐอุทิศ": "Chueam Rat Uthit",
    "เตชะโต": "Techa To",
    "เทพสงเคราะห์": "Thep Songkhro",
    "เทศาพัฒนา": "Thesa Phatthana",
    "เทียนจ่ออุทิศ": "Thian Cho Uthit",
    "เพชรสยาม": "Phet Siam",
    "เพลินจิต": "Phloen Chit",
    "เลียบคลอง": "Liap Khlong",
    "เวชวิถี": "Wet Withi",
    "เสน่หานุสรณ์": "Saneha Nuson",
    "เเสงศรี": "Saeng Si",
    "แก้วพรหมทอง": "Kaeo Phrom Thong",
    "แป้นอนุสรณ์": "Paen Anuson",
    "แสงจันทร์": "Saeng Chan",
    "แสงอาทิตย์": "Saeng Athit",
    "โชคสมานคุณ": "Chok Saman Khun",
    "โชติวิทยะกุล": "Choti Witthayakun",
    "โรงอิฐ": "Rong It",
    "โสภณพิทยาคุณานุสรณ์": "Sophon Phitthayakhun Anuson",
    "ไชยมุณี": "Chai Muni",
    "ไทยอาคาร": "Thai Akhan",
    "ไพศาลอุทิศ": "Phaisan Uthit",
    "โรงเรียน มอ.วิทยานุสรณ์": "Mo Witthayanuson School",
    "สวนธรรมสากล": "Suan Tham Sakon",
    "วัดคลองแห": "Wat Khlong Hae",
    "มหาวิทยาลัยสงขลานครินทร์": "Prince of Songkla University",
    "วัดคลองเรียน": "Wat Khlong Rian"
}

# Use the last (usually spaced RTGS) alias for display, retaining all input aliases.
REVERSED_STREETS = {thai: roman.title() for roman, thai in ROMAN_STREETS.items()}
REVERSED_STREETS.update({"เพชรเกษม": "Phetkasem", "รัถการ": "Rattakan", "ละม้ายสงเคราะห์": "Lamai Songkhro"})


_WORDS = {**REVERSED_STREETS, **RTGS_WORDS, "ถนน": "Thanon", "ซอย": "Soi", "เขต": "District", "ร.": "Ro"}
_WORD_PATTERN = re.compile("|".join(re.escape(k) for k in sorted(_WORDS, key=len, reverse=True)))


@lru_cache(maxsize=4096)
def romanise(name: str) -> str:
    out = _WORD_PATTERN.sub(lambda m: " " + _WORDS[m.group()] + " ", name)
    return re.sub(r"\s+", " ", out).strip().translate(str.maketrans("๐๑๒๓๔๕๖๗๘๙", "0123456789"))


@lru_cache(maxsize=1)
def osm_english() -> dict[str, str]:
    path = Path(__file__).resolve().parents[2] / "data/hy-2025-11/v2-streets.geojson"
    out = {}
    for feature in json.loads(path.read_text())["features"]:
        p = feature["properties"]
        en = p.get("name:en") or p.get("nameEn")
        if en:
            for name in (p.get("name"), p.get("nameTh")):
                if name:
                    out[name] = en
    return out


def english_name(name: str | None, name_en: str | None = None) -> str | None:
    if not name:
        return name
    return name_en or osm_english().get(name) or romanise(name)


def bilingual(value):
    """Copy an API view, adding display fields without altering source evidence."""
    if isinstance(value, list):
        return [bilingual(v) for v in value]
    if not isinstance(value, dict):
        return value
    out = {k: bilingual(v) for k, v in value.items()}
    for key in ("name", "label", "sectorName", "district", "address"):
        if isinstance(out.get(key), str):
            out[key + "En"] = english_name(out[key], out.get(key + "En"))
    if "label" in out and "geometry" not in out and ("sector" in out or "zoneId" in out):
        out.setdefault("name", out["label"])
        out.setdefault("nameEn", out.get("labelEn"))
    return out


def bilingual_view(fn):
    from functools import wraps

    @wraps(fn)
    def view(*args, **kwargs):
        return bilingual(fn(*args, **kwargs))
    return view
