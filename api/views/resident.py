"""The family's own status page (D6, 8A): `GET /api/status/{token}`. Only this request; no other family, no exact
points, no medical notes. Honest wording: a team's time is an estimate, never a promise; nothing promises a rescue
before a team has taken the family.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from api.views import thai
from api.views.store import Store
from api.views.team import ACTIVE, allocations_for, group_owner

BANGKOK = timezone(timedelta(hours=7))


def _clock(iso: str) -> str:
    return datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(BANGKOK).strftime("%H:%M")


def _family_line(store: Store, need: dict, gid: str) -> dict:
    candidates = [a for a in allocations_for(store, need["listingId"]) if gid in a["groupIds"]]
    a = next((a for a in reversed(candidates) if a["state"] in ACTIVE or
              a.get("outcome") in ("done", "already_left", "not_found")), candidates[-1] if candidates else None)
    owner = group_owner(store, need, gid)
    if a is None and not owner:
        return {"state": "waiting", "text": "On the list. No team has taken it yet. Call again if it becomes an emergency.",
                "th": "อยู่ในรายการแล้ว ยังไม่มีทีมรับงาน หากกลายเป็นเหตุฉุกเฉินให้โทรอีกครั้ง"}
    if a is None:
        return {"state": "taken", "text": f"Team {owner} is handling your request.",
                "th": f"{thai.team(owner)} กำลังดูแลคำขอของคุณ"}
    t = a["teamId"]
    if a["state"] == "held":
        w = a.get("window")
        earlier = f"earlier {_clock(w['start'])}–{_clock(w['end'])} estimate withdrawn" if w else "arrival time not confirmed"
        earlier_th = f"ยกเลิกเวลาประมาณเดิม {_clock(w['start'])}–{_clock(w['end'])} แล้ว" if w else "ยังไม่ยืนยันเวลาถึง"
        nxt = _clock(a['nextStatusUpdate']['at'])
        return {"state": "held", "text": f"Transport: on hold; new time not known; {earlier}. "
                f"Next update {nxt} from the coordinator desk (status update, not arrival).",
                "th": f"การรับส่ง: พักไว้ก่อน ยังไม่ทราบเวลาใหม่ {earlier_th} "
                f"แจ้งความคืบหน้าครั้งถัดไป {nxt} จากโต๊ะประสานงาน (เป็นการแจ้งสถานะ ไม่ใช่เวลาที่ทีมจะถึง)"}
    if a["state"] == "closed":
        at = _clock(a["closedAt"])
        return {"state": a["outcome"], "text": {
            "done": f"Picked up by Team {t} at {at}.",
            "already_left": f"Team {t} found the place empty at {at}. If you still need help, call again.",
            "not_found": f"Team {t} couldn't find you at {at}. Call again with a landmark near you.",
            "needs_more_help": "Back on the list: a team saw you need more help. Call again if it becomes an emergency.",
        }[a["outcome"]], "th": {
            "done": f"{thai.team(t)} รับตัวแล้วเมื่อ {at}",
            "already_left": f"{thai.team(t)} ไปถึงเมื่อ {at} แต่ไม่พบใคร หากยังต้องการความช่วยเหลือให้โทรอีกครั้ง",
            "not_found": f"{thai.team(t)} หาคุณไม่พบเมื่อ {at} โทรอีกครั้งพร้อมบอกจุดสังเกตที่อยู่ใกล้คุณ",
            "needs_more_help": "กลับเข้ารายการอีกครั้ง: ทีมเห็นว่าคุณต้องการความช่วยเหลือเพิ่ม หากกลายเป็นเหตุฉุกเฉินให้โทรอีกครั้ง",
        }[a["outcome"]]}
    if a["state"] == "on_scene":
        return {"state": "on_scene", "text": f"Team {t} is at your place.", "th": f"{thai.team(t)} อยู่ที่บ้านของคุณแล้ว"}
    if a["state"] == "on_the_way":
        return {"state": "on_the_way", "text": f"Team {t} is on the way.", "th": f"{thai.team(t)} กำลังเดินทางไปหาคุณ"}
    if a.get("window"):
        w = a["window"]
        span = f"{_clock(w['start'])}–{_clock(w['end'])}"
        return {"state": "window", "text": f"Team {t} expects to reach you about {span} (team estimate, not a promise).",
                "th": f"{thai.team(t)} คาดว่าจะถึงประมาณ {span} (เป็นการประมาณของทีม ไม่ใช่คำสัญญา)"}
    return {"state": "taken", "text": f"Team {t} has taken your request. They haven't set a time yet.",
            "th": f"{thai.team(t)} รับคำขอของคุณแล้ว ยังไม่ได้กำหนดเวลา"}


def resident_status(store: Store, token: str, now: str) -> dict | None:
    ref = store.seed.get("statusTokens", {}).get(token)
    if ref is None:
        return None
    report = next((r for r in store.seed.get("reports", []) if r["reportId"] == ref["reportId"]), None)
    responses = store.seed.get("receiptResponses", {}).get(ref["reportId"], [])
    receipt = responses[-1] if responses else None
    times = [(report or {}).get("receivedAt"), (report or {}).get("reviewedAt"), None,
             receipt["at"] if receipt and receipt["answer"] == "yes" else None]
    base = {"reportId": ref["reportId"], "generatedAt": now, "label": "Your request (ReachPoint demo, synthetic)",
            "receipt": receipt, "completedAt": times}
    if ref.get("caseId") is None:
        if report and report["status"] == "rejected":
            why = report.get("rejectReason", "")
            return {**base, "state": "closed", "lines": [{"state": "closed",
                    "text": "A coordinator closed this request: " + why + ". Call again if you still need help.",
                    "th": f"ผู้ประสานงานปิดคำขอนี้แล้ว: {why} หากยังต้องการความช่วยเหลือให้โทรอีกครั้ง"}]}
        return {**base, "state": "received", "lines": [{"state": "received", "text": "We received your request. A coordinator is reading it now.",
                                                        "th": "เราได้รับคำขอของคุณแล้ว ผู้ประสานงานกำลังอ่านอยู่"}]}
    case = next(c for c in store.cases if c["caseId"] == ref["caseId"])
    lines = []
    for n in case["needs"]:
        if n["type"] != "evacuation_transport":
            continue
        for i, g in enumerate(n["groups"]):
            lines.append({"family": g["label"], "familyTh": thai.family(g["label"]),
                          **_family_line(store, n, f"{n['listingId']}-G{i + 1}")})
    if lines and all(line["state"] == "done" for line in lines):
        listing_ids = {need["listingId"] for need in case["needs"]}
        finished = [a["closedAt"] for a in store.seed.get("allocations", [])
                    if a["listingId"] in listing_ids and a.get("outcome") == "done" and a.get("closedAt")]
        times[2] = max(finished) if finished else None
    if not lines:
        lines.append({"state": "reviewed", "text": "Your request was reviewed and is on the list for supplies or medical help.",
                      "th": "คำขอของคุณได้รับการตรวจสอบแล้ว และอยู่ในรายการรอรับสิ่งของหรือความช่วยเหลือทางการแพทย์"})
    return {**base, "caseId": case["caseId"], "state": "reviewed", "lastConfirmedAt": case["lastConfirmedAt"], "lines": lines}
