"""ReachPoint starter server (FastAPI). Routes: contract/api.md.

    uvicorn api.main:app --reload            # local, from the repo root
    VITE_DATA=api npm --prefix web run build # then the same server serves the app at /

It serves the built web app and the API from one service. Records start from
`contract/seed/demo.hy-2025-11.json`. Set REACHPOINT_DB_PATH for local SQLite persistence;
without it, the demo resets on restart. Firestore remains the planned shared store.
"""

from __future__ import annotations

import json
import os
from datetime import timedelta
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from typing import Literal

from pydantic import BaseModel, Field, model_validator

import threading
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor

from api.ai import briefing_text, triage
from api.intake.extract import extract
from api.intake import conversation
from api.intake.live_voice import router as live_voice_router
from api.location.resolve import resolve as resolve_location
from api.server.memory import Clock, MemoryStore, NotFound, Refused
from api.server.sqlite_store import HELP_REQUEST_FIELDS, SQLiteMemoryStore, SQLiteState
from api.views.briefing import area_briefing
from api.views.desk import rain_view, rising_water_view, zone_order_view
from api.views.resident import resident_status
from api.views.review import review_queue
from api.views.team import team_missions
from api.contract.flood import ReplayReset, ReplayStep, WaterInput
from api.server.flood_replay import FloodReplay
from api.views.flood import flood_map
from api.views.planning import panel as live_panel

ROOT = Path(__file__).resolve().parents[1]
WEB = Path(os.environ.get("REACHPOINT_WEB_DIST", ROOT / "web" / "dist"))
DAY_START, STEPS = "2026-10-11T03:00:00Z", 15  # the replayed demo day: 10:00–17:00 Bangkok, every 30 min

app = FastAPI(title="ReachPoint", version="0.1", docs_url="/api/docs", openapi_url="/api/openapi.json")
app.include_router(live_voice_router)
database = SQLiteState(os.environ["REACHPOINT_DB_PATH"]) if os.environ.get("REACHPOINT_DB_PATH") else None
conversation.configure_storage(database)


def _new_memory() -> MemoryStore:
    clock = Clock(os.environ.get("REACHPOINT_CLOCK", "demo"))
    return SQLiteMemoryStore(database, clock) if database else MemoryStore(clock=clock)


def _new_replay(store: MemoryStore) -> FloodReplay:
    return FloodReplay(store.store.catalogue, saved=database.get("replay") if database else None,
                       persist=(lambda state: database.put("replay", state)) if database else None)


memory = _new_memory()
flood_replay = _new_replay(memory)
USE_AI = os.environ.get("REACHPOINT_AI", "on") != "off"  # off: no Gemini calls (tests, offline demo)


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
    return {"ok": True, "store": "sqlite" if database else "memory", "seedVersion": memory.store.seed.get("version"),
            "clock": memory.clock.mode, "now": _now()}


# Zone briefing text (C8): written in the background, once per set of facts, then kept. A view never waits for it.
BRIEFINGS: dict[str, dict] = {}
_pending: set[str] = set()
_brief_lock = threading.Lock()
_writer = ThreadPoolExecutor(max_workers=1)
_triager = ThreadPoolExecutor(max_workers=1)  # triage never waits behind briefing writes


def _write_briefing(key: str, facts: dict) -> None:
    try:
        result = briefing_text.write(facts)
    except Exception as e:  # never let a briefing break the view
        result = {"state": "unavailable", "text": None, "reason": type(e).__name__}
    with _brief_lock:
        BRIEFINGS[key] = result
        _pending.discard(key)
    time.sleep(1.0)  # stay well under the free tier's requests per minute


def _with_briefings(view: dict) -> dict:
    for z in view["zones"]:
        facts = briefing_text.zone_facts(z)
        key = briefing_text.facts_key(facts)
        with _brief_lock:
            done = BRIEFINGS.get(key)
            if done is None and USE_AI and key not in _pending:
                _pending.add(key)
                _writer.submit(_write_briefing, key, facts)
        if done is not None:
            z["briefing"] = done
        else:
            z["briefing"] = {"state": "writing" if USE_AI else "unavailable", "text": None,
                             "reason": None if USE_AI else "ai_off"}
    return view


@app.get("/api/views/areaBriefing/{area_id}")
def view_briefing(area_id: str):
    if area_id not in {a["id"] for a in memory.store.catalogue["areas"]}:
        raise NotFound(area_id)
    with memory.lock:
        view = area_briefing(memory.store, area_id, _now())
    return _with_briefings(view)


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
def view_split(areaId: str | None = None):
    with memory.lock:
        return live_panel(memory.store, _now(), areaId)


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

class ResourceFailure(Write):
    submissionId: str = Field(min_length=1)
    reason: str = Field(min_length=1, max_length=200)
    nextStatusUpdate: str


@app.post("/api/resources/{resource_id}/unavailable")
def resource_unavailable(resource_id: str, b: ResourceFailure):
    return memory.write(b.submissionId, lambda: memory.resource_unavailable(resource_id, b.reason, b.nextStatusUpdate))


@app.post("/api/listings/{listing_id}/urgent-flag")
def urgent_flag(listing_id: str, b: UrgentFlag):
    return memory.write(b.submissionId, lambda: memory.urgent_flag(listing_id, b.reason, b.confirmedNow))


@app.post("/api/ask-teams")
def ask_teams(b: AskTeams):
    return memory.ask_teams(b.suggestionId, b.teamIds)


# --- intake, desk review, family status (T3, D6) ---


class LocationInput(BaseModel):
    """A pin (GPS or map tap) or an address; see contract/api.md "Locating a request" (D25)."""
    kind: Literal["pin", "address"]
    lat: float | None = Field(default=None, ge=-90, le=90)
    lon: float | None = Field(default=None, ge=-180, le=180)
    method: Literal["gps", "map", "pinpoint"] | None = None
    accuracyM: float | None = Field(default=None, ge=0, le=100_000)
    text: str | None = Field(default=None, max_length=300)

    @model_validator(mode="after")
    def _shape(self):
        if self.kind == "pin" and (self.lat is None or self.lon is None):
            raise ValueError("A pin needs lat and lon")
        if self.kind == "address" and not (self.text or "").strip():
            raise ValueError("An address needs text")
        return self


class Intake(Write):
    text: str = Field(min_length=1, max_length=2000)
    channel: str = "text"
    segmentId: str | None = None  # a field report from a team in its segment (D20)
    teamId: str | None = None
    location: LocationInput | None = None


class CallTurn(BaseModel):
    text: str = Field(min_length=1, max_length=conversation.MAX_TURN_CHARS)
    turnId: str = Field(min_length=1, max_length=100)


class CallLocation(BaseModel):
    query: str
    action: Literal["select", "reject"]
    locationId: str | None = None


class CallConfirm(BaseModel):
    submissionId: str = Field(min_length=1, max_length=100)
    expectedRevision: int = Field(ge=0)


class Locate(BaseModel):
    location: LocationInput


class Approve(Write):
    segmentId: str
    people: dict[str, int]
    needs: list[str]
    waterBand: str | None = None
    urgentReason: str | None = None
    deskNote: str | None = None
    location: LocationInput | None = None  # the coordinator's correction, e.g. an address heard on a phone call


class Reject(Write):
    reason: str


@app.post("/api/intake/text")
def intake_text(b: Intake):
    """A request typed by the caller or by a volunteer taking the call. The AI reads it outside the lock (it can take
    seconds); the report is then stored as a proposal for the desk."""
    if b.submissionId and b.submissionId in memory.done:
        return memory.done[b.submissionId]
    proposal = extract(b.text, use_model=USE_AI)
    channel = "field" if b.segmentId else b.channel
    location = resolve_location(b.location.model_dump(exclude_none=True)) if b.location else None  # outside the lock (Pinpoint)
    r = memory.write(b.submissionId, lambda: memory.submit_report(b.text, channel, proposal, b.segmentId, b.teamId, location))
    v = r["value"]
    _triager.submit(_run_triage)  # the triage agent looks at the new request in the background
    return {"ok": True, "value": {**v, "statusUrl": f"/status/{v['statusToken']}", "aiSource": proposal["source"]}}


@app.get("/api/call/config")
def call_config():
    available = USE_AI and conversation.configured()
    return {"chat": available, "voice": available and os.environ.get("REACHPOINT_VOICE", "off") == "on"}


@app.post("/api/call/sessions")
def start_call():
    return conversation.create().snapshot()


@app.get("/api/call/sessions/{session_id}")
def read_call(session_id: str):
    return conversation.get(session_id).snapshot()


@app.post("/api/call/sessions/{session_id}/turn")
async def call_turn(session_id: str, b: CallTurn):
    if not USE_AI:
        raise HTTPException(503, "Conversation mode is disabled on this server.")
    return await conversation.turn(conversation.get(session_id), b.text, b.turnId)


@app.post("/api/call/sessions/{session_id}/location")
async def call_location(session_id: str, b: CallLocation):
    return await conversation.choose_location(conversation.get(session_id), b.query, b.action, b.locationId)


def _help_request_row(session: conversation.Conversation, report_id: str | None = None) -> dict:
    fields = set(HELP_REQUEST_FIELDS) - {"report_id", "channel"}
    return {"report_id": report_id, "channel": session.channel, **session.case.model_dump(include=fields)}


async def submit_call_session(session: conversation.Conversation, _submission_id: str,
                              expected_revision: int | None = None) -> dict:
    async with session.lock:
        if session.sent:
            if database:
                database.put_help_request(_help_request_row(session, session.sent["reportId"]))
            return session.snapshot()
        call_key = f"CALL-{session.id}"
        with memory.lock:
            previous = memory.done.get(call_key)
            saved_report = (next((r for r in memory.store.seed.get("reports", [])
                                  if r["reportId"] == previous["value"]["reportId"]), None)
                            if previous else None)
        if previous:
            value = previous["value"]
            if database:
                database.put_help_request(_help_request_row(session, value["reportId"]))
            session.sent = {**value, "statusUrl": f"/status/{value['statusToken']}",
                            "aiSource": saved_report.get("proposal", {}).get("source", "unknown") if saved_report else "unknown"}
            try:
                conversation.save(session)
            except Exception:
                session.sent = None
                raise
            return session.snapshot()
        if expected_revision is not None and expected_revision != session.revision:
            raise HTTPException(409, "The summary changed. Review the latest details before confirming.")
        text, location_input = conversation.submission(session)
        if len(text) > conversation.MAX_REPORT_CHARS:
            raise HTTPException(409, "Conversation too long. Please use the text form.")
        proposal = await asyncio.to_thread(extract, text, USE_AI)
        location = await asyncio.to_thread(resolve_location, location_input) if location_input else None
        # One report per session even if the browser retries with a different submissionId after a crash.
        def submit() -> dict:
            return memory.submit_report(text, session.channel, proposal, location=location)
        result = (memory.write(call_key, submit, help_request=_help_request_row(session))
                  if isinstance(memory, SQLiteMemoryStore) else memory.write(call_key, submit))
        value = result["value"]
        session.sent = {**value, "statusUrl": f"/status/{value['statusToken']}", "aiSource": proposal["source"]}
        try:
            conversation.save(session)
        except Exception:
            session.sent = None
            raise
        _triager.submit(_run_triage)
        return session.snapshot()


@app.post("/api/call/sessions/{session_id}/confirm")
async def confirm_call(session_id: str, b: CallConfirm):
    return await submit_call_session(conversation.get(session_id), b.submissionId, b.expectedRevision)


_triage_lock = threading.Lock()
_triage_again = threading.Event()


def _run_triage() -> None:
    """One pass at a time; a request that arrives during a pass triggers one more pass after it."""
    if not _triage_lock.acquire(blocking=False):
        _triage_again.set()
        return
    try:
        while True:
            _triage_again.clear()
            with memory.lock:
                snapshot = memory.store.__class__(json.loads(json.dumps(memory.store.seed)), memory.store.catalogue,
                                                  memory.store.exposure, memory.store.register)
                now = _now()
            result = triage.run_agent(snapshot, now) if USE_AI else triage.rule_proposals(snapshot, now)
            memory.write(None, lambda: memory.store.seed.__setitem__("triage", {**result, "at": now}))
            if not _triage_again.is_set():
                break
    finally:
        _triage_lock.release()


@app.get("/api/views/reviewQueue")
def view_review():
    with memory.lock:
        return {**review_queue(memory.store), "generatedAt": _now()}


@app.post("/api/locate")
def locate(b: Locate):
    """Read-only preview of where a pin or address lands (D25). Writes nothing."""
    return {"ok": True, "value": resolve_location(b.location.model_dump(exclude_none=True))}


@app.post("/api/reports/{report_id}/approve")
def approve(report_id: str, b: Approve):
    location = resolve_location(b.location.model_dump(exclude_none=True)) if b.location else None  # outside the lock
    return memory.write(b.submissionId, lambda: memory.approve_report(report_id, b.segmentId, b.people, b.needs, b.waterBand,
                                                                        b.urgentReason, b.deskNote, location))


@app.post("/api/reports/{report_id}/reject")
def reject(report_id: str, b: Reject):
    return memory.write(b.submissionId, lambda: memory.reject_report(report_id, b.reason))


class LinkReport(Write):
    caseId: str


@app.post("/api/reports/{report_id}/link")
def link_report(report_id: str, b: LinkReport):
    return memory.write(b.submissionId, lambda: memory.link_report(report_id, b.caseId))


@app.post("/api/reports/{report_id}/not-same")
def not_same(report_id: str, b: LinkReport):
    return memory.write(b.submissionId, lambda: memory.not_same(report_id, b.caseId))


@app.get("/api/status/{token}")
def status(token: str):
    with memory.lock:
        v = resident_status(memory.store, token, _now())
    if v is None:
        raise NotFound("status link")
    return v


class Publish(Write):
    zoneId: str
    reasons: list[str] = []


class Dismiss(Write):
    reason: str


class TakeSegment(Write):
    teamId: str


class MarkSegment(Write):
    state: str
    householdsFound: int | None = None
    pickupsNeeded: int | None = None
    reason: str | None = None


@app.post("/api/zone-missions")
def publish_mission(b: Publish):
    return memory.write(b.submissionId, lambda: memory.publish_zone_mission(b.zoneId, b.reasons))


@app.post("/api/suggested-checks/{zone_id}/dismiss")
def dismiss_check(zone_id: str, b: Dismiss):
    return memory.write(b.submissionId, lambda: memory.dismiss_check(zone_id, b.reason))


@app.post("/api/segments/{segment_id}/take")
def take_segment(segment_id: str, b: TakeSegment):
    return memory.write(b.submissionId, lambda: memory.take_segment(segment_id, b.teamId))


@app.post("/api/segment-claims/{claim_id}/mark")
def mark_segment(claim_id: str, b: MarkSegment):
    return memory.write(b.submissionId, lambda: memory.mark_segment(claim_id, b.state, b.householdsFound, b.pickupsNeeded, b.reason))


@app.post("/api/demo/reset")
def reset():
    """Start the demo again from the seed (coordinator only once sign-in exists)."""
    global memory, flood_replay
    if database:
        database.clear()
    conversation.clear_cache()
    memory = _new_memory()
    flood_replay = _new_replay(memory)  # the 1,200-report replay starts again too
    return {"ok": True, "now": _now()}


# --- user-owned map and isolated replay ---

@app.get("/api/views/floodMap")
def view_flood_map(source: str = "operations"):
    if source not in ("operations", "replay"):
        raise HTTPException(status_code=422, detail="Unknown map source")
    replay = flood_replay.snapshot() if source == "replay" else None
    with memory.lock:
        return flood_map(memory.store, _now(), replay)


@app.post("/api/demo/flood-replay/step")
def replay_step(b: ReplayStep):
    return flood_replay.write(b.submissionId, b.expectedCursor, b.expectedRevision, b.count)


@app.post("/api/demo/flood-replay/reset")
def replay_reset(b: ReplayReset):
    return flood_replay.write(b.submissionId, b.expectedCursor, b.expectedRevision)


@app.post("/api/water-observations")
def water_observation(b: WaterInput):
    from api.intake.extract import quoted
    from api.rules.water import timestamp

    def apply():
        report = next((r for r in memory.store.seed.get("reports", []) if r["reportId"] == b.reportId), None)
        if report is None:
            raise HTTPException(404, detail="Unknown intake report")
        if report.get("status") == "rejected":
            raise Refused("INVALID", "Rejected intake cannot supply current water evidence")
        if b.segmentId not in memory.store.landmarks or b.siteId != b.segmentId:
            raise Refused("INVALID", "Use the reported segment landmark; exact household sites are not shared")
        if b.segmentId not in b.quote:
            raise Refused("INVALID", "Location must be explicitly present in the report")
        if b.source != report["channel"]:
            raise Refused("INVALID", "Observation source must match the intake channel")
        if b.evidenceRef and b.evidenceRef != b.reportId and b.evidenceRef not in report["text"]:
            raise Refused("INVALID", "Source reference must be present in the report")
        if not quoted(report["text"], b.quote):
            raise Refused("INVALID", "Observation needs words from the original report")
        if b.depthM is not None:
            import re
            measurements = re.findall(r"(\d+(?:\.\d+)?)\s*(?:m\b|metres?\b|meters?\b|เมตร)", b.quote)
            if not any(abs(float(x) - b.depthM) < 0.001 for x in measurements):
                raise Refused("INVALID", "Numeric depth needs a metre measurement in the quoted words")
        references = {"street_ground": ("street ground", "พื้นถนน"), "indoor_floor": ("indoor floor", "พื้นบ้าน"),
                      "upper_floor": ("upper floor", "ชั้นสอง")}
        if b.reference != "unknown" and not any(word in b.quote.lower() for word in references[b.reference]):
            raise Refused("INVALID", "Measurement reference must be present in the quoted words")
        if b.observedAt and b.observedAt.isoformat().replace("+00:00", "Z") not in b.quote:
            raise Refused("INVALID", "Explicit observation timestamp must be present in the quoted words; otherwise leave it unknown")
        if b.trend != "unknown" and not any(word in b.quote.lower() for word in {
                "rising": ("rising", "สูงขึ้น"), "steady": ("steady", "คงที่"), "falling": ("falling", "ลดลง")}[b.trend]):
            raise Refused("INVALID", "Trend must be supported by the quoted words")
        if b.band:
            from api.intake.extract import standin_extract
            if (standin_extract(b.quote).get("water") or {}).get("band") != b.band:
                raise Refused("INVALID", "The water band must be supported by the quoted words")
        row = b.model_dump(mode="json", exclude={"submissionId"})
        row["evidenceRef"] = b.evidenceRef or b.reportId
        row.update(observationId="W-" + b.submissionId, receivedAt=_now(), review="ai_read")
        if row["observedAt"] and timestamp(row["observedAt"]) > memory.clock.now():
            raise Refused("INVALID", "Observation time is in the future")
        memory.store.seed.setdefault("waterObservations", []).append(row)
        return {"observationId": row["observationId"], "review": "ai_read"}

    return memory.write(b.submissionId, apply)


class PlanAsk(BaseModel):
    submissionId: str = Field(min_length=1)
    suggestionId: str
    teamIds: list[str] = Field(min_length=1)
    areaId: str | None = None


@app.post("/api/plans/ask")
def plan_ask(b: PlanAsk):
    def apply():
        current = live_panel(memory.store, _now(), b.areaId)
        s = current["suggestion"]
        if b.suggestionId != s["suggestionId"]:
            return {"ok": False, "code": "VERSION_CONFLICT", "message": "Needs or resources changed",
                    "detail": {"why": "Refresh the current whole-family plan", "current": s}}
        allowed = {a["teamId"] for a in s["assignments"]}
        if not s["solver"]["optimal"] or len(set(b.teamIds)) != len(b.teamIds) or not set(b.teamIds) <= allowed:
            raise Refused("INVALID", "Ask only teams in the current optimal plan")
        asks = []
        for team in b.teamIds:
            links = [current["groupLinks"][a["listingId"]] for a in s["assignments"] if a["teamId"] == team]
            ask = {"askId": f"ASK-{b.submissionId}-{team}", "teamId": team, "suggestionId": s["suggestionId"],
                   "listingIds": sorted({l["listingId"] for l in links}), "groups": links, "askedAt": _now()}
            memory.store.seed.setdefault("teamAsks", []).append(ask)
            asks.append(ask)
        return {"ok": True, "askedAt": _now(), "asks": asks, "note": "Teams still take whole groups; no assignment or arrival promise was made"}

    # Atomic retry-safe wrapper; flatten its value to the split panel's AskResult contract.
    return memory.write(b.submissionId, apply)["value"]


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
