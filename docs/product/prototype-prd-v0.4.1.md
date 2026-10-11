> Historical draft. Superseded for current discovery by the volunteer-workflow correction and [current PRD](prototype-prd.md). No final MVP was approved.

# Relief Ledger prototype PRD

Version: 0.4.1. Date: 2026-10-11. **DRAFT — human scope approval pending.** Consolidates the latest product discussion into a three-page proposal. [Detailed specification](product-detail.md), [wireframe guide](../design/wireframe-guide.md), [synthetic demo](demo-scenario.md), [evaluation](prototype-evaluation.md), [accepted requirements](requirements.md) and [sources](../research/sources.md) support review.

This is design/documentation only. Static wireframes are explicitly requested review artifacts, not functioning product screens, implementation, clinical governance or authority to purchase/deploy/publish. No framework, telecom provider, model, database, runtime region or final MVP has been selected. Historical [v0.3](prototype-prd-v0.3.md) is retained; its narrower workload and review scores do not apply to v0.4.

## Product thesis

Help a flood-response coordinator identify areas lacking assessment, review emergency reports and keep response plans current as information and resources change. The memorable proposed workflow is **unassessed area → reviewed discovery → emergency intake → owned response → precise reassessment**. Incoming requests cannot represent all people needing help. Exposure estimates are not confirmed needs, and unavailable resources do not erase needs.

Primary user: small desk coordinator on desktop; supporting intake operator, resident/proxy and team lead on mobile. Thai intake and English operator/demo interface are proposed. No partner, local demand, adoption, real flood feed or clinical service is validated.

## Proposed pages

| Page | Primary decision | Main features |
|---|---|---|
| Situation | Where is evidence changing, and where have we not assessed? | Typed flood evidence; footprint and separate population exposure; scoped assessment gaps; case/map/list context; sources/times/unknowns. |
| Contact Center | What was reported and what may enter the operating record? | Real telephone/text/field intake; clarification; original/labeled translated evidence; event-by-event review; case association; incomplete/manual states. |
| Response | Who owns the next action and does the plan still hold? | Assessment/assistance tasks; team/resources; explicit checks/dependencies; progress and reassessment; versioned brief/acknowledgment. |

Shared case drawer preserves separate needs, sources, identity/location uncertainty, task reports and confirmed outcomes. Medical coordination is reported facts/unassessed/referral tracking with governance unavailable; no autonomous diagnosis, prescribing or triage. Team mobile shows minimum necessary own-task details. Resident text is a supporting surface, not a fourth coordinator page.

The human explicitly requested map emphasis after the initial wireframe review. [Map experience](map-experience.md) proposes a central Situation map, Contact Center location inset and Response map/list view with source/time/uncertainty labels. The expanded static map drawings are on pages 10–11. No provider, live feed, route generation or continuous GPS is selected.

## Requested capabilities and proposed prototype treatment

| Request | Proposed inclusion | Explicit limit |
|---|---|---|
| R1 Chat | One in-product text/manual field update flow. | No LINE/WhatsApp/social integration. |
| R2 Telephone | Real controlled inbound two-way call and clarification, reviewable synthetic transcript. | Suitable account/number/audio gate; browser voice does not satisfy R2. Outbound calls and live operator transfer deferred. |
| R3 Operations | Situation, Contact Center and Response. | One desk/locality, no multi-agency admin suite. |
| R4 Household map | Central map workspace plus linked location/task views; synthetic reviewed reported locations, uncertainty and list alternative. | Unknown location stays in list; no public beneficiary map. |
| R5 Volunteers | Own-team reported position/time and manual availability. | Continuous GPS and offline sync deferred; proximity is not suitability. |
| R6 Resources | Small team/vehicle roster, capability evidence and explicit assignment dependencies. | Broad inventory/optimization/onboarding deferred. |
| R7 Medical coordination | Reported need, unassessed status, owner and synthetic referral states. | Qualified recipient/protocol unconfirmed; no care service or clinical decision. |
| R8 Flood context | Typed timestamped source fixture/local reports; conditional approved observational import. | No exact depth everywhere or live multi-feed guarantee; gauge/extent/forecast are distinct. |
| R9 Satellite estimates | Fixed footprint/exposure and separate population fixture; conditional source-backed import. | Buildings ≠ households/current occupancy; no custom detector or invented victim count. |

All deferrals/fallbacks are scope proposals needing human agreement, not amendments to accepted requests. Data analysis on real public geographic sources also needs separate authorization/suitability review. Operational records and medical examples remain synthetic.

## Workflow and authority

1. Source-labeled potential exposure plus absent relevant assessment proposes area attention under an explicit scoped/recency policy; silence alone proves nothing.
2. Coordinator assigns an assessment action subject to resource/access checks. Field observation produces a report; partial coverage remains partial.
3. Phone/text clarification proposes events and case association. Shared phone is not household identity.
4. Permitted reviewer accepts attributed reports against current versions; review approval and evidence corroboration stay separate. Each material event can have a different decision.
5. Reviewed events change current reported facts. Explicit dependency checks flag plans; they do not overwrite planned pickup, mission progress or acknowledgment history.
6. Coordinator verifies/revises/holds an action with reason/owner. New brief version needs fresh acknowledgment; no confirmed resource means an open need and blocked/unassigned task.
7. Task outcome, reported delivery, confirmed receipt, referral and confirmed care stay separate. Unknown/unreachable is never complete.

AI contribution: source-language clarification, evidence-linked proposals and missing questions. Geometry/counts, permissions, state transitions and explicit impact checks remain deterministic. Compare against a good structured script and extraction-only baseline; generic overlays/briefs are supporting features.

## Acceptance and evidence

The detailed feature IDs S01–S07, C01–C09 and RSP01–RSP08 are in [product detail](product-detail.md). Proposal gates retain zero identity/state/permission invariant failures, exact explicit dependency sets, at least 90% precision/recall on answerable held-out proposed changes, and 10 real controlled phone calls with at least 9 complete intakes. Report actual latency and failures; three-second response target is aspirational. No tests have run.

Add scoped area/footprint tests only if implemented: stale/missing/unknown source; frozen overlap rules; no invented households/occupancy; partial versus complete-scope assessment; unchanged-area/assignment controls; unreachable check. The base [evaluation protocol](prototype-evaluation.md) remains proposed and fixtures unrun. A tiny synthetic comparison cannot establish actual population coverage, lives saved, adoption or field readiness; comparative human speedup remains untested.

## Conditional delivery and scope gates

Expanded scope rough estimate: 15–20 person-days; deliberately reduced fixed-import/synthetic version: 11–14, subject to immediate phone/data availability. These are planning judgments, not measured effort or delivery guarantees. The earlier 12 person-day allocation excluded the new scope. Two people over six full days have roughly 12 person-days before interruptions; agree cuts and protect evaluation/presentation.

After separate implementation approval: first day time-box real phone and one bounded source package; next complete source→proposal→review→impact before map polish; midpoint freeze scenarios/events; final two days protect evaluation and authorized deployment/materials. Failed gates require explicit scope revision. Google flood API access is waitlisted; the researched Twilio streaming route cannot rely on a trial account. Sources, licenses, account owner, spend ceiling and current Google model/API/region/quota remain open. No paid services enabled.

## Review package and next decisions

Review navigation, feature inclusion/deferrals, phone/data feasibility, medical boundary, demo fixture, workload and role authority. Then approve/revise the smallest coherent scope. Implementation, paid services, infrastructure, publication and submission need explicit authorization. No approved final MVP decision exists.

Independent read-only workflow and scope reviews informed this draft. Findings incorporated: event-level review; current location versus pickup; precise resource dependencies; identity/count limits; separate assessment action/knowledge; clinical governance unavailable; revised workload and shorter integrated demo. Static wireframes and this consolidated draft require human review. Validation results are recorded in the [wireframe guide](../design/wireframe-guide.md); no application tests, calls or model evaluations have run.
