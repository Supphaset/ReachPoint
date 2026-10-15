"""The v2 demo scenario: Hat Yai city, 21–28 Nov 2025, with real water data and synthetic people.

    python data/scripts/build_v2_scenario.py

Real: river gauge X.44 (RID), rain (IMERG), zones and population estimate, Open Buildings outlines, FABDEM ground.
Synthetic: households on real buildings, the messages they and others send, volunteer plans, and bulletins
reconstructed from the real gauge readings. Fixed seed, so every build is identical.

The true water surface per zone follows the real gauge: the canal tops its bank (7.4 m) on 23 Nov and peaks at
9.97 m on 25 Nov 10:00. Each zone floods to its own depth (from the modelled flooded share) with its own delay.
The truth is stored for the evaluation and is never read by the pipeline.
"""

from __future__ import annotations

import json
import math
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from api.v2 import geo as G  # noqa: E402
from api.v2.depth_words import words_for  # noqa: E402

PKG = ROOT / "data" / "hy-2025-11"
TZ = timezone(timedelta(hours=7))
START = datetime(2025, 11, 21, 6, tzinfo=TZ)
HOURS = 7 * 24
BANK_M, PEAK_M = 7.0, 9.97
SEED = 20251125
N_HOUSEHOLDS = 260


def iso(h: float) -> str:
    return (START + timedelta(hours=h)).isoformat(timespec="minutes")


def gauge_series():
    g = json.loads((PKG / "gauge-x44.json").read_text())
    pts = [((datetime.fromisoformat(r["at"]) - START).total_seconds() / 3600, r["levelM"]) for r in g["readings"]]
    return sorted(pts)


def interp(pts, h):
    if h <= pts[0][0]:
        return pts[0][1]
    for (h1, v1), (h2, v2) in zip(pts, pts[1:]):
        if h1 <= h <= h2:
            return v1 + (v2 - v1) * (h - h1) / (h2 - h1)
    return pts[-1][1]


def main() -> None:
    rnd = random.Random(SEED)
    geo = G.load()
    gauge = gauge_series()
    zones = {z["properties"]["id"]: z["properties"] for z in geo.zones}
    by_zone: dict[str, list[G.Building]] = {}
    for b in geo.buildings.values():
        if b.ground_m is not None:
            by_zone.setdefault(b.zone_id, []).append(b)

    # --- truth: a water surface per zone per hour, shaped by the gauge
    zt = {}
    for zid, bs in by_zone.items():
        grounds = sorted(b.ground_m for b in bs)
        p50 = grounds[len(grounds) // 2]
        est = zones[zid]["estimate"]
        mid = lambda r: (r[0] + r[1]) / 2 if r else 0
        share = min(1.0, mid(est.get("modelledFlooded")) / max(1, mid(est.get("everyone"))))
        zt[zid] = {"groundP50": round(p50, 2), "peakDepthM": round(0.35 + 2.0 * share, 2), "lagH": round(rnd.uniform(0, 8), 1)}

    def wse(zid, h):
        z = zt[zid]
        frac = (interp(gauge, h - z["lagH"]) - BANK_M) / (PEAK_M - BANK_M)
        if frac <= 0:
            return None
        return round(z["groundP50"] + z["peakDepthM"] * min(1.2, frac) - 0.6 * (1 - min(1, frac)), 2)

    def depth(b, h):
        w = wse(b.zone_id, h)
        return 0.0 if w is None else max(0.0, w - b.ground_m)

    # --- truth households on real buildings, weighted toward deeper zones
    weights = []
    cand = []
    for zid, bs in by_zone.items():
        peak = zt[zid]["peakDepthM"]
        for b in bs:
            if b.area_m2 < 40:
                continue
            cand.append(b)
            weights.append(peak * min(b.area_m2, 300))
    picked = set()
    households = []

    def new_household(b, silent=False):
        n = rnd.choices([1, 2, 3, 4, 5, 6, 7], [10, 18, 22, 22, 14, 9, 5])[0]
        elderly = min(n, rnd.choices([0, 1, 2], [55, 35, 10])[0])
        children = 0 if n == 1 else min(n - max(1, elderly), rnd.choices([0, 1, 2, 3], [50, 25, 18, 7])[0])
        hh = {"id": f"H{len(households) + 1:03d}", "buildingId": b.id, "zoneId": b.zone_id, "people": n,
              "elderly": elderly, "children": children, "cannotWalk": 1 if elderly and rnd.random() < 0.3 else 0,
              "phoneKey": f"P{rnd.randrange(10**6):06d}" if rnd.random() < 0.75 else None,
              "lang": "en" if rnd.random() < 0.12 else "th", "silent": silent,
              "lostContactAfterH": rnd.uniform(60, 120) if rnd.random() < 0.08 else None,
              "houseNo": f"{rnd.randint(1, 199)}/{rnd.randint(1, 40)}"}
        households.append(hh)
        picked.add(b.id)
        return hh

    while len(households) < N_HOUSEHOLDS:
        b = rnd.choices(cand, weights)[0]
        if b.id not in picked:
            new_household(b)
    hh_by_building = {h["buildingId"]: h for h in households}

    def street_of(b, th=True):
        for n in [b] + geo.near(b.x, b.y, 250):
            fn = geo.facing(n)
            if fn and (fn.street_th if th else fn.street):
                return fn.street_th if th else fn.street
        return None if th else street_of(b, True)

    landmarks = {}
    for f in json.loads((PKG / "landmarks.geojson").read_text())["features"]:
        landmarks.setdefault(f["properties"]["zoneId"], []).append(f["properties"]["type"])
    LM_TH = {"Temple": "วัด", "Market": "ตลาด", "School": "โรงเรียน", "Shrine": "ศาลเจ้า", "Mosque": "มัสยิด",
             "Health centre": "อนามัย", "Community building": "ศาลาชุมชน", "Shelter (high ground)": "ศูนย์พักพิง"}

    msgs = []

    def add(h, channel, kind, text, b, precision, about=None, reporter=None, **extra):
        jitter = {"address": 0, "landmark": 70, "area": 250}[precision]
        x, y = b.x + rnd.gauss(0, jitter), b.y + rnd.gauss(0, jitter)
        lon, lat = G.to_ll(x, y)
        msgs.append({"id": f"M{len(msgs) + 1:04d}", "atH": round(h, 2), "at": iso(h), "channel": channel, "kind": kind,
                     "text": text, "pin": {"lon": round(lon, 6), "lat": round(lat, 6), "precision": precision},
                     "truth": {"about": about, "reporter": reporter, "buildingId": b.id, **extra}})

    def people_th(hh):
        s = f"อยู่กัน {hh['people']} คน" if hh["people"] > 1 else "อยู่คนเดียว"
        if hh["elderly"]:
            s += f" มีผู้สูงอายุ {hh['elderly']} คน"
        if hh["children"]:
            s += f" เด็ก {hh['children']} คน"
        if hh["cannotWalk"]:
            s += " มีคนเดินไม่ได้"
        return s

    def people_en(hh):
        s = f"{hh['people']} of us" if hh["people"] > 1 else "I'm alone"
        if hh["elderly"]:
            s += f", {hh['elderly']} elderly"
        if hh["children"]:
            s += f", {hh['children']} kids"
        if hh["cannotWalk"]:
            s += ", one can't walk"
        return s

    def where_th(hh, b):
        st = street_of(b)
        lm = rnd.choice(landmarks.get(b.zone_id, ["Temple"]))
        return (f"บ้านเลขที่ {hh['houseNo']} {st}" if st else f"บ้านเลขที่ {hh['houseNo']}") + f" ใกล้{LM_TH.get(lm, 'วัด')}"

    def where_en(hh, b):
        st = street_of(b, th=False)
        return f"house {hh['houseNo']}" + (f", {st}" if st else "")

    def noisy(d, planted=False):
        if planted:  # an exaggerated or panicked report: well beyond what the water is
            return d + max(0.8, d) + rnd.uniform(0, 0.4)
        return max(0.05, d + rnd.gauss(0, 0.15))

    # --- each household's own story
    for hh in list(households):
        b = geo.buildings[hh["buildingId"]]
        th = rnd.uniform(0.2, 0.7)
        first = next((h for h in range(HOURS) if depth(b, h) >= th), None)
        if first is None or hh["silent"]:
            continue
        t0 = first + rnd.expovariate(1 / 3)
        if t0 >= HOURS - 6:
            continue
        reports_self = rnd.random() < 0.72
        planted = rnd.random() < 0.05
        d = noisy(depth(b, t0), planted)
        lang = hh["lang"]
        if reports_self:
            ch = rnd.choices(["chat", "voice", "post"], [55, 25, 20])[0]
            if lang == "th":
                help_ = rnd.choice(["ช่วยด้วยค่ะ ", "ช่วยด้วยครับ ", "ขอความช่วยเหลือค่ะ ", "", "ตอนนี้"])
                text = f"{help_}{words_for(d, 'th')}แล้ว {people_th(hh)} {where_th(hh, b)}"
            else:
                text = f"Please help, {words_for(d, 'en')}. {people_en(hh).capitalize()}. We're at {where_en(hh, b)}."
            prec = "address" if ch != "post" else "landmark"
            nb_side = None
            if ch != "post" and rnd.random() < 0.35:
                sides = geo.neighbours(b)
                opts = [(s, ids[0]) for s, ids in sides.items() if ids and s in ("left", "right", "across")]
                if opts:
                    side, nid = rnd.choice(opts)
                    nb = geo.buildings[nid]
                    other = hh_by_building.get(nid) or new_household(nb, silent=True)
                    hh_by_building[nid] = other
                    who_th = ("ยายอยู่คนเดียว" if other["elderly"] and other["people"] == 1 else
                              f"ครอบครัว {other['people']} คน" + (f" มีเด็ก {other['children']} คน" if other["children"] else ""))
                    side_th = {"left": "บ้านทางซ้ายมือ", "right": "บ้านทางขวามือ", "across": "บ้านฝั่งตรงข้าม"}[side]
                    side_en = {"left": "the house on our left", "right": "the house on our right", "across": "the house across the street"}[side]
                    who_en = ("an old lady lives alone" if other["elderly"] and other["people"] == 1 else
                              f"a family of {other['people']}" + (f" with {other['children']} kids" if other["children"] else ""))
                    text += f" {side_th}มี{who_th} ยังไม่ได้ออกมา" if lang == "th" else f" Also {side_en}: {who_en}, still inside."
                    nb_side = {"side": side, "neighbourBuildingId": nid, "neighbourHousehold": other["id"]}
            add(t0, ch, "self", text, b, prec, about=hh["id"], reporter=hh["id"], planted=planted,
                trueDepthM=round(depth(b, t0), 2), neighbour=nb_side)
        # relatives and friends post about them too (duplicates, sometimes forwarded later)
        if rnd.random() < (0.35 if reports_self else 0.6):
            tp = t0 + rnd.uniform(0.5, 18)
            if tp < HOURS:
                dd = noisy(depth(b, tp))
                rel = rnd.choice(["ญาติผม", "แม่ของเพื่อน", "ยายผม", "ครอบครัวพี่สาว", "เพื่อนบ้าน"])
                text = f"ใครอยู่แถว{street_of(b) or 'นั้น'} ช่วยด้วยครับ {rel} {people_th(hh)} {words_for(dd, 'th')} ติดต่อไม่ค่อยได้"
                add(tp, "post", "relative", text, b, "landmark", about=hh["id"], trueDepthM=round(depth(b, tp), 2))
                if rnd.random() < 0.25 and tp + 30 < HOURS:
                    add(tp + rnd.uniform(24, 40), "post", "forward", "ส่งต่อ: " + text, b, "landmark", about=hh["id"],
                        trueDepthM=round(depth(b, tp), 2), staleFromH=round(tp, 2))
        # replies to the daily and alert check-ins, while the water is there
        evac_at = None
        for hc in [h for h in range(HOURS) if (START + timedelta(hours=h)).hour in (7, 19)]:
            if hc <= t0 + 1 or not reports_self:
                continue
            if evac_at is None and depth(b, hc) > 1.4 and rnd.random() < 0.35:
                evac_at = hc
                add(hc + rnd.uniform(0.2, 1.5), "safetyReply", "reply",
                    "อพยพออกมาแล้วค่ะ ทีมเรือมารับ ทุกคนปลอดภัย" if lang == "th" else "We've been evacuated by a boat team. Everyone is safe.",
                    b, "address", about=hh["id"], reporter=hh["id"], trueDepthM=round(depth(b, hc), 2), evacuated=True)
                break
            if hh["lostContactAfterH"] and hc > hh["lostContactAfterH"]:
                break
            if depth(b, hc) < 0.05 and depth(b, hc - 12) < 0.05:
                add(hc + rnd.uniform(0.05, 1.5), "safetyReply", "reply",
                    "น้ำลดแล้วค่ะ ทุกคนปลอดภัย" if lang == "th" else "The water has gone down. We're all safe.", b, "address",
                    about=hh["id"], reporter=hh["id"], trueDepthM=0.0)
                break
            if rnd.random() < 0.94:
                dd = noisy(depth(b, hc))
                rising = (wse(b.zone_id, hc) or 0) > (wse(b.zone_id, hc - 6) or 0) + 0.05
                text = (("ยังปลอดภัยค่ะ " if dd < 1.2 else "ต้องการความช่วยเหลือด่วน ") + words_for(dd, "th") +
                        (" น้ำยังขึ้นอยู่" if rising else " น้ำเริ่มทรงตัว")) if lang == "th" else \
                       (("Still OK. " if dd < 1.2 else "We need help now. ") + words_for(dd, "en").capitalize() +
                        (", still rising." if rising else ", holding steady."))
                add(hc + rnd.uniform(0.05, 1.5), "safetyReply", "reply", text, b, "address", about=hh["id"],
                    reporter=hh["id"], trueDepthM=round(depth(b, hc), 2))

    # --- bulletins reconstructed from the real gauge, every 6 hours
    for h in range(0, HOURS, 6):
        lv, prev = interp(gauge, h), interp(gauge, h - 6)
        rate = (lv - prev) / 6
        trend = "เพิ่มขึ้น" if rate > 0.02 else ("ลดลง" if rate < -0.02 else "ทรงตัว")
        state = "ล้นตลิ่ง" if lv > 7.4 else ("ใกล้ระดับเตือนภัย" if lv > 6.5 else "ต่ำกว่าตลิ่ง")
        msgs.append({"id": f"M{len(msgs) + 1:04d}", "atH": h, "at": iso(h), "channel": "bulletin", "kind": "bulletin",
                     "text": f"ประกาศกรมชลประทาน (จำลองจากข้อมูลจริง): สถานี X.44 คลองอู่ตะเภา บ้านหาดใหญ่ใน ระดับน้ำ {lv:.2f} ม.รทก. "
                             f"(ตลิ่ง 7.40 ม.) สถานะ{state} แนวโน้ม{trend} {abs(rate) * 100:.0f} ซม./ชม.",
                     "pin": None, "truth": {"gaugeM": round(lv, 2), "rateMh": round(rate, 3), "reconstructed": True}})

    # --- volunteer plans (one line each)
    deep = sorted(zt, key=lambda z: -zt[z]["peakDepthM"])
    teams = [("ทีมเรือกู้ภัยหาดใหญ่ 1", "เรือ", 8, "อพยพ"), ("มูลนิธิช่วยเหลือ ทีม 2", "เรือ", 6, "อพยพผู้ป่วย"),
             ("อาสาบ้านพรุ", "รถยกสูง", 12, "อพยพ"), ("ครัวอาสา", "รถกระบะ", 0, "อาหารและน้ำ"),
             ("ทีมแพทย์อาสา", "เรือ", 4, "การแพทย์"), ("เจ็ทสกีอาสา", "เจ็ทสกี", 2, "อพยพ"),
             ("ทีมเรือกู้ภัยหาดใหญ่ 3", "เรือ", 8, "อพยพ"), ("อาสาโรงเรียน", "รถบรรทุก", 20, "อาหารและน้ำ")]
    plans = []
    for i, (team, veh, seats, offer) in enumerate(teams):
        h = 50 + i * 7 + rnd.uniform(0, 4)
        z1, z2 = deep[i % 5], deep[(i + 3) % len(deep)]
        eta = START + timedelta(hours=h + rnd.uniform(1, 3))
        seat = f" {seats} ที่นั่ง" if seats else ""
        plans.append({"id": f"PL{i + 1}", "atH": round(h, 2), "at": iso(h),
                      "text": f"{team} {veh}{seat} จะเข้าโซน {z1} ประมาณ {eta:%H:%M} แล้วต่อ {z2} ({offer})",
                      "truth": {"team": team, "vehicle": veh, "seats": seats, "zones": [z1, z2], "eta": eta.isoformat(timespec='minutes'), "offers": offer}})

    msgs.sort(key=lambda m: m["atH"])
    for i, m in enumerate(msgs):
        m["id"] = f"M{i + 1:04d}"
    truth_wse = {zid: [[h, wse(zid, h)] for h in range(0, HOURS + 1, 3)] for zid in zt}
    out = {"package": "hy-2025-11", "start": START.isoformat(), "hours": HOURS,
           "label": "Real gauge, rain, satellite, terrain and buildings; synthetic people, messages and plans.",
           "zones": zt, "messages": msgs, "plans": plans,
           "truth": {"households": households, "wseByZone": truth_wse}}
    (PKG / "v2-scenario.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")))
    kinds = {}
    for m in msgs:
        kinds[m["kind"]] = kinds.get(m["kind"], 0) + 1
    print(len(households), "households;", len(msgs), "messages", kinds, ";", len(plans), "plans")


if __name__ == "__main__":
    main()
