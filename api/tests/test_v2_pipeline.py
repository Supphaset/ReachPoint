import os

os.environ.setdefault("REACHPOINT_AI", "off")

from fastapi.testclient import TestClient  # noqa: E402

from api.v2 import pipeline as P  # noqa: E402
from api.v2.reader import read_rules  # noqa: E402


def test_scenario_households_are_counted_once_and_levels_track_the_truth():
    w = P.run(100)
    truth = {z: dict(v) for z, v in P.scenario()["truth"]["wseByZone"].items()}
    errs = [abs(l.wse_m - truth[z][99]) for z, l in w.levels.items() if l.wse_m and truth[z].get(99)]
    assert errs and sum(errs) / len(errs) < 0.3
    msgs = [m for m in P.scenario()["messages"] if m["atH"] <= 100]
    true_heard = {m["truth"]["about"] for m in msgs if m["truth"].get("about")} | \
                 {m["truth"]["neighbour"]["neighbourHousehold"] for m in msgs if m["truth"].get("neighbour")}
    # merging keeps the household count close to the real number of families heard about
    assert len(w.households) <= len(true_heard) * 1.12


def test_most_reports_are_confirmed_and_few_are_doubtful():
    w = P.run(100)
    labels = [o.label for o in w.obs]
    assert labels.count("doubtful") / len(labels) < 0.08
    assert labels.count("confirmed") > labels.count("unconfirmed")


def test_planted_wrong_reports_are_mostly_flagged():
    w = P.run(150)
    planted = {m["id"] for m in P.scenario()["messages"] if m["truth"].get("planted")}
    flagged = {o.message_id for o in w.obs if o.label == "doubtful"}
    assert planted and len(planted & flagged) / len(planted) >= 0.5


def test_unknown_is_not_dry_before_any_report():
    w = P.run(10)
    assert all(l.wse_m is None for l in w.levels.values())


def test_neighbour_reader_takes_the_side_and_the_people():
    r = read_rules("น้ำถึงเข่า บ้านฝั่งตรงข้ามมีครอบครัว 3 คน มีเด็ก 1 คน ยังไม่ได้ออกมา")
    assert r.get("neighbour") == {"side": "across", "people": 3, "children": 1}
    assert r.get("depthRange") == [0.4, 0.6]


def test_judge_conversation_lands_on_the_board():
    from api.main import app
    c = TestClient(app)
    h = {"X-Demo-Room": "pytest-v2"}
    c.post("/api/v2/clock", json={"action": "reset"}, headers=h)
    before = c.get("/api/v2/state", headers=h).json()["overall"]["households"]
    sid = c.post("/api/v2/chat/sessions", headers=h).json()["id"]
    x = c.post(f"/api/v2/chat/sessions/{sid}/turn", json={"text": "น้ำถึงเอวแล้ว อยู่กัน 2 คน แม่เดินไม่ได้ บ้านเลขที่ 52/9 ถนนเพชรเกษม ซอย 2"}, headers=h).json()
    assert x["effects"]["household"]["zoneId"] and x["zone"]["id"] == x["effects"]["household"]["zoneId"]
    assert c.get("/api/v2/state", headers=h).json()["overall"]["households"] == before + 1
    # neighbour answers either match a known house or add one; the count never double-counts the judge
    for _ in range(4):
        sess = x["session"]
        if sess["pending"] in ("left", "right", "across"):
            x = c.post(f"/api/v2/chat/sessions/{sid}/turn", json={"text": "มียายอยู่คนเดียว"}, headers=h).json()
            break
        x = c.post(f"/api/v2/chat/sessions/{sid}/turn", json={"text": "ไม่มี"}, headers=h).json()
    plan = c.post("/api/v2/plans", json={"text": f"ทีมเรือเรา 8 ที่นั่ง จะเข้า {x['zone']['id']} ประมาณ 15:00 อพยพ"}, headers=h).json()
    assert plan["plan"]["told"] >= 1
    me = c.get(f"/api/v2/me/{x['session']['token']}", headers=h).json()
    assert any(i["kind"] == "planUpdate" for i in me["inbox"])
