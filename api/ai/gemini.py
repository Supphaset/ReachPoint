"""Where Gemini calls go: Vertex AI on our Google Cloud project, or the Gemini API with a key.

REACHPOINT_GEMINI picks the route:
    vertex  Vertex AI with the service's own identity (Application Default Credentials). No key, billed to the project,
            no free-tier daily caps. Available when selected explicitly.
    key     The Gemini API with GEMINI_API_KEY (environment only). Handy for local work.
    auto    (default) the key when there is one, otherwise Vertex when credentials are found.
The key and access tokens are never logged or sent to the browser.
"""

from __future__ import annotations

import os
import threading

ROUTE = os.environ.get("REACHPOINT_GEMINI", "auto")
# Vertex model IDs on the global endpoint, lite first: fast, cheap, and enough for reading a request.
VERTEX_MODELS = tuple(m.strip() for m in os.environ.get(
    "GEMINI_VERTEX_MODELS", "gemini-3.5-flash-lite,gemini-3.1-flash-lite,gemini-3.8-flash").split(",") if m.strip())
VERTEX_LOCATION = os.environ.get("GEMINI_VERTEX_LOCATION", "global")
KEY_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
_creds_lock = threading.Lock()
_creds = None


def api_key() -> str | None:
    if os.environ.get("GEMINI_API_KEY"):
        return os.environ["GEMINI_API_KEY"].strip()
    return None


def _credentials():
    """Application Default Credentials and project, or (None, None)."""
    global _creds
    with _creds_lock:
        if _creds is None:
            try:
                import google.auth
                c, p = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
                _creds = (c, os.environ.get("GOOGLE_CLOUD_PROJECT") or p or getattr(c, "quota_project_id", None))
            except Exception:
                _creds = (None, None)
        return _creds


def project() -> str | None:
    return _credentials()[1]


def use_vertex() -> bool:
    if ROUTE == "vertex":
        return True
    if ROUTE == "key":
        return False
    return not api_key() and bool(project())


def available() -> bool:
    return use_vertex() and bool(project()) or bool(api_key())


def models(key_models: tuple[str, ...]) -> tuple[str, ...]:
    return VERTEX_MODELS if use_vertex() else key_models


def _token() -> str:
    from google.auth.transport.requests import Request
    c, _ = _credentials()
    if c is None:
        raise RuntimeError("no Google Cloud credentials")
    with _creds_lock:
        if not c.valid:
            c.refresh(Request())
        return c.token


def post(model: str, body: dict, timeout: float, key: str | None = None):
    """generateContent on the chosen route; returns the httpx response."""
    import httpx
    from api.ai.usage import usage
    usage.reserve()
    body = {**body, "generationConfig": {"maxOutputTokens": 2048, **body.get("generationConfig", {})}}
    if key is None and use_vertex():
        url = (f"https://aiplatform.googleapis.com/v1/projects/{project()}/locations/{VERTEX_LOCATION}"
               f"/publishers/google/models/{model}:generateContent")
        return httpx.post(url, headers={"Authorization": f"Bearer {_token()}"}, json=body, timeout=timeout)
    return httpx.post(KEY_ENDPOINT.format(model=model), headers={"x-goog-api-key": key or api_key() or ""},
                      json=body, timeout=timeout)


def genai_client():
    """A google-genai client on the same route (the call conversation and the ADK agent use the SDK)."""
    from google import genai
    if use_vertex():
        c, p = _credentials()
        return genai.Client(vertexai=True, credentials=c, project=p, location=VERTEX_LOCATION)
    return genai.Client(api_key=api_key())


def adk_env() -> None:
    """Point ADK (google-genai inside) at the same route through its environment variables."""
    if use_vertex():
        os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "TRUE"
        os.environ.setdefault("GOOGLE_CLOUD_PROJECT", project() or "")
        os.environ["GOOGLE_CLOUD_LOCATION"] = VERTEX_LOCATION
    else:
        os.environ["GOOGLE_API_KEY"] = api_key() or ""
        os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "FALSE"
