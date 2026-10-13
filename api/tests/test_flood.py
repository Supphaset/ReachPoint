"""Flood evidence, replay isolation and the live planning handoff. Synthetic only; no AI/network."""
import copy
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

import api.main as main
from api.rules.water import estimate, local_estimates
from api.server.flood_replay import FloodReplay
from api.server.memory import MemoryStore, Refused
from api.views.flood import flood_map
from api.views.planning import panel

NOW = "2026-10-11T03:32:00Z"


def observation(oid="W-1", depth=0.8, **kw):
    return {"observationId": oid, "segmentId": "B-4-L5", "siteId": "B-4-L5", "evidenceRef": oid,
            "observedAt": "2026-10-11T03:20:00Z", "reference": "street_ground", "depthM": depth,
            "uncertaintyM": 0.15, "band": None, "trend": "unknown", "review": "ai_read", **kw}


def test_comparable_measurements_produce_an_envelope_without_claiming_independence():
    e = estimate([observation(), observation("W-2", 0.9)], NOW)
    assert e["status"] == "available" and e["rangeM"] == [0.65, 1.05] and e["centralM"] == 0.85
    assert e["independence"] == "unknown" and e["sourceReferences"] == 2
    assert "no interpolation" in " ".join(e["reasons"])


def test_qualitative_bands_never_turn_into_metres():
    e = estimate([observation(depth=None, band="chest"), observation("W-2", None, band="waist")], NOW)
    assert e["status"] == "qualitative_only" and e["rangeM"] is None and e["centralM"] is None
    assert set(e["bands"]) == {"chest", "waist"}


def test_repeated_observation_reference_is_one_source_and_uses_actual_time():
    rows = [observation(evidenceRef="ONE", observedAt="2026-10-11T10:15:00+07:00"),
            observation("W-2", 1.0, evidenceRef="ONE", observedAt="2026-10-11T03:25:00Z")]
    assert estimate(rows, NOW)["rangeM"] is None
    e = estimate(rows + [observation("W-3", 1.0)], NOW)
    assert e["rangeM"] == [0.85, 1.15] and e["sourceReferences"] == 2


def test_more_repeated_messages_do_not_shrink_uncertainty():
    rows = [observation(), observation("W-2", 0.8)]
    before = estimate(rows, NOW)
    more = rows + [observation(f"W-copy-{i}", 0.8, evidenceRef="W-1", uncertaintyM=0.05) for i in range(20)]
    assert estimate(more, NOW)["rangeM"] == before["rangeM"] == [0.65, 0.95]


def test_conflicts_keep_the_wide_range_and_abstain_from_a_single_depth():
    e = estimate([observation(), observation("W-2", 2.0)], NOW)
    assert e["status"] == "conflicting" and e["rangeM"] == [0.65, 2.15] and e["centralM"] is None


@pytest.mark.parametrize("change", [{"reference": "indoor_floor"}, {"reference": "upper_floor"},
                                    {"observedAt": None}, {"observedAt": "2026-10-11T04:00:00Z"},
                                    {"observedAt": "2026-10-11T02:40:00Z"}])
def test_incomparable_or_undated_or_old_window_does_not_make_an_estimate(change):
    assert estimate([observation(), observation("W-2", **change)], NOW)["rangeM"] is None


def test_stale_reports_abstain_and_sites_never_mix():
    rows = [observation(), observation("W-2")]
    e = estimate(rows, "2026-10-11T10:00:00Z")
    assert e["status"] == "stale" and e["rangeM"] is None
    rows[1]["siteId"] = "another-site"
    assert all(e["rangeM"] is None for e in local_estimates(rows, NOW))
    assert len(local_estimates(rows + [observation("W-3", review="disputed")], NOW)) == 2


@pytest.fixture
def c():
    main.USE_AI = False
    main.reset()
    main.memory.clock.now = lambda: datetime(2026, 10, 11, 3, 32, tzinfo=timezone.utc)
    main.flood_replay = FloodReplay(main.memory.store.catalogue)
    return TestClient(main.app)


def test_full_replay_retry_reset_and_all_operational_negative_controls(c):
    before = copy.deepcopy(main.memory.store.seed)
    first = {"submissionId": "STEP-1", "expectedCursor": 0, "expectedRevision": 0, "count": 200}
    r = c.post("/api/demo/flood-replay/step", json=first)
    assert r.status_code == 200 and r.json()["cursor"] == 200
    assert c.post("/api/demo/flood-replay/step", json=first).json() == r.json()
    for i in range(1, 6):
        assert c.post("/api/demo/flood-replay/step", json={**first, "submissionId": f"STEP-{i + 1}",
                      "expectedCursor": i * 200, "expectedRevision": i}).status_code == 200
    view = c.get("/api/views/floodMap?source=replay").json()
    assert view["counters"]["received"] == 1200 and view["counters"]["urgentReports"] == 150
    assert view["counters"]["organized"] == 720 and view["counters"]["exceptions"] == 480
    assert view["counters"]["numericEstimates"] > 0 and view["counters"]["conflicts"] > 0
    assert view["teams"] == [] and all(s["coverage"]["activeJobs"] == 0 for s in view["segments"])
    assert "quote" not in str(view) and "text" not in view
    assert main.memory.store.seed == before  # drafts, areas, medical, resident status, jobs, history all unchanged
    reset = {"submissionId": "RESET", "expectedCursor": 1200, "expectedRevision": 6}
    assert c.post("/api/demo/flood-replay/reset", json=reset).json()["cursor"] == 0
    assert c.post("/api/demo/flood-replay/step", json={**first, "submissionId": "STALE-BEFORE-RESET"}).status_code == 409
    assert main.memory.store.seed == before


def test_replay_records_are_labelled_simulator_read_and_demo_reset_clears_the_replay(c):
    step = {"submissionId": "STEP-A", "expectedCursor": 0, "expectedRevision": 0, "count": 200}
    assert c.post("/api/demo/flood-replay/step", json=step).json()["cursor"] == 200
    reviews = {r["review"] for rec in main.flood_replay.snapshot()["records"]
               for r in (rec["assistance"], rec["observation"]) if r}
    assert reviews == {"simulator_read"}  # no model read these reports
    c.post("/api/demo/reset")
    snap = main.flood_replay.snapshot()
    assert snap["cursor"] == 0 and snap["records"] == []


def test_replay_failure_is_atomic_and_concurrent_tabs_cannot_double_advance(monkeypatch):
    import api.server.flood_replay as replay_module
    replay = FloodReplay(MemoryStore().store.catalogue)
    original = replay_module.process
    def broken(report, landmarks):
        if report["reportId"] == "SIM-0002":
            raise ValueError("synthetic processing failure")
        return original(report, landmarks)
    monkeypatch.setattr(replay_module, "process", broken)
    with pytest.raises(ValueError):
        replay.write("FAIL", 0, 0, 20)
    assert replay.cursor == 0 and replay.revision == 0 and replay.processed == [] and replay.done == {}
    monkeypatch.setattr(replay_module, "process", original)
    def submit(i):
        try:
            return replay.write(str(i), 0, 0, 20)["cursor"]
        except Refused as e:
            return e.code
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(submit, [1, 2]))
    assert sorted(map(str, results)) == ["20", "VERSION_CONFLICT"] and replay.cursor == 20


def water_body():
    return {"submissionId": "W-SUB", "reportId": "SYN-REPORT", "segmentId": "B-4-L5", "siteId": "B-4-L5",
            "quote": "B-4-L5: 0.8 m above street ground at 2026-10-11T03:20:00Z, rising.",
            "observedAt": "2026-10-11T03:20:00Z", "depthM": 0.8, "reference": "street_ground", "trend": "rising"}


def add_report():
    body = water_body()
    main.memory.store.seed.setdefault("reports", []).append({"reportId": body["reportId"], "text": body["quote"] + " Private synthetic narrative.", "channel": "text", "status": "proposed"})
    return body


def test_water_handoff_is_quote_supported_retry_safe_and_does_not_create_a_job(c):
    body = add_report()
    cases = copy.deepcopy(main.memory.store.cases)
    r = c.post("/api/water-observations", json=body)
    assert r.status_code == 200 and r.json()["value"]["review"] == "ai_read"
    assert c.post("/api/water-observations", json=body).json() == r.json()
    assert len(main.memory.store.seed["waterObservations"]) == 1 and main.memory.store.cases == cases
    assert main.memory.store.seed["waterObservations"][0]["quote"] == body["quote"]
    view = c.get("/api/views/floodMap").json()
    assert "Private synthetic narrative" not in str(view) and body["quote"] not in str(view)
    segment = next(s for s in view["segments"] if s["segmentId"] == "B-4-L5")
    assert segment["observations"][-1]["review"] == "ai_read"
    assert segment["estimates"][0]["rangeM"] is None  # one source is insufficient


@pytest.mark.parametrize("change", [{"depthM": 1.8}, {"reference": "indoor_floor"}, {"source": "field"},
                                    {"segmentId": "B-1-L1", "siteId": "B-1-L1"}, {"siteId": "HOUSE-1"},
                                    {"observedAt": "2026-10-11T03:21:00Z"}, {"evidenceRef": "MADE-UP"},
                                    {"trend": "falling"}, {"quote": "Invented measurement"}])
def test_water_handoff_rejects_unsupported_fields_without_partial_writes(c, change):
    body = add_report()
    before = copy.deepcopy(main.memory.store.seed)
    assert c.post("/api/water-observations", json={**body, **change}).status_code == 409
    assert main.memory.store.seed == before


def test_live_plan_accounts_for_claimed_groups_and_s1_failure_without_splitting():
    m = MemoryStore()
    before = panel(m.store, NOW)
    assert any(a["resourceId"] == "S1" for a in before["suggestion"]["assignments"])
    assert all(not a["split"] for a in before["suggestion"]["assignments"])
    claimed = m.write("CLAIM", lambda: m.claim("L-C01-EVAC", "T-S", ["L-C01-EVAC-G1"], 2))["value"]
    after_claim = panel(m.store, NOW)
    assert "L-C01-EVAC-G1" not in after_claim["needs"]
    assert after_claim["suggestion"]["suggestionId"] != before["suggestion"]["suggestionId"]
    m.write("FAIL", lambda: m.resource_unavailable("S1", "Boat engine trouble", "2026-10-11T04:00:00Z"))
    after_fail = panel(m.store, NOW)
    assert "L-C01-EVAC-G1" in after_fail["needs"]
    assert not any(a["resourceId"] == "S1" for a in after_fail["suggestion"]["assignments"])
    map_view = flood_map(m.store, NOW)
    assert next(t for t in map_view["teams"] if t["resourceId"] == "S1")["freeSeats"] == 0
    assert sum(s["coverage"]["heldJobs"] for s in map_view["segments"]) == 1
    assert claimed["allocationId"] in [a["allocationId"] for a in m.store.seed["allocations"]]


def test_team_asks_are_visible_retry_safe_and_never_claim_or_promise(c):
    view = c.get("/api/views/splitPanel?areaId=P-B").json()
    s = view["suggestion"]
    teams = sorted({a["teamId"] for a in s["assignments"]})
    assert teams
    before = copy.deepcopy(main.memory.store.seed)
    body = {"submissionId": "ASK-SUB", "areaId": "P-B", "suggestionId": s["suggestionId"], "teamIds": teams}
    r = c.post("/api/plans/ask", json=body)
    assert r.status_code == 200 and r.json()["ok"]
    assert c.post("/api/plans/ask", json=body).json() == r.json()
    for k in before:
        assert main.memory.store.seed[k] == before[k]
    assert len(main.memory.store.seed["teamAsks"]) == len(teams)
    for team in teams:
        asks = c.get(f"/api/views/teamMissions/{team}").json()["asks"]
        assert asks and all(a["teamId"] == team for a in asks)
        assert all(g["expectedRevision"] >= 1 for a in asks for g in a["groups"])
    for other in {"T-S", "T-R"} - set(teams):
        assert c.get(f"/api/views/teamMissions/{other}").json()["asks"] == []
    main.memory.write("S1-FAIL", lambda: main.memory.resource_unavailable("S1", "Engine failed", "2026-10-11T04:00:00Z"))
    stale = c.post("/api/plans/ask", json={**body, "submissionId": "STALE-ASK"}).json()
    assert stale["ok"] is False and stale["code"] == "VERSION_CONFLICT"
    assert len(main.memory.store.seed["teamAsks"]) == len(teams)


def test_replay_matches_only_explicit_catalogue_locations_in_all_areas():
    from api.rules.replay import process
    from data.surge import generate
    catalogue = MemoryStore().store.catalogue
    rows, truth = generate(catalogue)
    landmarks = {l["id"]: l for l in catalogue["landmarks"]}
    expected = {t["reportId"]: t["expectedSegment"] for t in truth}
    for r in rows:
        assert process(r, landmarks)["segmentId"] == expected[r["reportId"]]
    assert process({**rows[0], "text": "Water 0.8 m; no place given"}, landmarks)["segmentId"] is None


def test_phone_transcript_and_approved_report_can_supply_evidence(c):
    body = add_report()
    main.memory.store.seed["reports"][-1].update(channel="phone_transcript", status="approved")
    assert c.post("/api/water-observations", json={**body, "source": "phone_transcript"}).status_code == 200
    view = c.get("/api/views/floodMap").json()
    assert any(o["source"] == "phone_transcript" for s in view["segments"] for o in s["observations"])


def test_unknown_time_remains_unknown_and_future_or_rejected_evidence_is_refused(c):
    body = add_report()
    r = c.post("/api/water-observations", json={**body, "observedAt": None})
    assert r.status_code == 200 and main.memory.store.seed["waterObservations"][0]["observedAt"] is None
    future_quote = body["quote"].replace("03:20", "04:20")
    main.memory.store.seed["reports"][-1]["text"] = future_quote
    assert c.post("/api/water-observations", json={**body, "submissionId": "FUTURE", "quote": future_quote,
                                                 "observedAt": "2026-10-11T04:20:00Z"}).status_code == 409
    main.memory.store.seed["reports"][-1].update(text=body["quote"], status="rejected")
    assert c.post("/api/water-observations", json={**body, "submissionId": "REJECTED"}).status_code == 409
    assert len(main.memory.store.seed["waterObservations"]) == 1
