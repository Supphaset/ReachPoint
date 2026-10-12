"""ReachPoint starter server (FastAPI). Routes: contract/api.md.

    uvicorn api.main:app --reload            # local, from the repo root
    VITE_DATA=api npm --prefix web run build # then the same server serves the app at /

It serves the built web app and the API from one Cloud Run service. Records live in memory, starting from
`contract/seed/demo.hy-2025-11.json`, so a restart resets the demo; the friend's version swaps `MemoryStore` for
Firestore and keeps the routes, rules and views. No secrets here: Cloud Run's own identity calls Google APIs.
"""

from __future__ import annotations

import json
import os
from datetime import timedelta
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from api.intake.extract import extract
from api.server.memory import Clock, MemoryStore, NotFound, Refused
from api.views.briefing import area_briefing
from api.views.desk import rain_view, rising_water_view, zone_order_view
from api.views.resident import resident_status
from api.views.review import review_queue
from api.views.team import team_missions

ROOT = Path(__file__).resolve().parents[1]
WEB = Path(os.environ.get("REACHPOINT_WEB_DIST", ROOT / "web" / "dist"))
DAY_START, STEPS = "2026-10-11T03:00:00Z", 15  # the replayed demo day: 10:00–17:00 Bangkok, every 30 min

app = FastAPI(title="ReachPoint", version="0.1", docs_url="/api/docs", openapi_url="/api/openapi.json")
memory = MemoryStore(clock=Clock(os.environ.get("REACHPOINT_CLOCK", "demo")))


@app.exception_handler(Refused)
async def refused(_: Request, e: Refused):
    return JSONResponse(status_code=409, content={"code": e.code, "message": e.message, "detail": e.detail})


@app.exception_handler(NotFound)
async def not_found(_: Request, e: NotFound):
    return JSONResponse(status_code=404, content={"code": "NOT_FOUND", "message": f"No such record: {e.args[0]}"})


def _now():
    return memory.clock.iso()


def _replay_times():
    from datetime import datetime
    start = datetime.fromisoformat(DAY_START.replace("Z", "+00:00"))
    return [start + timedelta(minutes=30 * i) for i in range(STEPS)]


# --- views ---

@app.get("/api/health")
def health():
    return {"ok": True, "store": "memory", "seedVersion": memory.store.seed.get("version"), "clock": memory.clock.mode, "now": _now()}


@app.get("/api/views/areaBriefing/{area_id}")
def view_briefing(area_id: str):
    if area_id not in {a["id"] for a in memory.store.catalogue["areas"]}:
        raise NotFound(area_id)
    with memory.lock:
        return area_briefing(memory.store, area_id, _now())


@app.get("/api/views/teamMissions/{team_id}")
def view_team(team_id: str):
    with memory.lock:
        if memory.store.team(team_id) is None:
            raise NotFound(team_id)
        return team_missions(memory.store, team_id, _now())


@app.get("/api/views/zoneOrder")
def view_zone_order():
    with memory.lock:
        return zone_order_view(memory.store, memory.clock.now(), _now())


@app.get("/api/views/rain/{area_id}")
def view_rain(area_id: str):
    with memory.lock:
        return [rain_view(memory.store, area_id, t, _now()) for t in _replay_times()]


@app.get("/api/views/risingWater/{area_id}")
def view_rising(area_id: str):
    if area_id != "P-B":
        raise NotFound(area_id)
    with memory.lock:
        now = _now()
        return [rising_water_view(memory.store, area_id, t, now, now) for t in _replay_times()]


@app.get("/api/views/splitPanel")
def view_split():
    return json.loads((ROOT / "contract" / "fixtures" / "splitPanel.cp3.json").read_text())


# --- team actions (C6) ---

class Write(BaseModel):
    submissionId: str | None = None


class Claim(Write):
    teamId: str
    groupIds: list[str] = Field(min_length=1)
    expectedRevision: int


class Window(Write):
    start: str
    end: str


class Progress(Write):
    state: str


class Close(Write):
    outcome: str


class HandBack(Write):
    reason: str


class Status(Write):
    status: str
    reason: str | None = None
    backAbout: str | None = None


class Reconfirm(Write):
    teamId: str | None = None


class UrgentFlag(Write):
    reason: str
    confirmedNow: bool = False


class AskTeams(Write):
    suggestionId: str
    teamIds: list[str]


@app.post("/api/listings/{listing_id}/claim")
def claim(listing_id: str, b: Claim):
    r = memory.write(b.submissionId, lambda: memory.claim(listing_id, b.teamId, b.groupIds, b.expectedRevision))
    with memory.lock:
        job = next(j for j in team_missions(memory.store, b.teamId, _now())["jobs"] if j["allocationId"] == r["value"]["allocationId"])
    return {"ok": True, "value": job}


@app.post("/api/allocations/{allocation_id}/window")
def window(allocation_id: str, b: Window):
    return memory.write(b.submissionId, lambda: memory.set_window(allocation_id, b.start, b.end))


@app.post("/api/allocations/{allocation_id}/progress")
def progress(allocation_id: str, b: Progress):
    return memory.write(b.submissionId, lambda: memory.progress(allocation_id, b.state))


@app.post("/api/allocations/{allocation_id}/close")
def close(allocation_id: str, b: Close):
    return memory.write(b.submissionId, lambda: memory.close(allocation_id, b.outcome))


@app.post("/api/allocations/{allocation_id}/hand-back")
def hand_back(allocation_id: str, b: HandBack):
    return memory.write(b.submissionId, lambda: memory.hand_back(allocation_id, b.reason))


@app.post("/api/teams/{team_id}/status")
def team_status(team_id: str, b: Status):
    return memory.write(b.submissionId, lambda: memory.team_status(team_id, b.status, b.reason, b.backAbout))


@app.post("/api/listings/{listing_id}/reconfirm")
def reconfirm(listing_id: str, b: Reconfirm):
    return memory.write(b.submissionId, lambda: memory.reconfirm(listing_id, b.teamId))


# --- desk actions ---

@app.post("/api/listings/{listing_id}/urgent-flag")
def urgent_flag(listing_id: str, b: UrgentFlag):
    return memory.write(b.submissionId, lambda: memory.urgent_flag(listing_id, b.reason, b.confirmedNow))


@app.post("/api/ask-teams")
def ask_teams(b: AskTeams):
    return memory.ask_teams(b.suggestionId, b.teamIds)


# --- intake, desk review, family status (T3, D6) ---

USE_AI = os.environ.get("REACHPOINT_AI", "on") != "off"


class Intake(Write):
    text: str = Field(min_length=1, max_length=2000)
    channel: str = "text"


class Approve(Write):
    segmentId: str
    people: dict[str, int]
    needs: list[str]
    waterBand: str | None = None
    urgentReason: str | None = None
    deskNote: str | None = None


class Reject(Write):
    reason: str


@app.post("/api/intake/text")
def intake_text(b: Intake):
    """A request typed by the caller or by a volunteer taking the call. The AI reads it outside the lock (it can take
    seconds); the report is then stored as a proposal for the desk."""
    if b.submissionId and b.submissionId in memory.done:
        return memory.done[b.submissionId]
    proposal = extract(b.text, use_model=USE_AI)
    r = memory.write(b.submissionId, lambda: memory.submit_report(b.text, b.channel, proposal))
    v = r["value"]
    return {"ok": True, "value": {**v, "statusUrl": f"/status/{v['statusToken']}", "aiSource": proposal["source"]}}


@app.get("/api/views/reviewQueue")
def view_review():
    with memory.lock:
        return {**review_queue(memory.store), "generatedAt": _now()}


@app.post("/api/reports/{report_id}/approve")
def approve(report_id: str, b: Approve):
    return memory.write(b.submissionId, lambda: memory.approve_report(report_id, b.segmentId, b.people, b.needs, b.waterBand, b.urgentReason, b.deskNote))


@app.post("/api/reports/{report_id}/reject")
def reject(report_id: str, b: Reject):
    return memory.write(b.submissionId, lambda: memory.reject_report(report_id, b.reason))


@app.get("/api/status/{token}")
def status(token: str):
    with memory.lock:
        v = resident_status(memory.store, token, _now())
    if v is None:
        raise NotFound("status link")
    return v


@app.post("/api/demo/reset")
def reset():
    """Start the demo again from the seed (coordinator only once sign-in exists)."""
    global memory
    memory = MemoryStore(clock=Clock(os.environ.get("REACHPOINT_CLOCK", "demo")))
    return {"ok": True, "now": _now()}


# --- the web app ---

if (WEB / "assets").is_dir():
    app.mount("/assets", StaticFiles(directory=WEB / "assets"), name="assets")


@app.get("/{path:path}", include_in_schema=False)
def spa(path: str):
    if path.startswith("api/"):
        raise HTTPException(404)
    f = WEB / path
    if path and f.is_file() and WEB in f.resolve().parents:
        return FileResponse(f)
    index = WEB / "index.html"
    if not index.is_file():
        return JSONResponse(status_code=503, content={"message": "Web app not built: run VITE_DATA=api npm --prefix web run build"})
    return FileResponse(index)
