# ReachPoint web app

The repository runs v2 only ([decision 0012](../docs/decisions/0012-v2-only-repository.md)).

```bash
cd web
npm ci
npm run dev        # Vite proxies /api to the backend at localhost:8093
npm run check      # TypeScript, design tokens and tests
npm run build      # production app, served by api/main.py
```

Run the FastAPI server as described in the [root README](../README.md).
All pages use the v2 API; fixture mode and classic demo roles have been retired.

| Path | Purpose |
|---|---|
| `src/main.tsx`, `src/App.tsx` | React startup and routes: `/`, `/report`, `/v/*` |
| `src/features/v2/` | Overview/replay, family phone, board map and browser voice |
| `src/features/v2/volunteer/` | Overview, feed, case, zone, visiting-order suggestion and mission |
| `src/features/v2/ui/` | Cards, evidence, demo controls and Thai/English language context |
| `src/data/` | Shared HTTP client, demo room, WebSocket origin, Maps loader and static street data |
| `src/ui/` | Shared design tokens, base styles and inline icons |

The backend lives in `api/v2/`. See the [v2 code map](../docs/planning/v2-code-map.md) for runtime
and data dependencies. Historical QA reports in this folder describe their dated revisions.

Use shared tokens for colours, type, spacing and sizes. Unknown water remains unknown, estimates
stay labelled, and exact household locations follow the server's team/zone visibility rules.
