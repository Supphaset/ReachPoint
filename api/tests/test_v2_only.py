"""Retiring classic must leave the judging API and visitor isolation intact."""

import sys

import pytest
from fastapi.testclient import TestClient

from api.main import app, rooms


@pytest.mark.parametrize("path", [
    "/api/views/reviewQueue", "/api/views/teamMissions/T-S", "/api/status/old-token",
    "/api/views/floodMap", "/api/call/config",
])
def test_classic_reads_are_gone(path):
    assert TestClient(app).get(path).status_code == 404


@pytest.mark.parametrize("path", ["/api/intake/text", "/api/call/sessions", "/api/demo/reset", "/api/plans/ask"])
def test_classic_writes_are_gone(path):
    assert TestClient(app).post(path, json={}).status_code == 404


def test_startup_and_new_rooms_do_not_load_classic_state():
    room = rooms.get("v2-only-startup")
    assert not hasattr(room, "memory") and not hasattr(room, "flood_replay")
    assert not any(name.startswith(("api.intake", "api.views", "api.rules")) for name in sys.modules)
    paths = set(app.openapi()["paths"])
    assert all(path.startswith("/api/v2/") or path in ("/api/health", "/api/config") for path in paths)


def test_shared_health_and_map_configuration_still_work():
    c = TestClient(app)
    assert c.get("/api/health").json()["ok"]
    assert c.get("/api/v2/health").json()["ok"]
    assert set(c.get("/api/config").json()) == {"mapsKey"}
