# Requirements and constraints

Status labels: **Accepted** = explicit human request or boundary; **Proposed** = approach needing human approval; **Open** = unresolved. Acceptance here does not authorize implementation or imply feasibility. The [prototype v1 inclusion/deferrals](prototype-scope-v1.md) are human-approved in [decision 0005](../decisions/0005-prototype-scope-proposal.md); operational policy/provider details remain open.

## Accepted requested capabilities

| ID | Capability | Definition still needed |
|---|---|---|
| R1 | Chat intake | Channels, language, identity, clarification and fallback |
| R2 | Inbound telephone calls | **Deferred beyond the prototype (user decision 2026-10-11, [0009 amendments](../decisions/0009-implementation-start-and-technical-direction.md#amendments-user-decisions-later-on-2026-10-11)).** The prototype uses a browser call screen that represents a phone call; it is disclosed as such. A real line needs a telecom provider, number/region, costs, consent and failure handling (TODO). |
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
- **Amended 2026-10-12 (user decisions D21–D22, surge):** AI may file clear non-emergency requests and rank the live priority list directly, but only visibly. Everything it does is labelled "AI-read" or "AI-ranked" with reasons, counted separately from verified numbers, subject to a fixed safety floor, and overridable by humans. Ranking is operational urgency from reported words, not clinical triage. AI never closes requests, promises times or assigns teams.
- **Amended 2026-10-12 (user decisions D25–D29, locations):** a household's exact point (with source and precision) is visible only to the coordinator and the team that has taken that job, and it leaves shared views when the job closes. Shared maps and other roles see the segment and landmark only. Neighbour-reported counts are a floor ("at least N", the largest single report), never summed, and never counted as confirmed. Satellite blind spots are "no satellite data", never dry, and satellite absence never lowers a caller's priority.
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

Selected technologies ([0009](../decisions/0009-implementation-start-and-technical-direction.md), friend confirmation pending): Gemini (Live API and structured output) via Vertex AI, Cloud Run, Firestore, Firebase Authentication/Hosting, Cloud Storage, Google Maps and Earth Engine (offline precompute). Phone access is deferred beyond the prototype: intake uses a browser call screen, labeled as representing a phone call (R2 deferred).

## Open acceptance design

Implementation treatment of the approved v1 inclusion/deferrals for R1–R12; identity merge/unmerge policy; who reviews/approves corrections and receipts; exceptions; clinical handover; flood sources; permissions/retention; recovery; operational owner; telecom feasibility; evidence/evaluation targets. See the open items in [decision 0009](../decisions/0009-implementation-start-and-technical-direction.md). Implementation is authorized from 12 Oct (0009).

## Accepted surge demonstration clarification — 12 Oct 2026

The user requested a connected demonstration with **1,000+ synthetic requests**, including simulated phone-call transcripts and text messages, to show how ReachPoint organizes assistance and builds a useful flood-observation map. This is a replayable scenario, not a requirement to prove production throughput or make 1,000 live AI calls. Browser voice represents a phone call in the prototype; a real telephone line remains deferred under R2.

Human review of every request is not the operating model. Clear routine requests may be automatically filed as **AI-read**, ranked with visible reasons and the deterministic safety floor, and summarized by assistance type and segment. AI-read quantities remain separate from verified quantities. Humans handle uncertainty, conflicting facts, uncertain household matches, overrides and response commitments; qualified personnel handle medical assessment. AI never assigns teams, promises arrival times or closes requests. Preserve original reports and link history; shared phones or nearby addresses do not establish household identity. New danger must never disappear into a duplicate group.

One report may produce both an assistance request and a separate dated water observation. AI-read observations may appear as reported, unverified evidence; distinguish them from coordinator-reviewed observations, team observations, historical satellite extent and modelled depth. Preserve observation time, source, qualitative band or measurement reference, location uncertainty and conflicts. Repeated messages do not establish independent corroboration. No reports means unknown; one observation does not establish the depth of an entire segment. Exact household points remain restricted under D25.

The demonstration must show incoming reports becoming actionable area summaries, urgent attention, an exception queue, team commitments and truthful resident status. Counters distinguish messages, distinct requests, possible duplicates, AI-read records, verified records, exceptions and unmet assistance. Report actual measured simulation results, not invented automation percentages. See [the surge demonstration plan](../planning/surge-demo.md) and [decision 0010](../decisions/0010-surge-demonstration-and-exception-review.md).

### Map-based rescue planning and multi-report water estimates

Accepted user requests, 12 Oct 2026: use the flood map for rescue planning and estimate local water levels from multiple intake reports. Estimates must retain evidence, observation times, measurement reference, uncertainty and conflicts; distinguish estimated ground-relative depth from water-surface/gauge elevation and measured depth. The map connects unmet assistance, suitable team/resources, family groups, coverage gaps and replanning. It must not infer safe routes or hide urgent needs when capacity/evidence is limited. Detailed estimator choices, eligibility thresholds, terrain interpolation and UI are proposed in the [implementation plan](../planning/surge-demo.md), not approved or validated methods. A first local estimator (`local-envelope-v1`, PR #16) is implemented for the demo; it is a prototype rule, not a validated method.

## Current runtime scope — 18 October 2026

The owner approved retiring the classic implementation and making the repository v2-only in
[decision 0012](../decisions/0012-v2-only-repository.md). The judging app uses the overview, family
chat/browser voice and volunteer pages backed by `/api/v2`. Classic desk, review, dispatch, resident
status-token and call APIs are removed; older scope documents remain historical design evidence.
This cleanup preserves v2 behavior and the constraints above. It does not approve new providers,
clinical behavior, spending or deployment. See the [runtime dependency map](../planning/v2-code-map.md).
