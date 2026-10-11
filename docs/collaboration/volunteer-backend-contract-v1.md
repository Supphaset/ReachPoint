# Volunteer ↔ coordination integration contract — draft v1

Date: 2026-10-11. **Proposed interface specification for both humans to review.** This expands the [delivery agreement](two-person-delivery-agreement.md), not the approved product scope. Operation/field names below are concrete suggestions, not existing functions, endpoints or database tables. No transport, framework, datastore, authentication provider or refresh mechanism is selected. Examples are synthetic documentation; no API, schema or executable mock is implemented.

The [architecture diagrams](../planning/architecture-overview.md) show where these operations connect intake, coordinator review, your volunteer workspace, shared records and resident status.

## Start here: what you can use from your friend

Your friend delivers a shared backend boundary that lets your volunteer screens **read permitted data and submit explicit actions**. Your screens do not need to interpret raw calls, reconcile household identity or directly edit final case/mission records. You deliver flood/source inputs, planning calculations and the volunteer interactions. Your friend integrates the common calculations and enforces authorized updates to shared state.

| Your screen | Reads it needs | Actions it submits | What the screen must show |
|---|---|---|---|
| Daily map/list | `listAreaBriefings`, `getAreaEvidence`, `getOwnTeam` | Select/filter locally; no dispatch from map selection | Same area IDs in map/list, response scope, known gaps, source age, uncertainty, missing assessment |
| Area detail / planner | `getAreaBriefing`, `getOwnTeam`, permitted existing coverage | `submitMissionProposal` | Preview load/gap, input versions, assumptions, pending checks; submitted proposal remains uncommitted |
| My missions | `listOwnMissions` | Open offer/task | Offered, accepted, preparing and held states separated |
| Team mission detail | `getOwnMission` | `respondToMissionOffer`, `acknowledgeBrief`, `submitTeamReport` | Current brief/version, acknowledgment, resource/access checks, reported progress/window, pending changes |
| Team check-in | `getOwnTeam` | `submitTeamUpdate` | Capability/availability basis; proposed changes distinguished from reviewed capacity |
| Field report | Own mission/area reference | `submitFieldReport` | Scoped observation, unknown counts, source/time, saved/pending review; no automatic area clearance |
| Your source-data work | Area/source references and package publication outcome | `submitSourcePackage` | Typed evidence and provenance; publication or rejection, not a promise of valid depth everywhere |

Read operations must return only the caller's permitted records. General volunteer briefings contain aggregates and broad capability requirements, not unrelated resident medical narratives/contact details. Own-assignment details can include the minimum necessary authorized pickup/location information. Your friend separately serves coordinator and resident views from the same records.

## Who creates and updates the “tables”

**Recommended ownership:** your friend defines and maintains the shared storage and write operations; you co-review the fields you depend on. You own the meaning/quality of your source package and planning rules. Each UI submits through the shared boundary; your friend does not manually re-enter your data.

These are logical record groups. They could become tables, collections or another representation after architecture selection; the list is not a physical schema.

| Logical group | Who supplies changes | Who saves/enforces them | Can your UI edit final records directly? |
|---|---|---|---|
| Areas / landmarks / source packages | You supply boundaries, references and dated typed source data | Friend's authorized source-publication operation | Submit package/revision; do not overwrite a published version |
| Incoming reports / proposed events | Friend's chat/phone; your team/field reports | Friend's intake/update pipeline | Submit a new attributed report; no final case overwrite |
| Cases / needs / scoped assessments | Coordinator's operational review; separately appropriate qualified review/fixture | Friend's review operations | No; read permitted summaries/assignment scope |
| Teams / resources | Your leader check-in; coordinator review where required | Friend's team/resource operations | Submit own-team changes; declared capacity is not automatically reviewed capacity |
| Proposals | Your planner | Friend's proposal operation | Submit/revise own draft with version checks |
| Missions / brief versions / acceptance | Coordinator offers/revises; your team accepts/acknowledges/reports | Friend's mission operations | Perform allowed actions; no arbitrary state changes |
| Delivery / receipt / referral / care evidence | Authorized reports and distinct confirmation/review | Friend's evidence/review operations | Submit report; team completion never confirms receipt/care |
| Area briefings / resident status | Derived from the above | Shared deterministic rules, integrated by Friend | No manual totals/status edits; refresh after changed input versions |

Area and resident summaries are views of shared truth. They must not become independently editable sources of truth. If summaries are cached later, the backend must expose their input versions and freshness; the cache strategy remains open.

## Proposed operation catalogue

Names are transport-neutral. Your friend can later expose them through an agreed API/client interface. Do not translate them into provider-specific SDK calls before choosing the architecture together.

| Operation | Your input | Backend returns / guarantees |
|---|---|---|
| `listAreaBriefings` | Planning period, permitted team/mission filters | Area IDs/boundary versions, brief summaries, relevant input versions and freshness; incomplete feed marked explicitly |
| `getAreaBriefing` | Area ID, target scope/period | Detail including source refs, reviewed response mode, distinct exposure/known needs, received/committed/unassigned values, capabilities and unknowns |
| `getAreaEvidence` | Area ID and evidence references | Authorized typed layers/geometry references, source/observation times, units/reference, uncertainty and availability; no invented geometry |
| `getOwnTeam` | Team ID within actor's permitted membership | Team/resource version, declared/reviewed capabilities, stock/availability, capacity assumptions and any permitted reported position/time |
| `listOwnMissions` / `getOwnMission` | Team ID / mission ID | Permitted offers/tasks, scope, status, brief/version/ack, readiness, resource dependencies and separate progress/window |
| `submitSourcePackage` | Submission ID, expected published version if revising, area/boundary references and typed evidence package | Saved proposal/publication result, evidence/package versions, validation issues; preserves older sources and observation times |
| `submitMissionProposal` | Submission ID, own team, selected scope/period, input versions, proposed load/capabilities, assumptions/window and unresolved checks | Proposal ID/version and review state; validates/recomputes using current inputs; creates no accepted coverage from a draft |
| `respondToMissionOffer` | Submission ID, mission ID/version, offered brief version, accept or decline; reason if supplied | Allowed transition or conflict; checks membership/current offer/resource constraints; acceptance alone does not acknowledge brief or confirm arrival/outcome |
| `acknowledgeBrief` | Submission ID, mission/current record version, saved brief version | Acknowledgment for exactly that version or conflict; no inherited acknowledgment after revision |
| `submitTeamUpdate` | Submission ID, own team/resource ID/version, attributed availability/capability/position/stock observation and time | Saved update/review state and version; distinguishes declaration from reviewed capability/capacity; flags affected plans appropriately |
| `submitTeamReport` | Submission ID, own mission/version, brief version, report type, observation time and typed report content | Report ID, pending/accepted/rejected state, owner and current mission/status version; no arbitrary transition or confirmed outcome from narrative |
| `submitFieldReport` | Submission ID, scope/location certainty, observed time, reported needs/count basis or unknown, relevant area/mission refs | Evidence/proposed-event IDs, review owner/state; suspected urgency remains visible; no automatic assessed-area/need-count change |

Team report types include preparation/progress, proposed estimated window, non-arrival/blocked/delay/resource issue and delivery/outcome report. Define permitted values, required fields and authorized review behavior together. A report of an unavailable resource must create visible review attention promptly; an accepted reviewed change holds/revises linked plans and withdraws the old current window. Do not hide the pending problem behind a normal “on time” label.

Resident timing is returned from your friend's own-status operation, not calculated again by your UI. Your mission view and the resident view must agree on the shared mission/assistance version. Transport and medical assistance have independent acceptance/window states.

## Fields and response behavior to freeze together

| Field/convention | Proposed meaning |
|---|---|
| `contractVersion` | Version of this agreed interface; different from record or brief version |
| `submissionId` | Unique identifier for one action. Retrying identical content with the same ID has the same effect/result; reusing it for different content is rejected |
| `expectedVersion` / `inputVersions` | The record or summary/source versions your UI used; backend rechecks before applying an action |
| `areaId`, `scopeId`, `boundaryVersion` | Stable planning area, actual targeted subset and boundary revision; not interchangeable |
| `caseId`, `reportId`, `proposalId`, `missionId`, `teamId`, `resourceId` | Separate stable references; telephone number is not any of these IDs |
| `observedAt`, `receivedAt`, `generatedAt` | Source observation, receipt and summary-generation times, with distinct meanings |
| Times | Proposed format: ISO 8601 UTC timestamps; UI displays local time with timezone. Reference year and valid planning interval remain separate fields |
| Unknown values | Explicit `null` plus reason/status where needed; never substitute zero. Empty list means no matching returned records only when the read itself is complete |
| Quantity | Number or unknown, unit, cohort/scope, period, source/count basis and review state |
| Location | Authorized geometry/reference, reported landmark, accuracy/uncertainty basis and source/time. Missing or ambiguous location has no fabricated pin |
| Arrival window | Start/end, assistance/mission scope, responsible source, basis, update time and current/withdrawn state. Next status-update time is a different field |
| Actor | Established by the authenticated backend context. A `teamId` or client-supplied role does not grant access |
| Result | Outcome, saved reference/version, review state, issues and current affected versions; “saved” is distinct from “approved” |

Read results expose unavailable/stale/partial dependencies as well as available data. The screen cannot infer “no emergency” from a failed read. If input scope, overlap, units or assumptions do not match, the backend returns an unresolved issue rather than an exact gap.

## Synthetic example: the data your planner reads

This is a proposed selected-area briefing at **10:00 Asia/Bangkok**, corresponding to the [wireframe fixture](../design/workflow-wireframe-guide.md#shared-scenario-and-provenance-fixtures). Source geometry and detailed evidence are obtained separately; no real coordinates or imagery are represented. Version numbers below are illustrative.

```json
{
  "contractVersion": "draft-v1",
  "dataMode": "synthetic",
  "areaId": "P-A",
  "boundaryVersion": 1,
  "briefingVersion": 1,
  "generatedAt": "2026-10-11T03:00:00Z",
  "responseMode": {
    "value": "support_in_place",
    "scopeId": "A01",
    "basisId": "AT-A",
    "assessedAt": "2026-10-11T02:30:00Z",
    "reviewState": "reviewed_fixture"
  },
  "exposure": {
    "modeledPeople": 100,
    "referenceYear": 2025,
    "evidenceId": "POP-A",
    "uncertainty": null,
    "uncertaintyReason": "not_supplied",
    "currentOccupancyOutsideTarget": null
  },
  "sourceRefs": ["EXT-A", "DEP-A", "POP-A", "AT-A"],
  "supplyCoverage": {
    "scopeId": "A01",
    "periodStart": "2026-10-10T17:00:00Z",
    "periodEnd": "2026-10-11T17:00:00Z",
    "targetPeople": 80,
    "item": "food_pack",
    "allowancePerPersonPerDay": 1,
    "allowanceBasis": "fictional_scenario_only",
    "requiredPacks": 80,
    "confirmedReceivedUsablePacks": 20,
    "remainingPacks": 60,
    "activeCommittedPacks": 30,
    "unassignedPacks": 30,
    "overlapState": "resolved_in_fixture"
  },
  "medicalNeedState": "no_reviewed_request_for_A01_in_fixture",
  "unknowns": [
    "Current occupancy outside A01",
    "Absence of medical need is not established"
  ],
  "inputVersions": {
    "sourcePackage": 1,
    "assessment": 1,
    "needs": 1,
    "receipts": 1,
    "commitments": 1
  }
}
```

You use `unassignedPacks` for contribution planning, `remainingPacks` for undelivered demand and `activeCommittedPacks` for planned coverage. You show modeled exposure separately. The preview may calculate from the matching inputs, but the backend recalculates before accepting any consequential change. No general flood-to-evacuation classification is derived from this object.

### Example evidence detail for the map

`getAreaEvidence` resolves source references into typed evidence. This illustrative DEP-A response contains the two synthetic sampled depth readings, observed at **09:00 Asia/Bangkok**. The point labels have no supplied geometry; show them in source/list detail without inventing map pins. A real permitted package must supply its agreed geometry format/location basis separately.

```json
{
  "contractVersion": "draft-v1",
  "dataMode": "synthetic",
  "areaId": "P-A",
  "evidenceId": "DEP-A",
  "evidenceVersion": 1,
  "type": "measured_point_depth",
  "sourceLabel": "Synthetic ground-relative observations",
  "observedAt": "2026-10-11T02:00:00Z",
  "retrievedAt": "2026-10-11T03:00:00Z",
  "scopeId": "A01",
  "unit": "m",
  "verticalReference": "local_ground_at_each_sample",
  "uncertainty": null,
  "uncertaintyReason": "not_supplied",
  "availability": "available_metadata",
  "samples": [
    {"sampleId": "DEP-A-1", "value": 0.4, "geometry": null},
    {"sampleId": "DEP-A-2", "value": 0.8, "geometry": null}
  ],
  "limitations": [
    "No supplied sample geometry",
    "No continuous area-depth surface",
    "No safe-access inference"
  ]
}
```

The map can display depth geometry only when actually supplied and permitted. Extent, gauge elevation, forecast and modeled depth need their own distinct types and relevant reference/validity fields. Never turn metadata-only point readings into a shaded depth polygon. Your package definitions and your friend's publication validation must agree on these distinctions.

## Synthetic example: what your planner submits

At **10:05 Asia/Bangkok**, T-R proposes 30 packs. Team stock is 80; payload/access/staging checks remain pending. The UI may recommend a load, but does not reserve stock or establish an arrival promise.

```json
{
  "submissionId": "SUB-PL-A-001",
  "teamId": "T-R",
  "expectedTeamVersion": 1,
  "areaId": "P-A",
  "boundaryVersion": 1,
  "scopeId": "A01",
  "expectedBriefingVersion": 1,
  "inputVersions": {
    "sourcePackage": 1,
    "assessment": 1,
    "needs": 1,
    "receipts": 1,
    "commitments": 1
  },
  "missionType": "relief_supplies",
  "periodStart": "2026-10-10T17:00:00Z",
  "periodEnd": "2026-10-11T17:00:00Z",
  "proposedLoad": [{"item": "food_pack", "quantity": 30, "unit": "pack"}],
  "proposedArrivalWindow": {
    "start": "2026-10-11T06:00:00Z",
    "end": "2026-10-11T07:00:00Z",
    "basis": "team_proposal_not_confirmed"
  },
  "unresolvedChecks": ["payload", "access", "staging"]
}
```

Expected saved response, before coordination review/team acceptance:

```json
{
  "contractVersion": "draft-v1",
  "submissionId": "SUB-PL-A-001",
  "outcome": "saved_pending_review",
  "proposalId": "PL-A",
  "proposalVersion": 1,
  "missionId": null,
  "authoritativeCoverageChanged": false,
  "stockReservationChanged": false,
  "currentUnassignedPacks": 30,
  "currentRemainingPacks": 60,
  "issues": ["payload", "access", "staging"]
}
```

Display **“Proposal submitted; awaiting coordinator review”**. Do not show accepted mission, zero unassigned need, stock 50 or a resident arrival window. Following matching reviewed coordination and team acceptance, planned coverage can change; receipt remains separate. Unknown overlaps/changed assumptions require resolution rather than forcing this arithmetic.

## Synthetic example: your team reports a resource problem

M-01 is the separate transport mission for C-01, accepted by T-S with brief v1 acknowledged. At **10:30 Asia/Bangkok**, S1 becomes unavailable. These IDs do not refer to PL-A.

```json
{
  "submissionId": "SUB-TEAM-01",
  "missionId": "M-01",
  "expectedVersion": 1,
  "briefVersion": 1,
  "reportType": "resource_unavailable",
  "observedAt": "2026-10-11T03:30:00Z",
  "resourceId": "S1",
  "replacementArrivalWindow": null,
  "reportedReason": "Synthetic resource availability failure"
}
```

The first result is a saved, attributed report with review state/owner and current mission version; the UI shows **“Problem reported; awaiting review”** and a timing concern. When the coordinator reviews this synthetic change, the backend applies a held/reassessment state, withdraws the prior 13:00–14:00 current window and exposes replacement time as unknown. The fictional next status update at 11:00 is a separate commitment. Saving brief v2 does not acknowledge it for the team. PL-A and the independent pending medical assistance remain unaffected unless explicitly linked evidence supports another change.

## Errors and screen behavior

Agree stable error codes, regardless of eventual transport. A response includes a safe message and references the caller is permitted to access; no unauthorized “current record” is leaked.

| Proposed outcome/code | Meaning | Your UI behavior |
|---|---|---|
| `saved_pending_review` | Evidence/proposal saved; authoritative state not yet changed | Show submitted/pending and owner; retain current reviewed values |
| `applied` | Authorized change committed | Refresh the affected briefing/team/mission versions; show actual resulting state |
| `VERSION_CONFLICT` | Inputs/record changed after the UI read | Preserve local draft, fetch permitted current data, compare changes and require deliberate resubmission with a new submission ID |
| `VALIDATION_FAILED` | Missing/incompatible scope, unit, time or other required field | Keep draft; show field-specific issues; do not pretend save succeeded |
| `NOT_READY` / `RESOURCE_CONFLICT` | An offer/action cannot proceed under current checks/availability | Show unresolved checks/owner; no accepted assignment/window |
| `PERMISSION_DENIED` / `NOT_AVAILABLE` | Actor cannot retrieve/act on record, or record is unavailable | Show a safe message; no hidden fields/coordinates |
| `SUBMISSION_REUSED` | Same submission ID was sent with different content | Require a new ID for the new intended action; do not merge meanings |
| `DEPENDENCY_UNAVAILABLE` | Required source/service unavailable | Show failed/stale/partial state and preserve useful permitted work |

If a save times out, the outcome is **unknown**, not failed. Query/retry the same submission ID with identical content before creating a new action. The backend must return the original result without duplicating effects. Editing and resubmitting is a new submission, after resolving the prior outcome.

## How both of you work before integration is ready

1. **Agree a small contract version first.** Each partner marks read/write operations as proposed, agreed specification, fixture-only, integrated or verified. “Agreed specification” does not mean it runs.
2. **Friend supplies interface examples.** For each needed operation: input, normal response, pending/unknown/error response, access rules and observable side effects. No actual endpoint URL/auth configuration is promised until selected and authorized.
3. **You supply geometry/source and calculation examples.** Stable area/landmark IDs and boundary/source versions, provenance, unknown/stale states, quantity/capacity assumptions and expected outputs. Source-backed analysis needs its separate verification; synthetic illustrations are labeled.
4. **After implementation authorization, use one replaceable data-access layer.** Your screens call the agreed operations. A local mock may return declared fixture states, and the same boundary can later use the actual backend. Keep mock totals/state transitions aligned with the contract; never claim a mock as a live integration.
5. **Connect early.** First, Friend's reviewed text request becomes a permitted map/list need. Then your proposal reaches coordinator review; an emergency offer reaches your team; acceptance/window reaches resident status. Only then expand channel/layer polish, while required phone/source feasibility is checked from the start.
6. **Run the common failure checks.** Duplicate input, unknown location, stale version, lost save response, resource failure, changed pickup, partial field coverage, denied record and failed layer. Keep the [delivery agreement's acceptance checklist](two-person-delivery-agreement.md#joint-acceptance-checklist) as the shared completion gate.

Development server configuration, actual access method, authentication/test roles, selected datastore, write/review policy details and refresh mechanism are still technical-planning decisions. Your friend should provide the resulting configuration instructions privately where necessary, with no credentials in Git. Neither partner should need the other's personal account login.

## First handoff checklist

| Friend gives you | You give Friend | Both settle |
|---|---|---|
| Agreed read/action names and fields | Area/scope/landmark ID catalogue | Contract version and version-change process |
| Normal/pending/conflict/denied examples | Source/geometry package and provenance | Which actions apply immediately versus require review |
| Permitted team/mission/brief data | Planning rules and expected calculations | Roles, identity, units, periods and unknown handling |
| Saved-result/retry/refresh behavior | Team action/report form requirements | First shared scenario and failure cases |
| Integration status and next dependency | Package status and next dependency | Auth/access, local configuration and datastore later |

When a field/state/meaning changes, propose a before/after example, identify affected screens/calculations and revise both examples together. Do not change published interfaces silently. Both humans review consequential changes under the [working agreement](working-agreement.md). These operation examples are detailed recommendations; human review is needed to freeze the actual contract.

For your first screen, ask your friend to review the **P-A briefing response and proposal submission/response above**, plus the corresponding own-team response. You can then design exactly what your map panel/planner consumes and sends. For your friend's first desk, give them the P-A scope/source references and calculation expectations; they can design review without guessing your fields. This small shared example is the first contract checkpoint, rather than waiting until both complete all their screens.

## Validation

Checks run: five changed/new Markdown files, 45 local links/fragment targets, whitespace and sensitive-pattern scans; all passed. All five JSON examples parse; cross-example area/submission IDs, input versions, quantity arithmetic, unchanged draft coverage/stock and absent depth geometry were checked. `git diff --check` passed; the separate file scans cover the untracked documents. JSON examples are illustrative specifications, not runtime results; no application tests or operational verification ran. No API/client, table/schema, application code, integration or account configuration was created.
