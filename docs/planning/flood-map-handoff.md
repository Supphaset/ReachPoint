# Flood workspace: implementation and integration handoff

12 Oct 2026 · user-owned implementation under [0010](../decisions/0010-surge-demonstration-and-exception-review.md).
Contract changes need review by both humans. No new dependencies, providers, services, infrastructure or AI calls.

## Delivered

- `/desk/map`: Water, Needs and Response modes over existing Hat Yai zones, historical satellite extent and dotted
  no-data areas. City-level zone summaries, zone focus and keyboard-selectable segment list share the same evidence selection. Response mode
  shows operational team landmarks, held/active jobs and segment checks. Historical dates remain explicit.
- Observation drawer: AI-read/verified provenance, measured depth or qualitative band, observed versus received time,
  reference, reported trend, local uncertainty envelope, conflicting/stale/insufficient states and observation history.
  Shared map responses withhold quotes, household points, transcripts and medical narrative.
- Deterministic 1,200-report scenario: 800 texts / 400 simulated-call transcripts; routine, urgent, updates, water-only,
  ambiguous and malformed categories. Repeated observation references, contradictions, rising water, unknown times
  and mixed Thai/English templates. Evaluation truth is separate and discarded before processing.
- Isolated replay: play/pause, next 20/200, reset, virtual clock, organized/exception/urgent/observation counters. Cursor
  plus revision handles concurrent/stale tabs; submission IDs make retries safe. A failed batch has no partial effect.
  No operational request, job, family status, medical record, draft or capacity is changed by replay/reset.
- Live operational transport plan: current open whole-family groups, deterministic priorities, remaining capable seats,
  existing commitments excluded. Coordinator asks are retry-safe recorded events, shown in the relevant team's waiting
  page. Team acceptance still uses the existing atomic claims; asks reserve nothing and promise no arrival time.
  S1 failure holds/reopens work, removes its capacity and invalidates the prior suggestion.

## Local demonstration

Use installed dependencies; start from the repository root:

```sh
REACHPOINT_AI=off .venv/bin/python -m uvicorn api.main:app --host 127.0.0.1 --port 8080
```

In another terminal build the web bundle (then restart the server so it mounts the assets):

```sh
cd web
VITE_DATA=api npm run build
```

Open `http://127.0.0.1:8080/desk/map?data=api`, choose the coordinator demo role if prompted.

1. Play or advance reports. Inspect Water and Needs; counts represent reports, not distinct households. Inspect a
   conflicting site and an unknown-time band. Unknown/blind spots never mean dry. The attention queue retains urgent,
   ambiguous, possible-update and invalid reports; water conflicts have their own map indicator/range.
2. Switch to Operational demo jobs. Inspect reviewed unmet groups, team capacity and coverage; choose a segment/area
   and open the current whole-family transport plan. Review the suggested groups and ask the suggested teams.
3. In the relevant team's Waiting screen inspect its recorded ask and take a whole group using existing controls.
   Set a team window only when ready to commit to an estimate. The family link reflects the existing status rules.
4. Use the desk S1 failure review with a coordinator next **status update**, then inspect Response and recalculate.
   S1 has zero free seats; unfinished jobs are held and groups relisted; the old arrival estimate is withdrawn.
5. Reset simulation: operational jobs remain. The separate existing operational demo reset resets seed jobs. A server
   restart loses both in-memory stores. Refresh a stale replay tab before advancing again.

Export the full scenario for integration/evaluation:

```sh
.venv/bin/python -m data.scripts.build_surge --output /tmp/reachpoint-surge
```

`intake.json` is the only processor input. `truth.json` is evaluation-only. Twelve representative intake samples are
tracked in `contract/fixtures/surge.samples.json`; they contain no expected labels or hidden household identity.

## Friend-owned integration

1. Save/acknowledge incoming text or browser-voice transcript before extraction. Keep original text, immutable report
   ID and submission ID; unknown facts remain unknown. A transcript channel can be `phone_transcript`; no real phone
   number or telephony service is provided by this PR.
2. Implement the accepted automatic AI-read assistance filing and exception policy. Existing `/api/intake/text` still
   requires desk approval before creating operational listings; this PR deliberately does not replace that worker.
   The replay parser is a constrained simulation adapter, not general Thai/English extraction or live Gemini.
3. After extraction, send quote-backed water facts through `/api/water-observations`, or preserve the same validated
   shape in the storage transaction. See [API contract](../../contract/api.md) and `api/contract/flood.py`. Segment/site
   mean an explicitly reported landmark; don't infer a household site from coarse proximity. Current API requires an
   explicit ISO observation timestamp in the quote; natural-language/unknown times remain qualitative until the time
   normalization contract is expanded with supporting context. Don't substitute ingestion time.
4. Reuse observation reference only when the report explicitly identifies the same observation. Keep uncertain identity
   updates as exceptions; neither common phone nor common landmark establishes a household. Quotes stay in protected
   records; the shared map receives only whitelisted metadata. Field corrections/disputes need append-only review
   events and current evidence state, not deletion of earlier records.
5. Move the map view and live planning adapters to the durable store without changing whole-group claim, capacity,
   replay isolation or version-conflict behavior. Keep the current solver priorities/medical boundaries. The starter
   plan intentionally uses validated transport groups; extend eligibility alongside the agreed AI-read filing contract.
6. When replay can enter the real saved-intake/filing worker, replace the isolated parser with that adapter and add an
   explicit synthetic run boundary/reset so replay cannot contaminate operational records. Preserve visible labels
   distinguishing simulation, real model runs and live browser voice. Keep evaluation truth inaccessible to the worker.

No autonomous clinical triage, boat navigability, safe route, terrain interpolation or production throughput is delivered.
Thresholds (30-minute window, six-hour staleness, ±0.15 m floor) are versioned prototype assumptions. The envelope
shows disagreement among comparable reports; it is not calibrated statistical confidence or a validated flood surface.
Different source references still have unknown observer independence. Continuous maps require suitable terrain/datum,
barriers/time compatibility and field validation, as described in [the plan](surge-demo.md).

## Validation — 13 Oct 2026

- API: `.venv/bin/python -m pytest -q api/tests` — **194 passed** (one existing Starlette/httpx deprecation warning).
  The notebook test uses the installed local kernel; all tests run with `REACHPOINT_AI=off`.
- Data: `.venv/bin/python -m unittest discover -s data/tests` — **41 passed**.
- Web: `npm test` — **46 passed**; `npx tsc --noEmit -p .`, `npm run check:tokens` and
  `VITE_DATA=api npm run build` — **passed**.
- Full replay through the browser: **1,200 received, 720 organized, 480 attention items, 150 urgent reports,
  1,081 water observations, 57 available local estimates, 8 conflicting sites**. These are deterministic scenario
  outputs, not extraction accuracy or capacity benchmarks. The generator export also ran successfully.
- Browser: city summaries, focused segment map, conflicting-evidence drawer, Needs mode, operational resources,
  fresh recorded team ask, stale-plan refusal and team waiting-page visibility checked. Narrow layout at 375 px
  had no horizontal overflow; wide layout checked at 1280 px. A CSS class collision discovered during visual
  testing was fixed by scoping flood-estimate styles.
- Replay retry/reset/concurrency and failed-batch rollback, quote-supported observation writes, source/time/reference
  validation, privacy projection, whole-family planning and S1 invalidation are tested. Replay's complete operational
  seed comparison covers unrelated drafts, other-area quantities, medical records, history and resident state.

No model evaluation, real call, deployment or production load test was run.
