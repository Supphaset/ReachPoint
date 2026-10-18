"""Judging limits use clocks and fake storage, never paid model calls."""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from api.ai.usage import BudgetExceeded, Usage
from api.server.rooms import Rooms
from api.v2 import limits as L, routes as R, store as S


@pytest.mark.parametrize("method,path,cap,body", [
    ("POST", "/api/v2/chat/sessions", 20, {}),
    ("POST", "/api/v2/chat/sessions/s/turn", 20, {}),
    ("POST", "/api/v2/v/copilot", 8, {}),
    ("POST", "/api/v2/clock", 10, {"action": "reset"}),
    ("POST", "/api/anything", 120, {}),
    ("GET", "/api/v2/state", 600, {}),
])
def test_http_buckets(monkeypatch, method, path, cap, body):
    now = [0.0]
    monkeypatch.setattr(L, "limits", L.Limits(clock=lambda: now[0]))
    for _ in range(cap):
        assert L.http_limit(method, path, "ip", "room", body) == 0
    retry = L.http_limit(method, path, "ip", "room", body)
    assert retry > 0
    now[0] += retry
    assert L.http_limit(method, path, "ip", "room", body) == 0


def test_ip_limit_cannot_be_bypassed_by_rotating_rooms_or_sessions():
    for i in range(30):
        assert not L.http_limit("POST", f"/api/v2/chat/sessions/s{i}/turn", "ip", f"room{i}", {})
    assert L.http_limit("POST", "/api/v2/chat/sessions/new/turn", "ip", "new", {}) == 2


def test_room_creation_and_cleaning(monkeypatch):
    now = [0.0]
    limiter = L.Limits(clock=lambda: now[0])
    monkeypatch.setattr(L, "limits", limiter)
    for i in range(10):
        assert not L.http_limit("GET", "/api/v2/state", "ip", str(i), {}, creating=True)
    assert L.http_limit("GET", "/api/v2/state", "ip", "extra", {}, creating=True) == 6
    now[0] = 120
    assert not L.http_limit("GET", "/api/v2/state", "other", "new", {})
    assert all("ip" not in key for key in limiter.buckets)


@pytest.mark.parametrize("kind,cap", [("copilot", 60), ("voice", 10)])
def test_daily_ip_limits_roll_at_utc_midnight(kind, cap):
    wall = [86399.0]
    limiter = L.Limits(wall=lambda: wall[0])
    for _ in range(cap):
        assert limiter.day((kind, "ip"), cap) == 0
    assert limiter.day((kind, "ip"), cap) == 1
    wall[0] += 1
    assert limiter.day((kind, "ip"), cap) == 0


def test_voice_concurrency_and_release():
    limiter = L.Limits()
    assert limiter.voice("a")
    assert not limiter.voice("a")
    assert limiter.voice("b") and limiter.voice("c")
    assert not limiter.voice("d")
    limiter.release("b")
    assert limiter.voice("d")


def test_thread_safe_bucket():
    limiter = L.Limits(clock=lambda: 0)
    with ThreadPoolExecutor(max_workers=12) as pool:
        results = list(pool.map(lambda _: limiter.take([("shared", 30, 60)]), range(100)))
    assert results.count(0) == 30


def test_forwarded_identity():
    req = SimpleNamespace(headers={"x-forwarded-for": "2001:db8::1, 10.0.0.1", "fastly-client-ip": "192.0.2.5"},
                          client=SimpleNamespace(host="fallback"))
    assert L.client_ip(req) == "2001:db8::1"
    req.headers["x-forwarded-for"] = "bad, 192.0.2.5"
    assert L.client_ip(req) == "fallback"


def test_gemini_cap_resets_every_15_minutes_and_refunds_live(monkeypatch):
    monkeypatch.setenv("RP_GEMINI_CALLS_15MIN", "2")
    monkeypatch.setenv("RP_LIVE_MIN_15MIN", "5")
    now = [1_000_000.0]
    usage = Usage(clock=lambda: now[0])
    window = usage.reserve(minutes=5)
    with pytest.raises(BudgetExceeded):
        usage.reserve(minutes=5)
    usage.finish_live(window, 60)
    assert usage.status()["liveMinutes"] == 1
    usage.reserve()
    assert usage.status()["capped"]
    with pytest.raises(BudgetExceeded):
        usage.reserve()
    assert 0 < usage.status()["resetsInS"] <= 900
    now[0] += 900
    usage.reserve()
    assert usage.status()["calls"] == 1 and not usage.status()["capped"]


def test_budget_stops_network_and_readers_use_labelled_rules(monkeypatch):
    from api.ai import gemini, usage
    from api.v2 import ai, copilot
    monkeypatch.setenv("RP_GEMINI_CALLS_15MIN", "0")
    monkeypatch.setenv("REACHPOINT_AI", "on")
    monkeypatch.setattr(ai, "USE_AI", True)
    monkeypatch.setattr(gemini, "available", lambda: True)
    monkeypatch.setattr(gemini, "use_vertex", lambda: False)
    import httpx
    monkeypatch.setattr(httpx, "post", lambda *a, **kw: pytest.fail("Paid request escaped the cap"))
    assert ai.read("Water at my knees, two people").reader == "rules"
    monkeypatch.setattr(copilot, "rules_answer", lambda *a: ("No families waiting.", [], None))
    assert copilot.ask({}, "Where first?")["reader"] == "rules"
    assert usage.usage.status()["capped"]


def test_room_flush_happens_before_eviction_and_failure_keeps_room(monkeypatch):
    registry = Rooms(cap=1)
    old = registry.get("old")
    old.v2 = object()
    seen = []
    monkeypatch.setattr(S, "flush", lambda key, v: seen.append((key, registry.contains(key))) or False)
    with pytest.raises(HTTPException):
        registry.get("new")
    assert registry.contains("old")
    monkeypatch.setattr(S, "flush", lambda key, v: seen.append((key, registry.contains(key))) or True)
    registry.get("new")
    assert seen == [("old", True), ("old", True)]
    assert not registry.contains("old")


def test_active_room_cannot_be_evicted():
    registry = Rooms(cap=1)
    old = registry.acquire("old")
    with pytest.raises(HTTPException):
        registry.get("new")
    registry.release(old)
    registry.get("new")
    assert len(registry) == 1


def test_sessions_per_room(monkeypatch):
    v = R.V2Room()
    v._room_id = "sessions-test"
    monkeypatch.setattr(R, "room", lambda: v)
    for _ in range(200):
        R.new_chat("en")
    with pytest.raises(HTTPException) as err:
        R.new_chat("en")
    assert err.value.status_code == 429 and len(v.sessions) == 200


def test_headers_origins_429_body_and_retired_classic_routes(monkeypatch):
    import api.main as main
    from api.security import HEADERS, ORIGINS
    c = TestClient(main.app)
    for path in ("/api/v2/health", "/api/health", "/classic"):
        response = c.get(path)
        assert all(response.headers[k] == v for k, v in HEADERS.items())
    assert c.get("/api/v2/health", headers={"Origin": "https://evil.example"}).status_code == 403
    response = c.options("/api/v2/chat/sessions", headers={"Origin": ORIGINS[0], "Access-Control-Request-Method": "POST", "Access-Control-Request-Headers": "X-Demo-Room"})
    assert response.headers["access-control-allow-origin"] == ORIGINS[0]
    assert response.headers["x-frame-options"] == "DENY"
    monkeypatch.setattr(L.limits, "take", lambda rules: 7)
    response = c.post("/api/v2/chat/sessions", json={})
    assert response.status_code == 429 and response.json() == {"error": "rate_limited", "retryAfter": 7}
    assert response.headers["Retry-After"] == "7"
    monkeypatch.setattr(L.limits, "take", lambda rules: 0)
    assert c.post("/api/intake/text", json={"text": "synthetic"}).status_code == 404
    assert c.post("/api/v2/chat/sessions", json={}).status_code == 200


def test_body_and_identifier_limits_and_fresh_room():
    import api.main as main
    c = TestClient(main.app)
    assert c.post("/api/v2/chat/sessions/s/turn", json={"text": "x" * 601}).status_code == 422
    assert c.post("/api/v2/chat/sessions/s/turn", json={"text": "x" * 32769}).status_code == 413
    assert c.get("/api/v2/v/cases/bad!id").status_code == 422
    assert c.get("/api/v2/v/blocks?zone=bad!id").status_code == 422
    r = c.get("/api/v2/health", headers={"X-Demo-Room": "../../invalid"})
    assert r.headers["X-Demo-Room"] != "main"
    assert len(r.headers["X-Demo-Room"]) == 32


def test_websocket_origin_and_classic_voice_rejected():
    from starlette.websockets import WebSocketDisconnect
    import api.main as main
    c = TestClient(main.app)
    for path, headers in [("/api/v2/chat/sessions/s/live", {"Origin": "https://evil.example"}),
                          ("/api/v2/chat/sessions/s/live", {}), ("/api/call/sessions/s/live", {})]:
        with pytest.raises(WebSocketDisconnect) as exc:
            with c.websocket_connect(path, headers=headers):
                pytest.fail("Unexpected socket acceptance")
        assert exc.value.code == (1000 if path.startswith("/api/call/") else 1008)


def test_live_call_timeout_cancels_tasks_and_releases_slot(monkeypatch):
    from contextlib import asynccontextmanager
    import api.main as main
    from api.v2 import live
    from api.ai import usage
    from api.security import ORIGINS
    registry = Rooms()
    registry.current_id.set("live-test")
    monkeypatch.setattr(R, "_rooms_ref", registry)
    session = R.new_chat("en")
    monkeypatch.setenv("REACHPOINT_AI", "on")
    seen = []

    class Connection:
        async def send_realtime_input(self, **kwargs):
            pass

    @asynccontextmanager
    async def connect(**kwargs):
        yield Connection()

    async def wait(tasks, timeout, **kwargs):
        seen.append(timeout)
        return set(), tasks

    async def blocking(*args):
        await asyncio.Event().wait()

    monkeypatch.setattr(live, "_client", lambda: SimpleNamespace(aio=SimpleNamespace(live=SimpleNamespace(connect=connect))))
    monkeypatch.setattr(live, "_from_browser", blocking)
    monkeypatch.setattr(live, "_to_browser", blocking)
    monkeypatch.setattr(live.asyncio, "wait", wait)
    with TestClient(main.app).websocket_connect(f"/api/v2/chat/sessions/{session['id']}/live?room=live-test", headers={"Origin": ORIGINS[0]}) as ws:
        assert ws.receive_json()["type"] == "ready"
        assert "five minutes" in ws.receive_json()["message"]
    assert 299 <= seen[0] <= 300
    assert not L.limits.calls
    assert registry.get("live-test").active == 0
    assert usage.usage.status()["calls"] == 1


def test_flush_cancels_pending_timer_and_saves_latest(monkeypatch):
    from test_v2_store import FakeFirestore
    db = FakeFirestore()
    monkeypatch.setenv("RP_FIRESTORE", "1")
    monkeypatch.setattr(S, "_client", db)
    monkeypatch.setattr(S, "_pending", {})
    v = R.V2Room()
    v._room_id = "flush"
    monkeypatch.setattr(S, "DEBOUNCE_S", 60)
    S.schedule(v)
    v.seq = 123
    assert S.flush("flush", v)
    assert "flush" not in S._pending
    assert S.load("flush")["seq"] == 123


def test_csp_edge_mirror_and_binary_cache_unchanged():
    import json
    from pathlib import Path
    import api.main as main
    from api.security import CSP, HEADERS
    edge = json.loads(Path("firebase.json").read_text())["hosting"]["headers"][0]["headers"]
    assert dict((h["key"], h["value"]) for h in edge) == {"Cache-Control": "no-store", **HEADERS}
    assert "frame-ancestors 'none'" in CSP
    assert "'unsafe-inline'" not in CSP.split("script-src", 1)[1].split(";", 1)[0]
    assert TestClient(main.app).get("/api/v2/sim.bin").headers["cache-control"] == "public, max-age=86400"


def test_model_body_schemas_bound_strings_and_collections():
    import api.main as main
    from pydantic import BaseModel
    from api.v2 import routes

    for module in (main, routes):
        classes = [cls for cls in vars(module).values() if isinstance(cls, type) and issubclass(cls, BaseModel) and cls is not BaseModel]
        for cls in classes:
            schema = cls.model_json_schema()

            def check(node):
                if isinstance(node, dict):
                    if node.get("type") == "string" and "enum" not in node and "const" not in node and "format" not in node:
                        assert "maxLength" in node, (cls.__name__, node)
                    if node.get("type") == "array":
                        assert "maxItems" in node, (cls.__name__, node)
                    for value in node.values():
                        check(value)
                elif isinstance(node, list):
                    for value in node:
                        check(value)
            check(schema)


@pytest.mark.parametrize("slots", [{"192.0.2.1": 0}, {"a": 0, "b": 0, "c": 0}])
def test_live_admission_limit_never_opens_model(monkeypatch, slots):
    import api.main as main
    from api.security import ORIGINS
    from api.v2 import live
    L.limits.calls.update(slots)
    monkeypatch.setattr(live, "_client", lambda: pytest.fail("Busy call reached Gemini"))
    with TestClient(main.app).websocket_connect("/api/v2/chat/sessions/s/live", headers={"Origin": ORIGINS[0], "X-Forwarded-For": "192.0.2.1"}) as ws:
        message = ws.receive_json()
        assert message["error"] == "rate_limited" and message["retryAfter"] == 300


def test_voice_worker_pins_room_until_its_write_finishes(monkeypatch):
    import threading
    from api.v2 import live
    registry = Rooms(cap=1)
    monkeypatch.setattr(R, "_rooms_ref", registry)
    started, finish = threading.Event(), threading.Event()

    def turn(*args):
        started.set()
        finish.wait(5)
        return {"ok": True}

    monkeypatch.setattr(R, "turn", turn)
    with ThreadPoolExecutor(max_workers=1) as pool:
        task = pool.submit(live._turn_in_room, "worker", "s", "synthetic")
        try:
            assert started.wait(5)
            with pytest.raises(HTTPException):
                registry.get("another")
        finally:
            finish.set()
        assert task.result() == {"ok": True}
    registry.get("another")


def test_board_cache_has_global_and_per_room_bounds(monkeypatch):
    from collections import OrderedDict
    monkeypatch.setattr(R, "_board_caches", OrderedDict())
    monkeypatch.setattr(R.B, "state", lambda *a: {"synthetic": True})
    rooms = [R.V2Room() for _ in range(9)]
    for room in rooms:
        R._state(room)
    assert len(R._board_caches) == 8 and not rooms[0]._cache
    for hour in range(10):
        rooms[-1].now_h = hour
        R._state(rooms[-1])
        assert len(rooms[-1]._cache) <= 2


@pytest.mark.parametrize("event", [{"bytes": b"x" * 64001}, {"text": "x" * 4097}])
def test_live_frame_size_limits(event):
    from api.v2.live import _from_browser
    closed = []

    class WS:
        async def receive(self):
            return {"type": "websocket.receive", **event}

        async def close(self, code):
            closed.append(code)

    asyncio.run(_from_browser(WS(), None))
    assert closed == [1009]


def test_gemini_output_ceiling(monkeypatch):
    import httpx
    from api.ai import gemini
    seen = []
    monkeypatch.setattr(httpx, "post", lambda *a, **kw: seen.append(kw["json"]))
    gemini.post("synthetic", {}, 1, key="test-only")
    assert seen[0]["generationConfig"]["maxOutputTokens"] == 2048
