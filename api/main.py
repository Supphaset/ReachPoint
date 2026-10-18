"""V2 FastAPI server and built React app, served together on Cloud Run.

    uvicorn api.main:app --reload
    npm --prefix web run build
"""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from api.server.rooms import Rooms
from api.security import install
from api.v2 import routes
from api.v2.live import router as live_router

ROOT = Path(__file__).resolve().parents[1]
WEB = Path(os.environ.get("REACHPOINT_WEB_DIST", ROOT / "web" / "dist"))

app = FastAPI(title="ReachPoint", version="2", docs_url="/api/docs", openapi_url="/api/openapi.json")
rooms = Rooms()
routes.bind(rooms)
app.include_router(routes.router)
app.include_router(live_router)


@app.middleware("http")
async def demo_room(request: Request, call_next):
    token = rooms.current_id.set(getattr(request.state, "demo_room", rooms.clean(
        request.headers.get("x-demo-room") or request.query_params.get("room"))))
    try:
        return await call_next(request)
    finally:
        rooms.current_id.reset(token)


install(app, rooms)


@app.exception_handler(HTTPException)
async def http_error(_: Request, exc: HTTPException):
    body = exc.detail if isinstance(exc.detail, dict) and exc.detail.get("error") == "rate_limited" else {"detail": exc.detail}
    return JSONResponse(body, exc.status_code, headers=exc.headers)


@app.get("/api/health")
def health():
    return routes.health()


@app.get("/api/config")
def client_config():
    """Restricted browser Maps key; server credentials are never returned."""
    from api.location.pinpoint import _config
    return {"mapsKey": _config("GOOGLE_MAPS_BROWSER_KEY") or _config("VITE_GOOGLE_MAPS_KEY")}


@app.api_route("/api/{path:path}", methods=["GET", "POST"], include_in_schema=False)
def unknown_api(path: str):
    raise HTTPException(404)


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
        return JSONResponse(status_code=503, content={"message": "Web app not built: run npm --prefix web run build"})
    return FileResponse(index)
