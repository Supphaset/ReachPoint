import os

os.environ.setdefault("REACHPOINT_AI", "off")

from fastapi.testclient import TestClient  # noqa: E402

from api.v2 import pipeline as P  # noqa: E402
from api.v2.reader import read_rules  # noqa: E402


def test_scenario_households_are_counted_once_and_levels_track_the_truth():
    w = P.run(100)
    # depth at households: the model corrected by the other reports beats the model alone (truth is a different run)
    sample = [m for m in P.scenario()["messages"] if m["kind"] in ("self", "reply") and 60 < m["atH"] <= 100
              and m["truth"].get("trueDepthM") is not None][::5]
    both = model = 0.0
    for m in sample:
        own = [o for o in w.assim_index.obs if o.id == m["id"]]
        for o in own:
            o.t += 1e6
        d, sd, n, prior = P.local_depth(w, m["pin"]["lon"], m["pin"]["lat"], m["atH"])
        for o in own:
            o.t -= 1e6
        both += abs(d - m["truth"]["trueDepthM"])
        model += abs(prior - m["truth"]["trueDepthM"])
    assert sample and both < model
    msgs = [m for m in P.scenario()["messages"] if m["atH"] <= 100]
    true_heard = {m["truth"]["about"] for m in msgs if m["truth"].get("about")} | \
                 {m["truth"]["neighbour"]["neighbourHousehold"] for m in msgs if m["truth"].get("neighbour")}
    # merging keeps the household count close to the real number of families heard about
    sure = len(w.households) - sum(1 for h in w.households.values() if h.possible_duplicate_of)
    assert sure <= len(true_heard) * 1.1


def test_most_reports_fit_their_neighbours_and_few_are_doubtful():
    w = P.run(100)
    labels = [o.label for o in w.obs]
    assert labels.count("doubtful") / len(labels) < 0.08
    assert labels.count("consistent") > labels.count("unchecked")


def test_reports_correct_the_model_locally_not_everywhere():
    from api.v2 import assim as A
    obs = [A.Ob("a", 0, 0, 10, 0.9, 1.1, "self", 0.4), A.Ob("b", 60, 0, 10, 0.9, 1.1, "self", 0.4)]
    near, sd_near, n1 = A.analyse(obs, 30, 0, 10, 0.4)
    far, sd_far, n2 = A.analyse(obs, 3000, 0, 10, 0.4)
    assert near > 0.8 and sd_near < sd_far
    assert far == 0.4 and n2 == 0  # no report nearby: the model alone, with its full uncertainty


def test_a_report_the_neighbours_contradict_is_doubtful():
    from api.v2 import assim as A
    obs = [A.Ob(str(i), i * 40, 0, 10, 0.4, 0.6, "self", 0.5) for i in range(4)] + [A.Ob("odd", 80, 20, 10, 2.5, 3.2, "self", 0.5)]
    A.check(obs)
    assert [o.id for o in obs if o.doubtful] == ["odd"]


def test_planted_wrong_reports_are_mostly_flagged():
    w = P.run(150)
    planted = {m["id"] for m in P.scenario()["messages"] if m["truth"].get("planted")}
    flagged = {o.message_id for o in w.obs if o.label == "doubtful"}
    assert planted and len(planted & flagged) / len(planted) >= 0.5


def test_unknown_is_not_dry_before_any_report():
    first = min(m["atH"] for m in P.scenario()["messages"] if m["channel"] != "bulletin")
    w = P.run(first - 0.5)
    assert all(l.wse_m is None for l in w.levels.values())


def test_neighbour_reader_takes_the_direction_and_the_people():
    r = read_rules("น้ำถึงเข่า บ้านทางทิศเหนือมีครอบครัว 3 คน มีเด็ก 1 คน ยังไม่ได้ออกมา")
    assert r.get("neighbour") == {"side": "north", "people": 3, "children": 1}
    assert r.get("depthRange") == [0.4, 0.6]
    # without a compass direction the side is unknown, and the agent asks
    assert read_rules("บ้านข้างๆ มียายอยู่คนเดียว").get("neighbour")["side"] == "unknown"
    # several houses in one message, each with its own direction and people
    two = [f.value for f in read_rules("บ้านทางทิศตะวันออกมียายอยู่คนเดียว ทางทิศตะวันตกมีครอบครัว 4 คน").all("neighbour")]
    assert two == [{"side": "east", "people": 1, "elderly": 1}, {"side": "west", "people": 4}]
    # a direction that isn't about a house is not a neighbour
    assert not read_rules("น้ำไหลมาทางทิศเหนือ อยู่กัน 2 คน").all("neighbour")


def test_compass_neighbours_point_the_right_way():
    from api.v2 import geo as G
    geo = G.load()
    b = next(iter(geo.buildings.values()))
    for side, ids in geo.neighbours(b).items():
        for nid in ids:
            n = geo.buildings[nid]
            dx, dy = n.x - b.x, n.y - b.y
            assert {"north": dy >= abs(dx) - 1e-6, "south": -dy >= abs(dx) - 1e-6,
                    "east": dx >= abs(dy) - 1e-6, "west": -dx >= abs(dy) - 1e-6}[side]


def test_judge_conversation_lands_on_the_board():
    from api.main import app
    c = TestClient(app)
    h = {"X-Demo-Room": "pytest-v2"}
    c.post("/api/v2/clock", json={"action": "reset"}, headers=h)
    before = c.get("/api/v2/state", headers=h).json()["overall"]["households"]
    sid = c.post("/api/v2/chat/sessions", headers=h).json()["id"]
    x = c.post(f"/api/v2/chat/sessions/{sid}/turn", json={"text": "น้ำถึงเอวแล้ว อยู่กัน 2 คน แม่เดินไม่ได้ บ้านเลขที่ 52/9 ถนนเพชรเกษม ซอย 2 บ้านข้างๆ มียายอยู่คนเดียว"}, headers=h).json()
    assert x["effects"]["household"]["zoneId"] and x["zone"]["id"] == x["effects"]["household"]["zoneId"]
    # the neighbour is held until the agent knows which way that house is
    assert c.get("/api/v2/state", headers=h).json()["overall"]["households"] == before + 1
    for _ in range(4):
        if x["session"]["pending"] == "nb_dir":
            break
        x = c.post(f"/api/v2/chat/sessions/{sid}/turn", json={"text": "ไม่มี"}, headers=h).json()
    assert x["session"]["pending"] == "nb_dir"
    x = c.post(f"/api/v2/chat/sessions/{sid}/turn", json={"text": "ทิศตะวันออกค่ะ"}, headers=h).json()
    # the agent shows the house that way on the satellite picture and asks to confirm
    assert x["session"]["pending"] == "nb_confirm" and x["effects"]["nbConfirm"]["side"] == "east"
    x = c.post(f"/api/v2/chat/sessions/{sid}/turn", json={"text": "ใช่ค่ะ"}, headers=h).json()
    nb = x["effects"]["neighbour"]
    assert nb and nb["side"] == "east" and x["session"]["neighbours"][-1]["confirmed"]
    # matched to a known house (count unchanged) or added as one new house; the judge is never counted twice
    after = c.get("/api/v2/state", headers=h).json()["overall"]["households"]
    assert after == before + 1 + (0 if nb["known"] else 1)
    plan = c.post("/api/v2/plans", json={"text": f"ทีมเรือเรา 8 ที่นั่ง จะเข้า {x['zone']['id']} ประมาณ 15:00 อพยพ"}, headers=h).json()
    assert plan["plan"]["told"] >= 1
    me = c.get(f"/api/v2/me/{x['session']['token']}", headers=h).json()
    assert any(i["kind"] == "planUpdate" for i in me["inbox"])


def test_volunteer_pages_tell_the_story_and_close_the_loop():
    from api.main import app
    c = TestClient(app)
    h = {"X-Demo-Room": "pytest-v2-volunteer"}
    c.post("/api/v2/clock", json={"action": "reset"}, headers=h)
    o = c.get("/api/v2/v/overview", headers=h).json()
    zid = o["zones"][0]["id"]
    z = c.get(f"/api/v2/v/zones/{zid}", headers=h).json()
    hid = z["households"][0]["id"]
    case = c.get(f"/api/v2/v/cases/{hid}", headers=h).json()
    # every message says why it belongs to this family; addresses stay masked until a team's plan covers the zone
    assert case["story"] and all(s["how"] for s in case["story"])
    assert not case["unlocked"] and case["address"] is None
    c.post("/api/v2/plans", json={"text": f"เรือ 8 ที่ จะเข้า {zid} ราวบ่ายสอง", "team": "ทีมทดสอบ"}, headers=h)
    case = c.get(f"/api/v2/v/cases/{hid}?team=ทีมทดสอบ", headers=h).json()
    assert case["unlocked"]
    # one tap: picked up; the family's phone is told and the zone counts it
    after = c.post(f"/api/v2/v/cases/{hid}/outcome", json={"outcome": "pickedUp", "team": "ทีมทดสอบ"}, headers=h).json()
    assert after["household"]["status"] == "evacuated" and after["contact"]["sent"][-1]["kind"] == "pickedUp"
    z2 = c.get(f"/api/v2/v/zones/{zid}", headers=h).json()
    assert z2["totals"]["open"] == z["totals"]["open"] - 1
    feed = c.get("/api/v2/v/feed?kind=team", headers=h).json()
    assert feed["items"] and feed["items"][0]["householdId"] == hid


def test_voice_call_turns_go_through_the_intake_agent():
    # the Live bridge's turn function is the same agent as typing: words in, facts and a reply out
    from api.v2 import routes as R
    from api.main import app
    c = TestClient(app)
    h = {"X-Demo-Room": "pytest-v2-live"}
    sid = c.post("/api/v2/chat/sessions", headers=h).json()["id"]
    out = R._rooms_ref.current_id.set("pytest-v2-live")
    try:
        r = R.turn(sid, "น้ำถึงเอวแล้ว อยู่กัน 2 คน บ้านเลขที่ 52/9 ถนนเพชรเกษม ซอย 2", "voice")
    finally:
        R._rooms_ref.current_id.reset(out)
    assert r["reply"] and r["effects"]["household"]["zoneId"]
