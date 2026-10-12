# ReachPoint HTTP API (draft v0.1, 12 Oct 2026)

What the web app calls in API mode (`VITE_DATA=api` or `?data=api`; see `web/src/data/mode.ts`). The starter server
in `api/main.py` implements all of it on an in-memory copy of `contract/seed/demo.hy-2025-11.json`, so the screens
work end to end before Firestore is connected. The friend's version keeps the same routes and shapes and moves the
records to Firestore, with each write in one transaction (pack §4.2).

Views are built by `api/views`. Legacy fixture mode remains available; the flood workspace requires the API, and its live transport plan uses current records rather than the split-panel fixture.

## Conventions

- JSON in and out. Times are ISO 8601 UTC (`2026-10-11T03:16:00Z`).
- Every write carries `submissionId` (random, from the client). Sending the same one again returns the first result
  and changes nothing (safe retry).
- A rule failure is **HTTP 409** with `{ "code", "message", "detail" }`. Codes: `ALREADY_TAKEN`,
  `NOT_ENOUGH_CAPACITY`, `NEED_CHANGED`, `ALLOCATION_CLOSED`, `ALLOCATION_HELD`, `VERSION_CONFLICT`, `NOT_AVAILABLE`, `INVALID`.
  `message` is shown to the user as is, so it is plain English ("Already taken by T-R").
- Unknown IDs are **404**. Bad input (missing field) is **422**.
- A successful write returns `{ "ok": true, "value": … }`; the client then fetches the affected view again.
- Sign-in is a demo role for now (`X-Demo-Actor: team:T-S`, `coordinator:demo-1`); Firebase Auth replaces it.

## Views (GET)

| Route | Returns | Built by |
|---|---|---|
| `/api/views/areaBriefing/{areaId}` | `AreaBriefingView` | `api.views.briefing.area_briefing` |
| `/api/views/teamMissions/{teamId}` | `TeamMissionsView` (open listings in the shared order, the team's jobs with exact points and medical notes) | `api.views.team.team_missions` |
| `/api/views/zoneOrder` | zone order + suggested checks | `api.views.desk.zone_order_view` |
| `/api/views/rain/{areaId}` | `RainStatus[]` for the replayed day (the screen picks the newest at or before its clock) | `api.views.desk.rain_view` |
| `/api/views/risingWater/{areaId}` | `RisingWaterView[]` for the replayed day | `api.views.desk.rising_water_view` |
| `/api/views/splitPanel?areaId=P-B` | `SplitPanelView`, current whole-family **transport** plan; area optional; no live What-if scenarios | `api.views.planning.panel` |
| `/api/views/floodMap?source=operations` | shared `FloodView`; `source=replay` selects isolated simulation | `api.views.flood.flood_map` |
| `/api/health` | `{ "ok": true, "store": "memory" \| "firestore", "seedVersion" }` | |

## Team actions (POST)

| Route | Body | Rules (all in one transaction) | `value` |
|---|---|---|---|
| `/api/listings/{listingId}/claim` | `teamId`, `groupIds[]`, `expectedRevision` | team Available; capable; every group open; seats enough; revision unchanged | the new `Job` (with exact pickup and, for that team only, medical notes) |
| `/api/allocations/{allocationId}/window` | `start`, `end` | job open; set by its own team | — |
| `/api/allocations/{allocationId}/progress` | `state`: `on_the_way` \| `on_scene` | job open | — |
| `/api/allocations/{allocationId}/close` | `outcome`: `done` \| `already_left` \| `not_found` \| `needs_more_help` | job open; medical notes removed from the team's view (D38); `needs_more_help` reopens the groups | — |
| `/api/allocations/{allocationId}/hand-back` | `reason` | job open; groups reopen with "Back from T-x: reason"; seats return | — |
| `/api/teams/{teamId}/status` | `status`, `reason`, `backAbout` | reason and back-about cleared on Available | — |
| `/api/listings/{listingId}/reconfirm` | `teamId` | marks "re-confirm requested" for the desk | — |

## Desk actions (POST, coordinator)

| Route | Body | Rules | `value` |
|---|---|---|---|
| `/api/resources/{resourceId}/unavailable` | `submissionId` (required), `reason`, `nextStatusUpdate` (future ISO timestamp with timezone) | coordinator review; all-or-nothing; resource unavailable; unfinished **transport** allocations using it held, owned by coordinator; groups reopen in the existing priority order; windows withdrawn, retained for history; capacity excluded; medical missions, completed jobs, drafts and other resources unchanged | `{ resourceId, heldAllocationIds[], alreadyUnavailable? }` |
| `/api/listings/{listingId}/urgent-flag` | `reason`, `confirmedNow` | reason required (`INVALID`); tier 1b → RED on every team view; `needRevision` + 1; `confirmedNow` moves "last confirmed" to now (D42) | — |
| `/api/ask-teams` | `suggestionId`, `teamIds[]` | legacy stub; retained for compatibility, not used by the live split screen | `AskResult` |
| `/api/plans/ask` | required `submissionId`, `suggestionId`, nonempty unique `teamIds[]`, optional `areaId` | recompute under the write lock; same optimal suggestion and suggested teams required; stores asks only; no claims, reserved seats or promised windows | **flat** `AskResult`; stale suggestion returns HTTP 200 with `ok: false`, `code: VERSION_CONFLICT`, `detail.current` |

S1 review retains allocation IDs and a `history` event containing before/after snapshots. Held jobs carry
`owner: coordinator`, `holdReason`, `nextStatusUpdate{at,by}`, a new `briefRevision` and pending brief acknowledgment.
The stored window has `state: withdrawn`, `withdrawnAt`, `withdrawnBy`. The team view returns `window: null` and
`withdrawnWindow` for display as an earlier, withdrawn estimate. The family's status says "Transport: on hold;
new time not known" and names the withdrawn estimate and the coordinator's next **status update**, never a new
arrival estimate. A replacement team's actual claim supersedes that held status; its time remains unknown until
it sets a window. `window`, `progress`, `close` and `hand-back` on a held allocation return `ALLOCATION_HELD`.
An unavailable resource cannot claim jobs even if its team sets itself Available. Repeating the same submission
returns the first result; another review of an already unavailable resource changes nothing.
This starter retains the existing demo-role model; production coordinator authorization is still a Firestore/Auth handoff.

## Intake, desk review, family status

| Route | Body | Rules | `value` |
|---|---|---|---|
| `POST /api/intake/text` | `text` (1–2,000 chars), `channel` | Gemini proposes facts; each must quote the caller's text or it is dropped (`api/intake/extract.py`); stored as a proposal, never a case | `reportId`, `statusToken`, `statusUrl`, `aiSource` |
| `GET /api/views/reviewQueue` | — | coordinator only: the caller's words, the proposal, a landmark suggestion, urgent / stretcher / neighbour prompts | `ReviewQueueView` |
| `POST /api/reports/{reportId}/approve` | `segmentId`, `people{adults,children,infants,stretcher}`, `needs[]`, `waterBand`, `urgentReason`, `deskNote` | the coordinator's values, not the AI's, become a validated case with one listing per need; an urgent reason makes the evacuation listing tier 1b (RED) | `caseId`, `listingIds` |
| `POST /api/reports/{reportId}/reject` | `reason` | reason required; the family's link shows it | — |
| `GET /api/status/{token}` | — | that request only, honest per-family lines; a random 128-bit token, 404 if unknown | `ResidentStatusView` |

## Zone missions and segments (D17b, D18, D20)

| Route | Body | Rules | `value` |
|---|---|---|---|
| `POST /api/zone-missions` | `zoneId`, `reasons[]` | coordinator; one mission per zone; the zone gets no new suggested check | `missionId` |
| `POST /api/suggested-checks/{zoneId}/dismiss` | `reason` | reason required | — |
| `POST /api/segments/{segmentId}/take` | `teamId` | the zone has a published mission; team Available; one team per segment (`ALREADY_TAKEN`) | `claimId` |
| `POST /api/segment-claims/{claimId}/mark` | `state`: `checked` \| `partly_checked` \| `could_not_reach`, `householdsFound`, `pickupsNeeded`, `reason` | pickups ≤ households; couldn't reach needs a reason and never clears the zone | — |
| `POST /api/intake/text` with `segmentId`, `teamId` | field report | reaches the review queue as `channel: field`, with the segment as the place | as above |

The team view carries `zoneMissions` (each segment's state, register count, estimate, reviewed families) and
`segmentJobs` once a mission exists.

## Triage agent (D22, D29, C13)

After each new request the server runs one pass of the ADK triage agent (`api/ai/triage.py`) in the background. Its
proposals appear on `GET /api/views/reviewQueue` as `triage` per request (possible duplicates with place, reason and
quote; a rank reason) and the queue is sorted with danger signs always first. The agent's tools are read and propose
only; a person decides:

| Route | Body | Rules |
|---|---|---|
| `POST /api/reports/{reportId}/link` | `caseId` | nothing is deleted: the request is kept as `linked`, the case counts as just confirmed, the caller's status link follows the case; a request with a danger sign is never linked away (`INVALID`) |
| `POST /api/reports/{reportId}/not-same` | `caseId` | hides that proposal for this request |

Live eval: `python api/scripts/triage_eval.py` (needs the Gemini key; 8 checks).

Still to add (friend): the voice call screen.

## Flood observations and isolated replay (user-owned demo)

Shapes: `api/contract/flood.py` (validated write bodies), `web/src/data/flood.ts` (shared view), and
[handoff / demonstration instructions](../docs/planning/flood-map-handoff.md). Representative synthetic intake:
`contract/fixtures/surge.samples.json`; generate all 1,200 with `python -m data.scripts.build_surge --output /tmp/reachpoint-surge`.

| Route | Body | Effect / response |
|---|---|---|
| `POST /api/water-observations` | required `submissionId`, `reportId`, `segmentId`, `siteId`, `quote`; band or measured `depthM`; optional `observedAt`, `evidenceRef`, `uncertaintyM`, `reference`, `source`, `trend` | atomic append to `waterObservations`, always `review: ai_read`; `{ok:true,value:{observationId,review}}`; no assistance, household merge or commitment |
| `POST /api/demo/flood-replay/step` | required `submissionId`, `expectedCursor`, `expectedRevision`; `count` 1–200, default 20 | process the next batch; flat `{ok:true,cursor,revision,total}`; all-or-nothing |
| `POST /api/demo/flood-replay/reset` | required `submissionId`, `expectedCursor`, `expectedRevision` | clear replay cursor/results only, increment revision; same flat response; operational seed unaffected |

Observation location must be explicitly quoted and must be a known segment landmark; `siteId` must equal
`segmentId`. Original report must exist and not be rejected; approved/linked reports can also contribute evidence.
The source must match its intake channel: `text`, `simulated_call`, `phone_transcript` or `field`. A phone transcript is
supplied text, not proof of an implemented telephone integration. Quote is retained internally and must be a substring
of the report. Numeric values require matching explicit metre units in the quote (0–15 m); reference and trend need
supporting words. Current starter timestamp validation requires the explicit ISO timestamp in the quote, with a timezone;
otherwise leave `observedAt` unknown. It never defaults to received time. Future times are refused. Evidence reference
defaults to report ID; a different repeated-observation reference must appear in the original text. Distinct references do
not prove independent observers. Unknown reference remains unknown. Unsupported fields return 409 without an append;
unknown report is 404; shape violations/extra fields are 422.

Map projection includes only landmark coordinates, whitelisted observation metadata, local estimates, separate report
and verified-demand counts, job/check coverage and team landmarks. No source quotes, transcripts, household points,
status tokens or medical narratives are returned. Replay exceptions expose reasons and IDs, not original text. Latest
100 exceptions and last 40 observations in the UI are display limits; full replay records remain in memory. Legacy body
bands retain unknown observation time and do not become metre measurements.

Estimator `local-envelope-v1`: group by reported segment/site, newest dated observation and preceding 30 minutes;
exclude future, disputed/superseded evidence; numeric estimates require at least two distinct numeric source references
with street-ground reference. Each source contributes its latest measurement. Return the union of reported intervals
with minimum ±0.15 m, a median when intervals overlap, and `conflicting` with no central value when they disagree.
Newest evidence older than six hours is `stale` with no current numeric range. Bands stay qualitative. Thresholds and
reference uncertainty are prototype rules, not validated flood accuracy, confidence bounds, depth interpolation or
route safety. Conflicting envelopes retain high reports; more correlated messages do not shrink the floor.

Replay uses a separate lock/store and virtual clock, labelled deterministic template parsing; no Gemini or live calls.
Both cursor and monotonically increasing revision prevent stale tabs advancing a reset replay. Submission IDs return
the first successful response, including after reset. Operational demo reset and replay reset are separate. Both stores
are in-memory and reset on server restart; this is workflow demonstration, not production throughput evidence.

Live planning reads unassigned validated whole-family groups and residual transport seats, preserving existing
commitments. Map depth never decides route feasibility or creates urgency/clinical decisions. A stored team ask includes
original listing/group IDs and expected need revisions, and appears only in that team's `TeamMissionsView.asks`.
Teams still use existing claim/window/progress rules. Plan identity changes with needs, resources and commitments
(or the minute-level snapshot); stale asks write no new event. Medical and supplies remain separate existing workflows.
The current demo-role access model is retained; production authentication and automatic AI-read assistance filing are
explicit friend-owned handoffs.
