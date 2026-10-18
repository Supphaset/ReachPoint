"""Browser boundaries and response headers for v2 routes."""

import asyncio
import json
import re
import uuid

from fastapi import HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware

from api.server.rooms import VALID
from api.v2.limits import client_ip, http_limit

ORIGINS = [
    "https://reachpoint-main.web.app", "https://reachpoint-main.firebaseapp.com",
    "https://reachpoint-900867850704.asia-southeast1.run.app", "https://reachpoint-plxxmixu6a-as.a.run.app",
    *[f"http://{host}:{port}" for host in ("localhost", "127.0.0.1") for port in (5173, 4173, 3000, 8080, 8000, 8093)],
]
CSP = "; ".join([
    "default-src 'self'", "base-uri 'self'", "object-src 'none'", "frame-ancestors 'none'", "form-action 'self'",
    "script-src 'self' 'unsafe-eval' blob: https://maps.googleapis.com https://maps.gstatic.com",
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",  # Maps and map pins set inline styles.
    "font-src 'self' https://fonts.gstatic.com",
    "img-src 'self' data: blob: https://*.googleapis.com https://*.gstatic.com https://*.google.com https://*.googleusercontent.com",
    "frame-src https://*.google.com",
    "connect-src 'self' data: blob: https://*.googleapis.com https://*.gstatic.com https://*.google.com "
    "wss://reachpoint-900867850704.asia-southeast1.run.app wss://reachpoint-plxxmixu6a-as.a.run.app "
    "ws://localhost:5173 ws://localhost:8000 ws://localhost:8080 ws://localhost:8093 ws://127.0.0.1:5173 ws://127.0.0.1:8000 ws://127.0.0.1:8080",
    "worker-src 'self' blob:", "media-src 'self' blob:",
])
HEADERS = {
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "X-Content-Type-Options": "nosniff", "Referrer-Policy": "strict-origin-when-cross-origin",
    "X-Frame-Options": "DENY", "Permissions-Policy": "microphone=(self), geolocation=(self)",
    "Content-Security-Policy": CSP,
}
ID = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
MAX_BODY = 32768


def install(app, rooms):
    app.add_middleware(CORSMiddleware, allow_origins=ORIGINS, allow_methods=["GET", "POST", "OPTIONS"],
                       allow_headers=["Content-Type", "X-Demo-Room", "Authorization"],
                       expose_headers=["Retry-After", "X-Demo-Room"])

    @app.middleware("http")
    async def harden(request, call_next):
        lease = None
        response = None
        try:
            origin = request.headers.get("origin")
            if origin and origin not in ORIGINS:
                response = JSONResponse({"error": "origin_not_allowed"}, status_code=403)
            else:
                raw = request.headers.get("x-demo-room") or request.query_params.get("room")
                room = raw if raw and VALID.fullmatch(raw) else uuid.uuid4().hex if raw else "main"
                request.state.demo_room = room
                path = request.url.path
                body = {}
                if request.method == "POST":
                    data = bytearray()
                    async for chunk in request.stream():
                        data.extend(chunk)
                        if len(data) > MAX_BODY:
                            raise HTTPException(413, "Request body too large")
                    # Restore the bounded body for FastAPI's model parser.
                    request._body = bytes(data)
                    try:
                        body = json.loads(data) if data else {}
                    except ValueError:
                        body = {}
                    if not isinstance(body, dict):
                        body = {}
                room_request = request.method in ("GET", "POST") and path.startswith("/api/") and path not in ("/api/v2/health", "/api/config")
                creating = room_request and not await asyncio.to_thread(rooms.contains, room)
                retry = http_limit(request.method, path, client_ip(request), room, body, creating=creating)
                if retry:
                    response = JSONResponse({"error": "rate_limited", "retryAfter": retry}, 429, headers={"Retry-After": str(retry)})
                else:
                    # Reject malformed household and zone IDs before route lookups.
                    ids = re.findall(r"/(?:cases|zones)/([^/]+)", path)
                    ids += [z.strip() for z in request.query_params.get("zones", "").split(",") if z.strip()]
                    ids += [request.query_params[k] for k in ("zone", "areaId") if k in request.query_params]
                    if any(not ID.fullmatch(i) for i in ids) or len(ids) > 200:
                        raise HTTPException(422, "Invalid identifier")
                    if room_request:
                        lease = await asyncio.to_thread(rooms.acquire, room)
                    response = await call_next(request)
                response.headers["X-Demo-Room"] = room
        except HTTPException as exc:
            value = exc.detail if isinstance(exc.detail, dict) else {"detail": exc.detail}
            response = JSONResponse(value, exc.status_code, headers=exc.headers)
        except Exception as exc:
            import logging
            logging.error("Request failed: %s", type(exc).__name__)
            response = JSONResponse({"error": "server_error"}, 500)
        finally:
            if lease:
                await asyncio.to_thread(rooms.release, lease)
        if request.headers.get("origin") in ORIGINS:
            response.headers["Access-Control-Allow-Origin"] = request.headers["origin"]
            response.headers["Access-Control-Expose-Headers"] = "Retry-After, X-Demo-Room"
            response.headers.add_vary_header("Origin")
        for key, value in HEADERS.items():
            response.headers[key] = value
        return response
