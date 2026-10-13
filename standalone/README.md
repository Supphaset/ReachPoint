# Standalone Thai flood-intake prototype

This is the complete, separate intake app that Norrawee developed before moving it into the ReachPoint repository. It has its own LangGraph backend and React frontend. It does **not** write to ReachPoint's `api/` records, publish listings, dispatch teams, or update resident status. ReachPoint's main app remains under `api/` and `web/`.

The backend runs a Thai conversation through `extract_case → lookup_location → chat`, offers Pinpoint location candidates for explicit confirmation, and provides Gemini Live browser voice, optional Google Speech-to-Text, and manual Text-to-Speech replay. The browser app is added in the companion call UI PR.

Use synthetic request details only. Credentials, local conversations, recordings, dependency folders, and build output are excluded from Git. The original app adapts Google's [Gemini Fullstack LangGraph Quickstart](https://github.com/google-gemini/gemini-fullstack-langgraph-quickstart) at `e34e569de465340e42f36cd3cab4fac0c3ce7036`. Its Apache 2.0 license is in [LICENSE](LICENSE); the backend also carries its upstream MIT notice in [backend/LICENSE](backend/LICENSE).

## Backend development

From `standalone/`:

```sh
uv venv --python 3.12 backend/.venv
uv pip install --python backend/.venv/bin/python -e './backend' 'langgraph-cli[inmem]'
cp backend/.env.example backend/.env
```

Set `GEMINI_API_KEY` and `GOOGLE_CLOUD_PROJECT` in the untracked `backend/.env` for the project you are authorized to use. Gemini Live and optional Google speech features also need Application Default Credentials with access to that project. Then start the backend:

```sh
cd backend
.venv/bin/langgraph dev --no-browser
```

The local LangGraph API listens on `http://127.0.0.1:2024`. The backend can start before the browser build exists; `/app/` returns a build notice until the frontend is added and built. This standalone app has no ReachPoint login or production access control, so run it locally only.
