# ReachPoint HTTP API (draft v0.1, 12 Oct 2026)

What the web app calls in API mode (`VITE_DATA=api` or `?data=api`; see `web/src/data/mode.ts`). The starter server
in `api/main.py` implements all of it on an in-memory copy of `contract/seed/demo.hy-2025-11.json`, so the screens
work end to end before Firestore is connected. The friend's version keeps the same routes and shapes and moves the
records to Firestore, with each write in one transaction (pack §4.2).

Views are always built by `api/views` (the same functions that write `contract/fixtures`), so a screen that works on
the fixtures works on the server.

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
| `/api/views/splitPanel` | `SplitPanelView` | stored suggestion (`allocationSuggestion` + What-ifs) |
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
| `/api/ask-teams` | `suggestionId`, `teamIds[]` | returns **200** with `AskResult`: `ok: false, code: VERSION_CONFLICT` and the current suggestion when the input changed (C7) | `AskResult` |

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

## Locating a request (D25)

A request can carry a **location**: a pin from the caller's phone (GPS or a tap on the map) or an address
(typed by the caller, or by the coordinator from a phone call). The server resolves it, snaps it to the segment and
nearest landmark, and keeps the exact point for the coordinator and the team that takes the job only.

`LocationInput` (client → server), one of:
- `{ "kind": "pin", "lat": 7.0089, "lon": 100.4705, "method": "gps" | "map", "accuracyM": 25 }`
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
