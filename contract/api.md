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
- **Thai twins.** Lines the server writes for the victim and volunteer screens carry a Thai version next to the English
  one (`api/views/thai.py`): status `lines[].th` and `familyTh`; team view `urgency.th {title, summary, kit, withheld}`,
  `urgency.facts[].th`, `groups[].labelTh`, `destination.th {label, reason}`. The web app shows them when the viewer
  picks ไทย. Words people typed (flag reasons, medical notes, caller quotes) are never translated. Rule-failure
  `message`s are still English only.

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

### Caller review (`/desk`, 15 Oct 2026)

The 16 Oct evaluation policy adds `transport_threshold_cm` (50), nullable `reported_water_depth_cm`, and `transport_basis` to AI reviews. Gemini supplies quoted current numeric measurements; server logic validates units and applies the boat planning preference. Ground-floor descriptions alone remain unmeasured. Explicit current unmet food, water, regular medication or evacuation needs are Level 2 evidence. See the [evaluation guideline](../docs/designs/desk-review-guideline.md). These remain candidates requiring human approval and field access confirmation.

The source table is `callers`, transactionally migrated from `help_requests` at startup. Original caller fields remain unchanged. In memory-only mode the same rows live in the operation snapshot. Derived reviews and append-only history are separate from caller statements, validated cases and team commitments.

| Route | Request / result |
|---|---|
| `GET /api/desk` | `{generated_at, callers, counts, ai_enabled}`. Each caller includes its original fields, `input_revision`, `received_at`, `report_status`, `review`, `review_stale`, `immediate_danger`, `reported_emergency_level`, `ai_processing`, and `history`. Counts separate AI-read, human-reviewed and requests awaiting approval. |
| `GET /api/desk/{report_id}` | One caller with the same metadata; missing ID is 404. |
| `POST /api/desk/{report_id}/ai-review` | `{submissionId}`; returns `{ok:true,value:review}`. Model work happens outside the records lock; older results cannot overwrite newer reviews. Same-ID retries return the original result. A new rerun preserves a human review of the same input revision. |
| `POST /api/desk/{report_id}/human-review` | `{submissionId,input_revision,expected_revision,transport_recommendation?,emergency_level?,immediate_danger,volunteer_summary?,reviewed_by,reason,approve?,resolved_location?}`. Atomically saves review/history; stale revisions are 409. `approve:true` requires only the original caller `phone_number`, help type (`type`) and `location`, each nonblank. Derived address/coordinates, transport, urgency and notes may remain null/unresolved. Nullable/omitted transport is represented as `needs_assessment`; nullable/omitted urgency remains null. An explicit routine/priority level still cannot contradict `immediate_danger:true`. Corrections (`approve:false`, default) can remain incomplete and clear approval. |

Review fields: `transport_recommendation` is `boat`, `truck`, or `needs_assessment` (candidates, never route clearance). `emergency_level` is `1a` (suspected medical emergency), `1b` (urgent flood rescue), `2` (priority assistance), `3` (routine/non-emergency), or null (unresolved). `checked_by` is `AI`, `Human`, or null (unreviewed/rules-only). `review_status` is `ai_read`, `human_review_required`, or `human_reviewed`. Also present: `source`, `rules_version`, `review_revision`, `input_revision`, `reviewed_at`, `reviewed_by`, `clinical_assessment: not_assessed`, `reasons[]`, `evidence[{field,quote,kind}]`, `missing_information[]`, and nullable `volunteer_summary`.

Reviews also contain `resolved_location: {address,latitude,longitude,source,status,map_url}`, `approved`, `approved_by` and `approved_at`. Address/coordinates are derived separately from original caller fields. Google Maps links may provide location text and destination coordinates; camera/viewport coordinates are ignored. Short-link redirects are restricted to Maps hosts. Optional server-side Google Maps Geocoding (`GOOGLE_MAPS_API_KEY`, `REACHPOINT_MAPS_GEOCODING=on`, default off) supplies full addresses. Ambiguous/failing lookups remain unresolved. Human correction sets location provenance to `human`; clients cannot supply provider provenance. Changed caller input invalidates current approval while retaining history. `/api/status/{token}` advances to `reviewed` after current human approval, records `approved_at` in `completedAt[1]`, and states that response planning is pending. AI review alone does not advance tracking; no team/case is created by desk approval.

Immediate danger is surfaced before AI completes using a conservative reported-sign escalation floor, and sorts first across medical/rescue categories. Missing evidence/model failure never implies Level 3. Gemini findings require quotes in the corresponding caller field. Dedicated phone, coordinate and address fields are excluded from model input; operational narratives, including access details, and counts are included. Supported excerpts form the optional preparation summary; it does not prescribe medication or invent equipment. Every AI result awaits human approval. New callers trigger background review; opening the desk schedules existing unreviewed/stale rows and older AI rules versions. Stored results prevent repeated Gemini calls on every poll. Explicit retry is available after failure.

The existing validated allocation tiers remain governed by qualified assessment and coordinator approval. Desk recommendations do not approve cases, change clinical assessment, alter inventory, dispatch teams or promise arrival. Case creation remains a separate API action; its former expandable panel is removed from `/desk`. Human-approved preparation notes may appear on accepted active team jobs as `preparationSummary: {text,checkedBy,at}`, absent from shared open listings, other teams' jobs, pending reviews and closed/handed-back jobs. Reviewer identity uses the existing demo identity; it is not authenticated professional accreditation.

### Existing coordinator actions

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
| `GET /api/callers/config` | — | reports whether conversational text and Gemini Live voice are enabled; no credentials returned | `chat`, `voice` |
| `POST /api/callers/sessions` | — | creates an opaque, two-hour in-memory conversation; no report is created | conversation snapshot |
| `GET /api/callers/sessions/{id}` | — | resume an unexpired session | conversation snapshot |
| `POST /api/callers/sessions/{id}/turn` | `text` (1–500 chars), `turnId` | Gemini extracts caller-only facts and asks the next missing topic; repeated `turnId` does not record another turn; up to 16 caller turns | latest conversation snapshot |
| `POST /api/callers/sessions/{id}/location` | `query`, `action: select \| reject`, `locationId` for selection | the current Pinpoint candidate must match the current location query; no coordinate is accepted before caller selection | conversation snapshot |
| `POST /api/callers/sessions/{id}/confirm` | `submissionId`, `expectedRevision` | only after a complete review summary and location choice; rejects an older summary revision; stores the caller's original words, quote-validated proposal and selected location as one report for human review; repeated calls return the same report | conversation snapshot with `sent` |
| `WS /api/callers/sessions/{id}/live` | 16 kHz PCM audio frames | server-side Gemini Live turn tool updates the same session; exact spoken phrase `ยืนยันส่งคำขอ` after summary triggers confirmation; server streams 24 kHz PCM and session snapshots | `ready`, `transcript`, `snapshot`, `interrupted`, `turn_complete`, `error` |
| `GET /api/views/reviewQueue` | — | coordinator only: the caller's words, the proposal, a landmark suggestion, urgent / stretcher / neighbour prompts | `ReviewQueueView` |
| `POST /api/reports/{reportId}/approve` | `segmentId`, `people{adults,children,infants,stretcher}`, `needs[]`, `waterBand`, `urgentReason`, `deskNote` | the coordinator's values, not the AI's, become a validated case with one listing per need; an urgent reason makes the evacuation listing tier 1b (RED) | `caseId`, `listingIds` |
| `POST /api/reports/{reportId}/reject` | `reason` | reason required; the family's link shows it | — |
| `GET /api/status/{token}` | — | that request only, honest per-family lines; a random 128-bit token, 404 if unknown | `ResidentStatusView` |

Conversation snapshots contain `sessionId`, `revision`, `messages`, `case`, `locationLookup`, `canConfirm`, `summary`, and
`sent`. Sessions and reports are in memory in the starter server and reset on restart. The conversation is for the
synthetic demo; do not enter real personal details. `REACHPOINT_AI=off` disables conversational text and voice,
and `REACHPOINT_VOICE=on` explicitly enables the Gemini Live WebSocket. Live requires Google Cloud Application
Default Credentials, `GOOGLE_CLOUD_PROJECT`, and access to `GEMINI_LIVE_MODEL` (default `gemini-3.8-live`) in
`GEMINI_LIVE_LOCATION` (default `us-central1`). Text conversation uses `GEMINI_API_KEY` when set, otherwise
Google Cloud Application Default Credentials, with `GEMINI_CONVERSATION_MODEL` (default `gemini-3.8-flash`) and
`GEMINI_CONVERSATION_LOCATION` (default `global`). The browser receives neither credential. Live sessions close
after ten minutes to bound demo usage.

## Locating a request (D25)

A request can carry a **location**: a pin from the caller's phone (GPS or a tap on the map) or an address
(typed by the caller, or by the coordinator from a phone call). The server resolves it, snaps it to the segment and
nearest landmark, and keeps the exact point for the coordinator and the team that takes the job only.

`LocationInput` (client → server), one of:
- `{ "kind": "pin", "lat": 7.0089, "lon": 100.4705, "method": "gps" | "map" | "pinpoint", "accuracyM": 25 }`
- `{ "kind": "address", "text": "12/3 ถนนนิพัทธ์อุทิศ 2 หาดใหญ่" }`

`Location` (server → client):
`{ "status": "located" | "outside_area" | "unlocated", "kind", "method", "at": [lon, lat] | null,
   "precision": "house" | "street" | "landmark" | "area" | null, "source": "caller pin (GPS)" | "caller pin (map)" |
   "Pinpoint address match" | "address not found" …, "provider": "device" | "pinpoint" | "stand-in",
   "accuracyM"?, "address"?, "segmentId"?, "landmarkId"?, "landmarkLabel"?, "zoneId"?, "areaId"? }`

- A GPS pin is checked against the demo area **on the phone first**; outside it, nothing is sent.
- An address goes to **Pinpoint** (server side, key in Secret Manager / `~/.config/reachpoint/env`, never in the
  browser). With no key, a stand-in resolves only the synthetic demo addresses and landmark names.
- `unlocated` is never dropped: the coordinator picks the landmark by hand, as today.

| Route | Body | Rules | `value` |
|---|---|---|---|
| `POST /api/locate` | `location: LocationInput` | read-only preview (no write, no submissionId); used by the call page and the desk | `Location` |

`POST /api/intake/text` also takes an optional `location: LocationInput`; the resolved `Location` is stored on the
report, shown in `reviewQueue` (`reports[].location`) and preselects `suggestedSegment`. `POST /api/reports/{id}/approve`
also takes an optional `location: LocationInput` (the coordinator's correction, e.g. the address heard on a phone call);
the approved case's exact pickup point is that location (`exactPickup {at, precision, source}`), otherwise the
report's own, otherwise the landmark. The family's status page never shows a point.

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
| `POST /api/demo/flood-replay/step` | required `submissionId`, `expectedCursor`, `expectedRevision`; `count` 1–200, default 20 | process the next batch with fixed rules (records are `review: simulator_read`, never `ai_read`); flat `{ok:true,cursor,revision,total}`; all-or-nothing |
| `POST /api/demo/flood-replay/reset` | required `submissionId`, `expectedCursor`, `expectedRevision` | clear replay cursor/results only, increment revision; same flat response; operational seed unaffected. `POST /api/demo/reset` also starts the replay again |

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

### Caller page and shared request schema

The `/callers` page has Chat, Voice and Form modes. All conversation HTTP and WebSocket endpoints use `/api/callers`: config, sessions, read, turn, location, confirm and live. The previous `/api/call` endpoints have been removed; clients must use `/api/callers`.

The browser form shows five fields: phone number, help type, location (Google Maps link), people details (children, older people, patients, pets), and situation details. The first three are required in the form. The link is saved in `location`; it is not automatically resolved to coordinates. The API retains the shared details below for chat, voice and existing clients.

Chat and voice ask for missing location, food/evacuation type and phone number, then at most one optional prompt for missing people/situation details. When the water level is unknown, this prompt explicitly asks “ตอนนี้น้ำสูงถึงไหนคะ?” (how high is the water), combined with people details if needed. A brief or partial answer is enough; missing optional values remain unknown rather than causing more questions. Chat provides **Skip details** and voice accepts “ข้าม”. Reported immediate danger skips the optional prompt. A spoken place or landmark is accepted for voice; Google Maps links are preserved without inferring coordinates. Existing caller-selected place candidates and contradiction checks still apply. Counts, access details and other information are retained when volunteered, with no separate questions. The brief summary covers the five fields and any supplied extra facts before explicit confirmation. Snapshots expose `canSkipDetails` while the optional prompt is pending.

`POST /api/callers/sessions/{id}/turn` accepts `{text, turnId}`. With `Accept: text/event-stream`, it immediately sends a `status` event, then `delta` events (`{text}`) for the reply and an authoritative `snapshot` event. Extraction validates the full facts before composing the reply; partial model JSON is never shown. Failures after streaming starts send `error` (`{message, status}`) and no snapshot. The browser shows the user message immediately and a reading indicator, then appends reply deltas. Interrupted retries retain the same `turnId`. Other clients keep receiving the JSON snapshot.

`POST /api/callers/sessions/{id}/form` accepts the 13 editable fields below plus `submissionId` and `expectedRevision`. `phone_number` and `type` are required for new requests; other fields are nullable. Phone numbers contain 7–15 digits and may start with `+`; spaces, hyphens, dots and parentheses are removed without changing a leading zero or country prefix. `type` is exactly `food` or `evacuation`. Counts must be nonnegative integers, and coordinates use `latitude, longitude`. The form is reviewed directly before the caller submits it. The API rejects stale revisions, uses the same confirmation/persistence path as conversation intake, and returns the conversation snapshot with `sent`. Retries for the same session return the existing report.

All three modes save exactly these columns in `callers` (renamed from `help_requests`):

```text
report_id
channel
phone_number
type
people_details
n_children
n_elders
n_pets
location
coordinates
location_details
water_level
situation_details
emergency_detail
other_details
```

`report_id` is server-generated. New form, chat and voice requests cannot be confirmed without `phone_number` and `type`, even if those fields are marked unavailable during conversation. Phone numbers support a later follow-up about help received; this change does not send messages. Existing rows retain null for these new fields until collected, and existing saved requests remain readable and retryable. `channel` is `chat`, `voice` or `form`; mixed chat/voice sessions use the latest recorded input mode. The Python model in `api/intake/schema.py` defines the shared fields, and `web/src/data/call.ts` defines the matching browser types. Unknown values stay null; zero means a reported absence. Conversation control state (danger flag, contradictions, unavailable fields, revisions, messages and status tokens) is separate from the stored request columns. No caller name is requested, extracted or stored as a field. See [decision 0012](../docs/decisions/0012-shared-caller-schema.md).

### Caller receipt response and step times

`GET /api/status/{token}` also returns the latest `receipt` (`{answer: yes | no, at}` or null) and `completedAt`, a four-entry timestamp/null array: report received, report reviewed, volunteer visit completed, and caller-confirmed receipt. No timestamp is invented for an unknown historical event.

`POST /api/status/{token}/receipt` accepts `answer: yes | no` and `submissionId`. Possession of this request's private status token grants access to respond for this report only. The API records the response and server timestamp, preserves earlier responses, and scopes retries to the report. Yes supplies the final completion timestamp; No leaves it unset. Responses do not close volunteer allocations or alter confirmed quantities. Demo controls and demo receipt answers never call this endpoint.
