"""Notifier: the words of every message ReachPoint sends a household. Plain Thai first, English second.

Privacy rule: no message ever names another household or repeats another household's details.
These templates are the fallback; api/v2/ai.py can ask Gemini to word a message for one person's situation.
"""

from __future__ import annotations

T = {
    "check": ("ทุกคนในบ้านยังปลอดภัยไหมคะ ตอนนี้น้ำสูงแค่ไหน ตอบ 1 ปลอดภัย · 2 ต้องการช่วยด่วน · 3 น้ำขึ้น",
              "Is everyone at home still safe? How high is the water now? Reply 1 safe · 2 need help now · 3 water rising"),
    "morning": ("สวัสดีตอนเช้าค่ะ ทุกคนในบ้านยังปลอดภัยไหมคะ น้ำเมื่อคืนสูงขึ้นไหม",
                "Good morning. Is everyone still safe? Did the water rise overnight?"),
    "earlyWarning": ("ระดับน้ำคลองอู่ตะเภาสูงขึ้น น้ำอาจถึงบริเวณบ้านคุณภายในราว 6 ชั่วโมง มีผู้สูงอายุหรือคนป่วยในบ้านไหมคะ",
                     "The U-Tapao canal is rising. Water may reach your area within about 6 hours. Is anyone elderly or sick at home?"),
    "rain": ("อีก 3 ชั่วโมงจะมีฝนหนัก น้ำที่บ้านสูงขึ้นไหมคะ ตอบ 1 ปลอดภัย · 2 ต้องการช่วยด่วน · 3 น้ำขึ้น",
             "Heavy rain is expected in the next 3 hours. Is the water rising? Reply 1 safe · 2 need help now · 3 water rising"),
    "river": ("ระดับน้ำแม่น้ำต้นทางสูงขึ้น อาจถึงบริเวณบ้านคุณในราว 6 ชั่วโมง ต้องการออกจากบ้านไหมคะ",
              "The river upstream is rising and may reach you in about 6 hours. Do you need to leave?"),
    "askBack": ("ขอถามเพิ่มนิดหนึ่งค่ะ น้ำอยู่สูงกว่าหรือต่ำกว่าลูกบิดประตูคะ",
                "One more question: is the water above or below your door handle?"),
    "quiet": ("ขอสอบถามค่ะ ถนนหรือซอยใกล้บ้านคุณ ยังมีคนติดอยู่ในบ้านไหมคะ โดยเฉพาะผู้สูงอายุที่อยู่คนเดียว",
              "Do you know if anyone is still inside on the streets near you, especially older people living alone?"),
    "lostCall": ("(สายจากผู้ช่วย AI) สวัสดีค่ะ เราไม่ได้ยินจากคุณสักพัก ทุกคนปลอดภัยไหมคะ",
                 "(AI voice call) Hello, we haven't heard from you for a while. Is everyone safe?"),
    "rainRise": ("ฝนหนักราว {mm} มม. กำลังจะตก แบบจำลองน้ำท่วมคาดว่าน้ำที่บ้านคุณจะสูงขึ้นราว {cm} ซม. ในอีกราว {h} ชั่วโมง {advice}",
                 "Heavy rain (about {mm} mm) is coming. The flood model expects the water at your house to rise about {cm} cm in about {h} hours. {advice}"),
    "pickedUp": ("{team} แจ้งว่ารับคุณออกมาแล้ว ขอให้ปลอดภัยนะคะ หากยังมีคนติดอยู่ ตอบกลับได้เลยค่ะ",
                 "{team} says they picked you up. Stay safe. If anyone is still inside, reply here."),
    "nobodyThere": ("{team} ไปที่บ้านคุณแต่ไม่พบใคร ตอนนี้คุณอยู่ที่ไหน ปลอดภัยไหมคะ ตอบกลับได้เลย",
                    "{team} came to your house but found nobody. Where are you now, and are you safe? Please reply."),
    "neighbourKnown": ("บ้านหลังนั้นอยู่ในระบบแล้วค่ะ และมีคนวางแผนช่วยอยู่ ขอบคุณที่บอกนะคะ",
                       "We already know about that house, and help is planned. Thank you for telling us."),
    "neighbourNew": ("เพิ่มบ้านหลังนั้นให้แล้วค่ะ เราจะพยายามติดต่อพวกเขา",
                     "We've added that house. We'll try to contact them."),
}


def say(key: str, lang: str = "th", **kw) -> str:
    th, en = T[key]
    return (th if lang == "th" else en).format(**kw)


def plan_update(plan: dict, zone: str, lang: str = "th") -> str:
    veh = {"boat": "ทีมเรือ", "jet ski": "ทีมเจ็ทสกี", "truck": "ทีมรถบรรทุก", "high truck": "ทีมรถยกสูง", "pickup": "ทีมรถกระบะ"}
    who_th = veh.get(plan.get("vehicle") or "", "ทีมอาสา")
    eta = plan.get("eta")
    if lang == "th":
        return f"{who_th}แจ้งว่าจะเข้าโซน {zone}" + (f" ประมาณ {eta} ค่ะ" if eta else " ค่ะ") + " หากมีคนเดินไม่ได้ ตอบกลับเพื่อแจ้งเราได้เลย"
    who = {"boat": "A boat team", "jet ski": "A jet ski team"}.get(plan.get("vehicle") or "", "A volunteer team")
    return f"{who} plans to come to zone {zone}" + (f" around {eta}." if eta else ".") + " Reply if anyone can't walk."
