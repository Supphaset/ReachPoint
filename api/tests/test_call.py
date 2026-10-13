"""The caller conversation (/call chat and voice): question order, language, in-chat pins, confirmation, demo rooms
and Pinpoint parsing. Gemini is replaced by fixed functions, so no network and no key are used."""

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

import api.main as main  # noqa: E402
from api.intake import conversation as C  # noqa: E402
from api.intake.facts import SUMMARY_TOPIC, FloodCase, next_topic  # noqa: E402
from api.intake.live_voice import is_confirm  # noqa: E402

A, B = {"X-Demo-Room": "call-aaaa"}, {"X-Demo-Room": "call-bbbb"}
FULL = dict(people_count=3, people_details="2 adults, grandma", water_level="chest", water_trend="rising",
            current_shelter="2nd floor", injuries="none", urgent_needs="boat")


def test_name_and_age_never_delay_help():
    assert "ฉุกเฉิน" in next_topic(FloodCase(immediate_danger=True))  # danger: where first
    first = next_topic(FloodCase())
    assert "ชื่อ" not in first  # what's happening, who and where come before any name
    c = FloodCase(location="B-3 market", **FULL)
    assert "ติดต่อกลับ" in next_topic(c)  # optional callback number, so a team can verify
    c.callback_contact = "skip"
    assert "ชื่อ" in next_topic(c)  # optional name last
    c.unavailable_fields = ["reporter_name"]
    assert next_topic(c) == SUMMARY_TOPIC
    assert "reporter_age" not in FloodCase.model_fields


def test_the_caller_language_follows_their_words():
    assert C.lang_of("น้ำถึงอกแล้ว") == "th" and C.lang_of("water is at my chest") == "en"
    assert C.lang_of("12/3", "en") == "en"  # no letters: keep the current language
    assert is_confirm("ยืนยันส่งคำขอ") and is_confirm("Confirm and send.") and not is_confirm("confirm")


@pytest.fixture
def client(monkeypatch):
    """Fixed readings instead of Gemini; the keyword stand-in for the report; rules instead of the agent."""
    monkeypatch.setattr(main, "USE_AI", True)
    monkeypatch.setattr(C, "_extract", lambda words: FloodCase(**FULL, callback_contact="skip",
                                                                 unavailable_fields=["reporter_name"]))
    monkeypatch.setattr(C, "_reply", lambda case, topic, words, lang, pinned=False: f"[{lang}] {topic}")
    from api.intake.extract import extract
    monkeypatch.setattr(main, "extract", lambda text, use_model=True: extract(text, use_model=False))
    monkeypatch.setattr(main.triage, "run_agent", main.triage.rule_proposals)
    return TestClient(main.app)


def test_chat_with_a_pin_confirms_once_into_the_callers_own_room(client):
    s = client.post("/api/call/sessions", json={"lang": "en"}, headers=A).json()
    assert s["lang"] == "en" and s["messages"][0]["text"].startswith("I'll help")
    sid = s["sessionId"]
    s = client.post(f"/api/call/sessions/{sid}/turn", json={"text": "We are 3, water at the chest", "turnId": "t1"}, headers=A).json()
    assert not s["canConfirm"]  # where they are is still missing
    again = client.post(f"/api/call/sessions/{sid}/turn", json={"text": "We are 3, water at the chest", "turnId": "t1"}, headers=A).json()
    assert again["revision"] == s["revision"]  # a retried turn is not recorded twice
    s = client.post(f"/api/call/sessions/{sid}/pin", headers=A, json={"location": {
        "kind": "pin", "lat": 7.0086, "lon": 100.4747, "method": "gps", "accuracyM": 12}}).json()
    assert s["pinned"]["status"] == "located" and s["case"]["location"] == s["pinned"]["landmarkLabel"]
    assert s["canConfirm"] and s["summary"].startswith("Summary of your request")
    stale = client.post(f"/api/call/sessions/{sid}/confirm", json={"submissionId": "c1", "expectedRevision": 0}, headers=A)
    assert stale.status_code == 409  # an older summary can't be confirmed
    done = client.post(f"/api/call/sessions/{sid}/confirm", json={"submissionId": "c1", "expectedRevision": s["revision"]}).json()
    assert done["sent"]["reportId"]  # confirmed with no room header (as voice does): still the conversation's room
    twice = client.post(f"/api/call/sessions/{sid}/confirm", json={"submissionId": "c2", "expectedRevision": s["revision"]}).json()
    assert twice["sent"] == done["sent"]  # one report, however many confirms
    rid = done["sent"]["reportId"]
    row = next(r for r in client.get("/api/views/reviewQueue", headers=A).json()["reports"] if r["reportId"] == rid)
    assert row["location"]["method"] == "gps" and row["channel"] == "chat"
    assert rid not in [r["reportId"] for r in client.get("/api/views/reviewQueue", headers=B).json()["reports"]
                       if r["text"] == row["text"]]


def test_clearing_the_pin_asks_where_again(client):
    sid = client.post("/api/call/sessions", json={"lang": "th"}).json()["sessionId"]
    client.post(f"/api/call/sessions/{sid}/pin", json={"location": {"kind": "pin", "lat": 7.0086, "lon": 100.4747, "method": "map"}})
    s = client.post(f"/api/call/sessions/{sid}/pin", json={"location": None}).json()
    assert s["pinned"] is None and s["messages"][-1]["text"].startswith("ลบตำแหน่ง")


def test_pinpoint_reply_is_read_from_autocomplete_then_details(monkeypatch):
    from api.location import pinpoint as P

    class R:
        def __init__(self, body):
            self.body = body

        def raise_for_status(self):
            pass

        def json(self):
            return self.body

    replies = iter([R({"success": True, "data": [{"LocationID": "L1", "FormattedAddress": "ซอยหลังตลาดกิมหยง หาดใหญ่"}]}),
                    R({"success": True, "data": {"LocationID": "L1", "LAT_LON": "7.0086, 100.4747",
                                                 "FormattedAddress": "ซอยหลังตลาดกิมหยง หาดใหญ่"}})])
    monkeypatch.setattr(P.httpx, "post", lambda *a, **k: next(replies))
    monkeypatch.setattr(P, "_config", lambda name: "test-key" if name == "PINPOINT_API_KEY" else None)
    hit = P.geocode("12/3 ซอยหลังตลาดกิมหยง")
    assert hit["at"] == [100.4747, 7.0086] and "กิมหยง" in hit["label"]
