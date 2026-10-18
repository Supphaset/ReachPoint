"""Where Gemini calls go (api/ai/gemini.py): Vertex AI on Cloud Run, the key locally; lite models first."""

from api.ai import gemini as G


def test_route_choice(monkeypatch):
    monkeypatch.setattr(G, "_credentials", lambda: (object(), "reachpoint-main"))
    monkeypatch.setattr(G, "ROUTE", "vertex")
    assert G.use_vertex() and G.models(("key-model",)) == G.VERTEX_MODELS and "lite" in G.VERTEX_MODELS[0]
    monkeypatch.setattr(G, "ROUTE", "key")
    assert not G.use_vertex() and G.models(("key-model",)) == ("key-model",)
    monkeypatch.setattr(G, "ROUTE", "auto")
    monkeypatch.setattr(G, "api_key", lambda: None)
    assert G.use_vertex()  # no key, but credentials: Vertex
    monkeypatch.setattr(G, "api_key", lambda: "k")
    assert not G.use_vertex()  # a key on this machine: the key


def test_vertex_requests_use_the_project_endpoint_and_a_token(monkeypatch):
    seen = {}
    monkeypatch.setattr(G, "ROUTE", "vertex")
    monkeypatch.setattr(G, "_credentials", lambda: (object(), "reachpoint-main"))
    monkeypatch.setattr(G, "_token", lambda: "tok")
    import httpx
    monkeypatch.setattr(httpx, "post", lambda url, headers, json, timeout: seen.update(url=url, headers=headers))
    G.post("gemini-3.5-flash-lite", {}, 5)
    assert seen["url"].startswith("https://aiplatform.googleapis.com/v1/projects/reachpoint-main/locations/global/")
    assert seen["headers"] == {"Authorization": "Bearer tok"}


def test_reader_tries_lite_models_first(monkeypatch):
    monkeypatch.setattr(G, "ROUTE", "vertex")
    monkeypatch.setattr(G, "_credentials", lambda: (object(), "p"))
    assert G.models(G.KEY_MODELS)[0] == G.VERTEX_MODELS[0]
