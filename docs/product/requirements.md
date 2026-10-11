# Requirements and constraints

Status labels: **Accepted** = explicit human request or boundary; **Proposed** = approach needing human approval; **Open** = unresolved. Acceptance here does not authorize implementation or imply feasibility. The [prototype v1 inclusion/deferrals](prototype-scope-v1.md) are human-approved in [decision 0005](../decisions/0005-prototype-scope-proposal.md); operational policy/provider details remain open.

## Accepted requested capabilities

| ID | Capability | Definition still needed |
|---|---|---|
| R1 | Chat intake | Channels, language, identity, clarification and fallback |
| R2 | Inbound telephone calls | Real telephone access; telecom provider, number/region, costs, consent and failures. Browser voice chat is not equivalent. |
| R3 | Operations dashboard | Decisions, review roles, shift handover and stale information |
| R4 | Household needs map | Identity, location uncertainty and visibility controls |
| R5 | Volunteer locations and updates | Source, freshness, permission and recovery |
| R6 | Team/resource management | Capacity, inventory and commitments |
| R7 | Medical aid coordination | Qualified responsibilities and partner/protocol; no autonomous clinical decisions |
| R8 | Flood height/depth context by area | Measurement type, provenance, units, reference and uncertainty |
| R9 | Satellite-informed building and population exposure estimates | Requested 2026-10-11; geography, image/footprint source and date, building versus residence/household distinction, population method and uncertainty, validation and MVP feasibility. No implementation approval. |
| R10 | Daily area/mission and capacity planning | Requested in volunteer-workflow correction: explain where help is needed, support-in-place versus evacuation needs, what/how much to bring, evacuation capacity and required capabilities. Team leaders plan routine trips; coordinators assign emergencies. Target population, assessment/coverage basis, mission types, assumptions, approval and priorities need definition. |
| R11 | Resident assistance status and timing | Own-request progress and truthful help timing; team acceptance, estimated windows, unknown/delayed states, channel, secure reference and update authority need definition. |
| R12 | Emergency validation and allocation | Coordinator validates operational reports and allocates suitable emergency responders. Clinical urgency and rescue decisions require appropriate qualified governance; no real protocol/partner is approved. |

## Accepted semantic constraints

- Separate need, review status, commitment, task progress, delivery report, confirmed receipt, medical referral and confirmed care/handover.
- Promised aid is not received aid. Partial delivery leaves the remainder open; water delivery cannot close medical needs; referral cannot prove received care.
- Shared phones do not identify households. Unknown stays unknown. Corrections retain history. Repeated submissions must not double-count.
- Calculate quantities from approved records, not AI narrative. Keep inventory available, reserved, issued and confirmed-received concepts separate.
- Volunteer positions retain source and freshness. Area summaries count unique households, not messages.
- Medical intake captures reported facts and clarification for qualified review. Unassessed is not low urgency. No diagnosis, prescribing, autonomous clinical triage, approved protocol or clinical partnership exists.
- Flood ground-relative depth, qualitative reports, river-gauge elevation, satellite extent and forecasts are distinct. Preserve time, source, units, reference and location uncertainty. No verified live feed; no fabricated continuous depth or safe routes.
- Separate attention needs from feasible response options. Scarce resources must not hide urgent needs; avoid unexplained AI urgency scores.
- AI proposals do not silently become authoritative. Deterministic rules enforce quantities, permissions and states; qualified personnel govern clinical decisions.

- Satellite-derived building detections, estimated residential buildings, households, modeled population exposure and confirmed needs are distinct. Imagery does not establish current occupancy or people trapped. Retain source/date/resolution, assumptions and uncertainty; unknown stays unknown.

## Accepted synthetic quantity example

| State | Requested | Confirmed received | Active commitment | Outstanding | Unassigned |
|---|---:|---:|---:|---:|---:|
| Initial | 20 | 8 | 12 | 12 | 0 |
| Approved correction | 20 | 6 | 12 | 14 | 2 |

For this example, outstanding = requested − approved receipt; unassigned = outstanding − active commitment. Overdelivery, overlapping commitments, cancellations and unit conversions still need explicit policies; do not extrapolate this example into a complete implementation rule.

## Proposed approaches

AI conversational clarification, case-history retrieval, contradiction interpretation, suggested report relationships, evidence-linked proposed events, unresolved-issue explanations, handovers and suggested next actions. A reviewed event history is promising but not a final storage architecture.

Selected technologies ([0009](../decisions/0009-implementation-start-and-technical-direction.md), friend confirmation pending): Gemini (Live API and structured output) via Vertex AI, Cloud Run, Firestore, Firebase Authentication/Hosting, Cloud Storage, Google Maps and Earth Engine (offline precompute). Phone access still needs telecom infrastructure. Until the R2 gate passes, intake is browser voice, labeled as such; that does not satisfy R2.

## Open acceptance design

Implementation treatment of the approved v1 inclusion/deferrals for R1–R12; identity merge/unmerge policy; who reviews/approves corrections and receipts; exceptions; clinical handover; flood sources; permissions/retention; recovery; operational owner; telecom feasibility; evidence/evaluation targets. See [open questions](open-questions.md). Product implementation remains unauthorized.
