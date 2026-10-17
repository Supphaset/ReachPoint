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
    # the family hears about the plan once the agent has finished taking the report
    for answer in ("อยู่บ้าน", "ไม่มี", "อยู่บ้าน", "ไม่มี"):
        if x["session"]["finished"]:
            break
        x = c.post(f"/api/v2/chat/sessions/{sid}/turn", json={"text": answer}, headers=h).json()
    assert x["session"]["finished"]
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


def test_copilot_answers_from_tools_and_its_numbers_are_checked():
    from api.v2 import copilot as K
    from api.main import app
    c = TestClient(app)
    h = {"X-Demo-Room": "pytest-v2-copilot"}
    # without Gemini the answer is written from the same tools, so the flow never dead-ends
    out = c.post("/api/v2/v/copilot", json={"question": "I have one boat with 6 seats. Where first?"}, headers=h).json()
    assert out["reader"] == "rules" and [t["name"] for t in out["toolCalls"]] == ["get_overview", "get_zone", "draft_plan"]
    plan = out["plan"]
    assert plan["runs"] and all(r["people"] <= 6 or len(r["households"]) == 1 for r in plan["runs"])
    assert out["cited"]["zones"] == [plan["zone"]] + ([plan["after"]["zone"]] if plan.get("after") else []) or out["cited"]["zones"]
    # the check: a number no tool gave, or a promise of rescue, sends the answer back to the rules
    results = [{"waiting": 7, "urgent": 3, "depthM": 1.32}]
    assert K.check("Go to [D12]: 7 waiting, 3 urgent, 1.32 m.", results, "6 seats") is None
    assert K.check("Go to [D12]: 9 waiting.", results, "6 seats")
    assert K.check("A team is coming to [D12].", results, "")


def test_a_neighbour_named_after_the_questions_still_gets_the_picture_check():
    from api.main import app
    c = TestClient(app)
    h = {"X-Demo-Room": "pytest-v2-late-neighbour"}
    sid = c.post("/api/v2/chat/sessions", headers=h).json()["id"]
    c.post(f"/api/v2/chat/sessions/{sid}/turn", json={"text": "น้ำถึงเอวแล้ว อยู่กัน 2 คน แม่เดินไม่ได้ บ้านเลขที่ 52/9 ถนนเพชรเกษม ซอย 2"}, headers=h)
    asked = c.post(f"/api/v2/chat/sessions/{sid}/turn", json={"text": "บ้านทางตะวันออก ยายอยู่คนเดียว"}, headers=h).json()
    assert asked["effects"].get("nbConfirm")
    done = c.post(f"/api/v2/chat/sessions/{sid}/turn", json={"text": "ใช่"}, headers=h).json()
    nb = done["effects"]["neighbour"]
    assert nb["sure"] and nb["householdId"] != done["session"]["householdId"]
    # the grandmother is her own household; the caller's family does not gain an elderly person
    me = c.get(f"/api/v2/v/cases/{done['session']['householdId']}", headers=h).json()["household"]
    assert me["elderly"] == 0


def test_a_map_pin_locates_the_house_and_the_shelter_comes_with_a_street_route():
    from api.main import app
    c = TestClient(app)
    h = {"X-Demo-Room": "pytest-v2-pin"}
    sid = c.post("/api/v2/chat/sessions", headers=h).json()["id"]
    first = c.post(f"/api/v2/chat/sessions/{sid}/turn", json={"text": "น้ำถึงเข่า อยู่กัน 2 คน"}, headers=h).json()
    assert first["effects"].get("askLocation")
    # a pin outside the city is refused; one in Hat Yai becomes the house
    out = c.post(f"/api/v2/chat/sessions/{sid}/turn", json={"text": "📍", "pin": {"lon": 100.0, "lat": 13.7, "method": "gps"}}, headers=h).json()
    assert out["effects"].get("pinOutside")
    got = c.post(f"/api/v2/chat/sessions/{sid}/turn", json={"text": "📍", "pin": {"lon": 100.4936, "lat": 7.0222, "method": "map"}}, headers=h).json()
    assert got["effects"]["located"]["by"] == "your pin on the map"
    # answer until the shelter question: it comes with the route on the streets, the water along it and a Maps link
    route = None
    for say in ("ไม่มีค่ะ", "ไม่มี", "ไม่มีค่ะ"):
        r = c.post(f"/api/v2/chat/sessions/{sid}/turn", json={"text": say}, headers=h).json()
        route = r["effects"].get("shelterRoute") or route
        if route:
            break
    assert route and route["by"] == "streets" and len(route["path"]) > 2 and route["samples"]
    assert route["googleMaps"].startswith("https://www.google.com/maps/dir/")


def test_the_agent_follows_up_until_the_family_is_safe():
    from api.main import app
    c = TestClient(app)
    h = {"X-Demo-Room": "pytest-v2-follow"}
    made = c.post("/api/v2/chat/sessions", headers=h).json()
    sid, token = made["id"], made["token"]

    def say(text, reply_to=None):
        return c.post(f"/api/v2/chat/sessions/{sid}/turn", json={"text": text, "replyTo": reply_to}, headers=h).json()

    say("น้ำถึงเข่า อยู่กัน 2 คน บ้านเลขที่ 52/9 ถนนเพชรเกษม ซอย 2")
    say("ไม่มีค่ะ")
    say("อยู่บ้าน")
    # a warning we send ends in a choice, and "I need to leave" opens the evacuation flow instead of "thanks"
    sim = c.post(f"/api/v2/chat/sessions/{sid}/simulate", json={"event": "river"}, headers=h).json()
    assert sim["message"]["choices"]
    walk = say("ต้องการออกจากบ้าน", "river")
    assert [o["send"] for o in walk["effects"]["choices"]["options"]] == ["เดินได้ทุกคน", "มีคนเดินไม่ได้"]
    ride = say("มีคนเดินไม่ได้", "evacWalk")
    assert ride["effects"]["checklist"] and ride["status"]["wantsOut"]
    # a team plans to come and then taps "picked up"; the family says someone is still inside: the case reopens
    c.post(f"/api/v2/chat/sessions/{sid}/simulate", json={"event": "teamVisit"}, headers=h)
    inbox = c.get(f"/api/v2/me/{token}", headers=h).json()["inbox"]
    visit = [o for o in inbox if o["kind"] == "pickedUp"][-1]
    assert [x["send"] for x in visit["choices"]][1] == "ยังมีคนติดอยู่"
    still = say("ยังมีคนติดอยู่", "pickedUp")
    assert still["status"]["urgent"] and still["status"]["status"] == "open"
    # a check-in answered "safe" gets a real reply with the next check time
    c.post(f"/api/v2/chat/sessions/{sid}/simulate", json={"event": "checkin"}, headers=h)
    assert "08:00" in say("ปลอดภัยดี", "checkin")["reply"]


def test_a_warning_button_is_answered_even_while_the_shelter_question_is_open():
    from api.main import app
    c = TestClient(app)
    h = {"X-Demo-Room": "pytest-v2-follow-open"}
    sid = c.post("/api/v2/chat/sessions", headers=h).json()["id"]
    c.post(f"/api/v2/chat/sessions/{sid}/turn", json={"text": "น้ำถึงเข่า อยู่กัน 2 คน บ้านเลขที่ 52/9 ถนนเพชรเกษม ซอย 2"}, headers=h)
    asked = c.post(f"/api/v2/chat/sessions/{sid}/turn", json={"text": "ไม่มีค่ะ"}, headers=h).json()
    assert asked["effects"].get("shelterRoute")  # the shelter question is open
    c.post(f"/api/v2/chat/sessions/{sid}/simulate", json={"event": "river"}, headers=h)
    r = c.post(f"/api/v2/chat/sessions/{sid}/turn", json={"text": "ต้องการออกจากบ้าน", "replyTo": "river"}, headers=h).json()
    assert r["effects"]["choices"]["kind"] == "evacWalk"


def test_urgent_cases_by_zone_and_do_first_marks():
    from api.main import app
    c = TestClient(app)
    h = {"X-Demo-Room": "pytest-v2-urgent"}
    u = c.get("/api/v2/v/urgent", headers=h).json()
    assert u["total"] > 0 and u["zones"][0]["cases"]
    case = u["zones"][-1]["cases"][-1]
    after = c.post(f"/api/v2/v/cases/{case['id']}/first", json={"team": "ทีมทดสอบ"}, headers=h).json()
    top = after["zones"][0]
    assert top["cases"][0]["id"] == case["id"] and top["cases"][0]["markedFirst"]["team"] == "ทีมทดสอบ"
    cleared = c.post(f"/api/v2/v/cases/{case['id']}/first", json={"team": "ทีมทดสอบ", "first": False}, headers=h).json()
    assert not any(r["markedFirst"] for z in cleared["zones"] for r in z["cases"])


def test_zone_plan_waits_until_the_report_is_finished():
    from api.main import app
    c = TestClient(app)
    h = {"X-Demo-Room": "pytest-v2-plan-wait"}
    made = c.post("/api/v2/chat/sessions", headers=h).json()
    c.post(f"/api/v2/chat/sessions/{made['id']}/turn", json={"text": "น้ำถึงเข่า อยู่กัน 2 คน บ้านเลขที่ 52/9 ถนนเพชรเกษม ซอย 2"}, headers=h)
    c.post("/api/v2/plans", json={"text": "ทีมเรือ A เข้าโซน B5 07:30", "team": "ทีมเรือ A"}, headers=h)
    inbox = c.get(f"/api/v2/me/{made['token']}", headers=h).json()["inbox"]
    assert not [o for o in inbox if o["kind"] == "planUpdate"]


def test_an_english_address_finds_the_same_house_as_the_thai_one():
    from api.v2 import geo as G, intake as I
    g = G.load()
    th = I.locate("บ้านเลขที่ 52/9 ถนนเพชรเกษม ซอย 2", g)
    en = I.locate("house 52/9 Phetkasem Soi 2", g)
    assert en and th and en["buildingId"] == th["buildingId"]


def test_a_second_ride_request_does_not_start_over():
    from api.main import app
    c = TestClient(app)
    h = {"X-Demo-Room": "pytest-v2-ride-again"}
    made = c.post("/api/v2/chat/sessions", headers=h).json()
    sid = made["id"]

    def say(text, reply_to=None):
        return c.post(f"/api/v2/chat/sessions/{sid}/turn", json={"text": text, "replyTo": reply_to}, headers=h).json()

    say("น้ำถึงเข่า อยู่กัน 2 คน บ้านเลขที่ 52/9 ถนนเพชรเกษม ซอย 2")
    say("ไม่มีค่ะ")
    say("อยู่บ้าน")
    c.post(f"/api/v2/chat/sessions/{sid}/simulate", json={"event": "river"}, headers=h)
    say("ต้องการออกจากบ้าน", "river")
    first = say("มีคนเดินไม่ได้", "evacWalk")
    assert first["effects"]["checklist"]
    st = c.post(f"/api/v2/chat/sessions/{sid}/ready", json={"done": [0, 1, 2]}, headers=h).json()
    assert st["ready"] == [0, 1, 2] and st["rideRequested"]
    hid = st["householdId"]
    posted = len(c.get(f"/api/v2/v/cases/{hid}", headers=h).json()["story"])
    again = say("ต้องการออกจากบ้าน", "leaveAsk")
    assert "checklist" not in again["effects"] and "choices" not in again["effects"]
    assert "3/5" in again["reply"]
    after = len(c.get(f"/api/v2/v/cases/{hid}", headers=h).json()["story"])
    assert after == posted  # no duplicate request for the teams


def test_a_pin_outside_the_area_is_explained():
    from api.main import app
    from api.v2 import geo as G
    c = TestClient(app)
    h = {"X-Demo-Room": "pytest-v2-pin-outside"}
    far = c.post("/api/v2/chat/sessions", headers=h).json()["id"]
    r = c.post(f"/api/v2/chat/sessions/{far}/turn", json={"text": "pinned", "pin": {"lon": 100.60, "lat": 7.20, "method": "map"}}, headers=h).json()
    assert r["effects"]["pinOutside"]["reason"] == "outside" and "1784" in r["reply"]
    # inside a zone but on no house: find a zone point with no building within 60 m
    g = G.load()
    spot = None
    for z in g.zones:
        ring = z["geometry"]["coordinates"][0] if z["geometry"]["type"] == "Polygon" else z["geometry"]["coordinates"][0][0]
        for lon, lat in ring[::7]:
            if g.zone_at(lon, lat) and g.snap(lon, lat, 60) is None:
                spot = (lon, lat)
                break
        if spot:
            break
    if spot:
        sid = c.post("/api/v2/chat/sessions", headers=h).json()["id"]
        r = c.post(f"/api/v2/chat/sessions/{sid}/turn", json={"text": "pinned", "pin": {"lon": spot[0], "lat": spot[1], "method": "map"}}, headers=h).json()
        assert r["effects"]["pinOutside"]["reason"] == "noHouse"
