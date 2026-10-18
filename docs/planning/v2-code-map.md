# V2 code map and cleanup — 18 October 2026

Scope: inspect `claude/v2` at `e3432e5`, remove unused files and retire classic under the owner's
explicit instruction in [decision 0012](../decisions/0012-v2-only-repository.md).

## Runtime paths

| Entry | Implementation and dependencies |
|---|---|
| Browser startup | `web/src/main.tsx` → `App.tsx`; v2 language context and shared room helpers |
| `/` overview | `features/v2/OverviewLanding.tsx`; replay, board map, activity and demo controls |
| `/report` family intake | `features/v2/V2Page.tsx` → `Phone.tsx`; chat, browser voice, incoming callback, status and follow-up cards |
| `/v/*` volunteers | `features/v2/volunteer/`; overview, feed, zone, family, editable visiting order and mission route; `TripPage.tsx` remains routed at `/v/plan/legacy` |
| V2 client | `features/v2/api.ts`, `liveVoice.ts`; shared HTTP, room headers and WebSocket origin helpers |
| Server startup | `api/main.py` registers `api/v2/routes.py` and `api/v2/live.py`, installs security and serves `web/dist/` |
| Intake and updates | `api/v2/intake.py`, `calls.py`, `followup.py`, `ai.py`, `reader.py`, `pipeline.py`; facts feed households, observations and activity |
| Map and flood | `geo.py`, `sim.py`, `assim.py`, `level.py`, `board.py`; buildings, streets, zones, scenario/fact caches, terrain, simulation and timeline files in `data/hy-2025-11/` |
| Plans and missions | `cases.py`, `plans.py`, `suggest.py`, `routing.py`, `shelters.py`; `suggest.py` still imports validation/context helpers from `copilot.py` |
| Rooms and persistence | `api/server/rooms.py` provides lightweight v2 room leases; `api/v2/store.py` optionally persists rooms in Firestore |
| Shared backend | V2 imports Gemini/budget/usage from `api/ai/`, key-model configuration from `api/ai/gemini.py`, and Pinpoint from `api/location/pinpoint.py` |

## V2-only boundary

The browser keeps `/`, `/report` and `/v/*`. Old classic browser URLs fall back to the v2 overview.
Classic API handlers are removed and return 404; `/api/health` (v2 alias) and `/api/config` (Maps key)
remain shared endpoints. V2 no longer constructs MemoryStore/FloodReplay or imports classic intake,
views, rules, solver or ADK code. The key-model fallback list moved unchanged into `api/ai/gemini.py`.
The frontend loads static OSM streets directly instead of importing the classic view/fixture loader.
All pages use the API without requiring a fixture-mode switch.

Removed groups include classic frontend features, shell, demo roles, translation/fixture stores and
exclusive tests; classic backend intake, views, rules, memory/replay, location resolver, solver notebook
and exclusive tests; classic fixture payloads, extraction/triage evaluation sets and fixture generators.
ADK, OR-Tools, their direct compatibility pins and notebook/test dependencies used only by classic
were removed from API dependency declarations. Docker no longer copies classic contract/seed data.

The copilot backend remains under [decision 0011](../decisions/0011-zone-plan-suggestions.md), and
`suggest.py` still uses its helpers. The earlier v2 `TripPage.tsx` remains routed at `/v/plan/legacy`.
Flood datasets, Earth Engine preparation, v2 generators/evaluation and their source provenance remain.
`contract/fixtures/areas.hy-2025-11.json` remains because shared geography preparation/tests consume it.
Historical specifications, decisions and QA reports are retained; they describe their dated revisions.

## Additional unused files removed

- `web/src/features/v2/Panels.tsx`: no runtime or test imports, and none of its four exported
  components have callers. The only remaining mention was a historical QA report, now annotated.
- `data/scripts/build_v2_flood_sim.py`: superseded city-only diffusive model. No code imports or
  invokes it. The committed `v2-sim.json` identifies basin run `s10`, the local-inertial model and
  4 cm encoding, rather than this older generator's diffusive model and 2 cm encoding. Current
  preparation uses `build_v2_basin_sim.py` followed by `publish_v2_sim.py`; README and runtime
  module documentation now point to that pipeline. Existing simulation assets are retained.

Both removed sources remain recoverable in Git history. The classic removals above are explicitly approved in decision 0012.

## Validation

- `npm --prefix web run check`: TypeScript, design tokens and 139 tests in 26 files passed.
- `npm --prefix web run build`: passed; main JavaScript 577.54 → 370.42 kB, CSS 171.19 →
  103.38 kB (uncompressed). The former >500 kB warning is gone; classic fixture chunks are absent.
- Python API/data checks: 212 tests passed, including room isolation/reset, storage, voice/security
  limits and retired API routes. The existing Starlette/httpx deprecation warning remains. Tests use
  the project interpreter with cached pytest helpers added only to the test process; no packages
  were installed. A clean container rebuild and paid-service checks were not run.
- No paid API calls, deployment, remote publication or commit performed.
- Python source parsing, local-import resolution, deploy-script syntax, new/changed documentation
  links, whitespace and sensitive/private-content scans passed.
- Removed 181 tracked files; original checkout edits are preserved in the original working directory.

A fresh [cleanup retest](../eval/v2-cleanup-retest.md) also verifies the built app over real HTTP and
the browser report → plan → pickup → family-confirmation flow, with external services disabled.
