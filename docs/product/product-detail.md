# Relief Ledger — detailed product proposal

> Prior design draft: the human requested a workflow rethink after these artifacts. Review the [volunteer planning and emergency workflow](volunteer-workflow-proposal.md) before treating these pages/features/scenario as the current proposal. Artifacts are preserved; no final screens or MVP were accepted.

Date: 2026-10-11. Version: 1.1. **Proposed for human review; no implementation approval.** This is the detailed companion to the [prototype PRD](prototype-prd.md) and [wireframe guide](../design/wireframe-guide.md). Accepted requests and invariants remain in [requirements](requirements.md). Every displayed person, event, location, phone reference and operational datum is synthetic. Brand, permissions and operating policies below are proposals.

## 1. Product definition and design brief

A coordination workspace for a small flood-response desk: understand what is known about the flood and exposed settlements, recognize gaps in assessment, review emergency reports, and coordinate people/resources with accountable next actions.

Primary user: a coordinator working at a desktop under time pressure. Supporting users: an intake operator, resident/proxy reporter and team lead on a phone. No agency, clinical partner, adoption or real-world operating authority is established. Proposed language target: Thai intake with preserved source-language evidence, English coordinator UI/demo, clearly labeled translations. Geography: one bounded fictional locality until lawful local source access is verified.

The most important action is **turn a reviewed information gap or need into an owned next action without hiding uncertainty**. Proposed design direction: calm, clear, practical; grayscale low-fidelity wireframes; persistent source/time labels; dense lists with a focused detail panel; restrained alerts and explicit status text. Final branding, fonts and colors are unselected. These preferences are assumptions submitted for review, not confirmed user brand choices.

Design principles: evidence before interpretation; attention separate from available options; no unknown disguised as zero; continuity across report/case/task; one consequential review at a time. Desktop is the proposed coordinator focus; mobile emphasizes task acknowledgment/reporting and resident text intake. All critical actions need keyboard focus, visible labels, readable contrast, text plus status symbols, and reflow. No hover-only evidence or color-only urgency.

## 2. Navigation and shared elements

Exactly three coordinator destinations: **Situation**, **Contact Center**, **Response**. Case detail is a shared drawer/full-screen detail at narrow widths. Assignment detail stays under Response. Source detail stays under Situation. Medical coordination is a filtered case/referral view, not a separate clinical app. Team mobile task and resident intake are role-specific supporting surfaces.

Shared header: locality/incident, synthetic-data indicator, active role, search (case/task/area/reference), source-health status. Search filters by permissions; no cross-household disclosure through shared phone search. Page filters persist during a shift. Selected object IDs connect map/list/detail. Coordinator can return to the originating queue after review.

No global “victims helped” or “area safe” score. Provisional case IDs are not a proven unique-household count. Display separate counts with definitions: unique reviewed cases, open needs, unassigned tasks, assessment gaps under the chosen scope, building detections, potentially exposed modeled population. Show date/area/method for estimates; missing data uses “Unknown,” not 0. These quantities cannot be added into a universal total.

Map emphasis was requested explicitly after the initial review. Proposed details are in [map experience](map-experience.md): a central Situation map, Contact Center location-review inset, Response map/list view and restricted own-task mobile map. Layer/source/time/uncertainty controls and unlocated-record recovery are part of the proposal; no map provider or functioning integration is selected.

## 3. Roles and proposed permissions

| Role | Can do | Cannot establish |
|---|---|---|
| Resident/proxy | Submit their own report; answer clarification; receive a truthful intake acknowledgment/reference. | Other households' history, review approval, assignment/arrival promises, household identity from caller ID. |
| Intake operator | Enter/clarify reports, correct draft transcription/translation with history, propose case associations, record requested callback preferences. | Approved case facts or task allocation unless also explicitly granted coordinator role. |
| Coordinator | Review evidence/events, establish case links, accept attributed operating assumptions, create/revise tasks and briefs, review observations/outcomes, assign ownership. | Clinical diagnosis/triage or source certainty merely by clicking approve. |
| Team lead | See minimum necessary details for their own assignments; acknowledge a brief version; report own-team/resource availability, position/time, progress and field observations. | Approve own report, see every household, allocate other teams or prove receipt/care by declaring a mission complete. |
| Qualified clinical partner — future | Would need agreed referral acceptance, clinical assessment and care/handover responsibility. | No such partner/protocol exists; prototype may show synthetic referral evidence only. |

No broad administrator UI in the hackathon proposal; role configuration remains a setup dependency. The same human may have multiple explicit roles; the event log records which authority was used. Clinical permission is never inferred from a volunteer skill tag.

## 4. Situation page

**Question:** What is happening, what evidence supports it, and where do we still lack assessment?

Layout: header/filter row; left layer controls; central map with a synchronized list alternative; right selected-area evidence/action panel. Below: compact attention queue. Tabs: Flood evidence / Assessment gaps / Known cases. The map is a spatial aid, not an emergency-routing tool. Unlocated cases remain in the list.

| Feature | Detail and reason | Observable proposed acceptance |
|---|---|---|
| S01 Typed flood evidence | Separate observed extent, station/rain observations, forecasts/warnings and local reports; toggle and inspect each. | Gauge elevation never appears as household depth; forecast never appears as observed flooding. |
| S02 Source/time detail | Publisher, item/version, station/area boundary, observation/acquisition, publication and retrieval times, units/datum, quality and validity. | Today’s fetch of an old item remains old; stale/missing/conflicting labels persist. |
| S03 Building/population context | Reviewed footprint count/filter policy; overlap with sourced extent; separate modeled population/reference year; residence/household/current occupancy unknown unless evidenced. | Building counts are not multiplied by arbitrary family size; missing uncertainty is labeled, not fabricated. |
| S04 Assessment gaps | Evidence-backed potential exposure with no relevant current scoped assessment under an agreed recency policy. | Zero requests cannot establish safety or distress; no-current-assessment creates attention, not automatic priority/dispatch. |
| S05 Area assessment action | Create draft verification task with reason, scope, owner/unknown, access constraints and linked evidence. | No resource leaves task/gap visible; a partial visit records its scope and never clears the whole area. |
| S06 Known-case context | Approved attributed locations and uncertainty, separate case IDs; team reported position/time when permitted. | Shared phone does not merge markers/households; old team position does not imply current proximity or availability. |
| S07 Changes needing review | Compare compatible item versions and explain potential exposure/assignment consequences. | No compatible geometry/time/source means comparison withheld with reason; never infer safe passage. |

Proposed source order after authorization: one approved observation/import for the locality, manual source-reviewed local reports, then optional additional gauges/forecast. Existing footprints/population are candidates, not selected data. Source links may lead to official external pages; import automation/license/cadence require verification. A map basemap is not a live flood observation.

## 5. Contact Center page

**Question:** What is being reported, which case might it concern, and what may the operator accept into the record?

Layout: queue on the left; selected conversation/report in the center; event review on the right. Tabs: All / Calls / Messages / Field reports / Review needed. Medical-reported facts are filterable and labeled “Unassessed.” Sorting is by explicit queue status/time or coordinator choice, not unexplained AI urgency. Provisional alerts never masquerade as clinical prioritization.

| Feature | Detail and reason | Observable proposed acceptance |
|---|---|---|
| C01 Real inbound call | Telephone number reaches an AI clarification flow; processing permission, source-language transcript, interruptions/disconnect and operator follow-up queue. | Normal telephone two-way audio works; browser voice cannot satisfy R2. No call recording by application default. |
| C02 Text/manual/field intake | One in-product text channel and human-entered observation; original channel/observer retained. | Field discovery can create a case only after review; aggregate “several families” creates an area report, not invented household records. |
| C03 Clarification | Ask about who/where/when/what changed and unknown material references. | “We moved; neighbor stayed” remains distinct; model cannot expose another caller’s history. |
| C04 Event-by-event review | Source excerpt, original language + labeled translation, proposed subject/value/time, prior recorded value, ambiguity and edit/approve/reject/duplicate controls. | Only permitted approval changes current records; approving one event does not approve all statements. |
| C05 Case association | Existing case reference/corroborating evidence or provisional new case; unresolved association stays unresolved. | Caller ID/shared number is not identity; no household merge/unmerge UI. Similar content is a candidate duplicate, not an automatic deletion. |
| C06 Change/impact hints | Proposed impact before review, established explicit dependencies afterward. | Changed resident location flags old pickup assumption; it does not rewrite an acknowledged plan. |
| C07 Contact/recovery | Permission/preferences, incomplete report state, attempt outcome, next owner; acknowledge receipt of report truthfully. | Disconnection is not completed intake; no answer is not resolved. Outbound call/SMS and transfers are deferred, not working UI controls. |
| C08 Medical coordination entry | Capture attributed medical facts verbatim, assessment status unknown/unassessed, requested assistance and missing info; assign coordinator review owner. | No diagnosis, prescribing or model clinical score. No acceptance/care assumed from a referral request. |
| C09 Manual fallback | AI unavailable state leaves human-entry/review possible; translation ambiguities remain visible. | AI error cannot approve/close cases. Live human call takeover requires telephony approval/engineering and is deferred; manual record work is not a promise of call transfer. |

Call states: received → permission requested → intake/clarification → proposal awaiting review → acknowledged/intake ended. Branches: permission declined, interrupted/incomplete, technical failure. Permission decline retains no conversation content beyond necessary minimal technical event under a later approved retention policy. No raw audio/video recording UI. Exact provider processing/retention and emergency-service boundary wording require review before real use.

Caller acknowledgment example: “Your report has been received for coordinator review. Assistance and arrival time are not confirmed.” Case reference is not proof of rescue dispatch. Repeat-call verification policy and callback capabilities remain open; prototype uses synthetic caller references, no real personal numbers.

## 6. Response page

**Question:** Who owns the next action, what resources does it require, and does its plan still hold?

Layout: tasks table and selected task detail; side panel for team/resource constraints. Tabs: Assessment / Assistance / Teams & resources / Reassessment. Filters: owner, team, status, area, blocked/unassigned. Reassessment is an overlay; it does not erase underlying mission progress.

| Feature | Detail and reason | Observable proposed acceptance |
|---|---|---|
| RSP01 Task creation | Assessment/verification/assistance task, linked area/case/need, expected scope/outcome, owner, planned pickup/destination and resource dependencies where relevant. | Need survives if no feasible option; assessment task differs from assistance commitment. |
| RSP02 Team/resource roster | Declared capability with source/reviewer, availability, resources, report time/location, commitments. | Unknown capability is not eligible; vehicle V1 failure does not make team T1 unavailable. Individual onboarding, inventory ledger and continuous GPS are deferred. |
| RSP03 Assignment checks | Explicit required skills/resource/access/destination checks; visible pass/unknown/conflict based on evidence. | Proximity alone never establishes suitability; no automatic resource reservation if counts/capacity policy absent. |
| RSP04 Brief/version acknowledgment | What/where/why, source links, known constraints, unresolved checks, owner; acknowledgment tied to version. | v2 needs fresh acknowledgment; v1 progress/history remains. Blank/unknown pickup blocks a transport plan from being presented as ready. |
| RSP05 Progress and observations | Own-team pending reports of not started/in progress/blocked/completed with observation time. | A report awaiting review cannot silently advance the authoritative task; team completion is not household receipt or care. |
| RSP06 Reassessment | Explain affected dependencies; coordinator verifies, revises or cancels with reason and historical linkage. | Old plan geometry remains until explicitly revised; unrelated assignment remains unchanged. |
| RSP07 Assessment result | Scoped observation with boundaries, time, source, partial coverage and discovered needs. | Unreachable result leaves assessment uncertain; one visited building does not establish area completeness. |
| RSP08 Shift handover | Filtered unresolved work: owner, reason, last evidence/contact, constraints, next action. | Unowned task remains visible; AI summary cites records and cannot allocate/close. No broad export/admin suite. Attention items may be deferred with reason/next owner, explicitly resolved against each reason, handed over or reopened by new relevant evidence; completing one verification task never clears unrelated reasons. |

Proposed task progression: draft → offered → acknowledged → active → team completion report awaiting review → reviewed task outcome. Branches: blocked, rejected offer, cancelled with reason. Every reported transition needs attribution; human-reviewed task outcome records completion of the scoped task only. Separate flags: needs reassessment, brief outdated, awaiting current-version acknowledgment. Active task can be reassessed; old acknowledgment is historical and does not authorize a revised action.

## 7. Shared case drawer and medical workflow

Header: provisional/established case reference, reported location/source/time/uncertainty, review/evidence status and owner. Sections: needs, reports/timeline, linked tasks, medical coordination, outcomes. Medical/personal details are restricted to necessary roles; overview list says only “Medical need reported · unassessed,” not sensitive narratives.

Keep independent axes: need resolution (open/partially resolved/resolved with basis); clinical assessment (unassessed/qualified assessment only under future governance); commitment/task progress; and outcome evidence (reported/corroborated/disputed/unknown). A commitment or task transition never substitutes for need resolution or clinical assessment. No universal household completion switch. A shelter arrival/water receipt cannot resolve a different medical need. A reported outcome and confirmed receipt are separate events with actor/source and history. A correction supersedes the earlier operating assumption without deleting it. A coordinator can dispute a reported outcome or correct a mistaken report-to-case link with reason and retained history; this is link correction, not household merge. Unreachable recipients leave outcomes unconfirmed. Corrections must explicitly flag affected derived records/tasks for review rather than silently move approved outcomes to another household.

Medical coordination proposal:

1. Preserve reported symptoms/medical assistance request as attributed facts and unassessed.
2. Coordinator reviews identity/location/contact ambiguity and assigns a referral-review action; no clinical triage by AI.
3. A referral request names intended recipient or unknown, purpose, necessary information and owner. No real recipient exists in the prototype.
4. Separate states: referral proposed, requested, recipient acceptance reported, acceptance corroborated, handover/care reported, care confirmed with evidence. No partner acceptance or care occurs in reality; synthetic demonstrations are labeled.
5. No qualified pathway available → show “Qualified recipient not confirmed,” keep need open and assigned for coordination follow-up. Never label it low urgency.

This is administrative coordination, not medical treatment. Any eventual diagnosis, prescribing, clinical triage or real referral protocol requires qualified governance and human scope approval. No emergency number or response-time promise is invented.

## 8. Supporting mobile surfaces

**Team lead:** own tasks list; detail with brief version, scope, necessary location/evidence, unknowns and acknowledgment; report progress/resource availability/location with observed time; field discovery form. Show last saved and pending review separately. No offline-sync promise: unsent form shows local unsent state only if implemented after approval; persistence/sync is deferred. Team cannot claim “safe route” from a map or accept an outdated brief.

**Resident text:** clear prototype boundary and permission; language choice, message/location reference with uncertainty, conversational clarification, report reference and review acknowledgment. Avoid a multi-page registration form. Phone and chat remain different ingress channels into the same proposed review workflow. No emergency guarantee, identity authentication by phone, or disclosure of another household. No public case lookup in this prototype.

## 9. Entity and state contracts

| Entity | Essential fields and distinctions |
|---|---|
| Source item | ID, type, publisher/observer, original evidence, observation/publication/retrieval time, scope, unit/datum, version, quality and permission. |
| Area | Boundary/version, named scope, source items, exposure estimate/model year/method, last assessment scope/time, gaps and owner. |
| Report | Original language/channel, processing permission, received time, incomplete/completed intake, reporter relation, case candidates, source-linked proposals. |
| Case/need | Separate household reference, identity confidence basis/unknown, current reported location versus planned pickup, distinct needs and evidence, owner. |
| Event proposal | Type/subject/value, source excerpt, observation time/unknown, association evidence, review pending/approved/rejected, evidence reported/corroborated/disputed/unknown, expected record version. |
| Team/resource | Capability source/review, resource identity, reported/operating availability/time, own-team location/time, explicit commitments. |
| Task/brief | Type/scope, case/area/need links, owner, assigned team/resources, explicit dependencies, progress, reassessment overlay, version/acknowledgment. |
| Outcome/referral | Reported versus confirmed basis, recipient/scope, reviewer/source/time, remaining need; referral is not received care. |

These are product contracts, not schema/framework choices. Authorization and deterministic rules own writes/counts/links; AI has permitted evidence retrieval and proposal generation only. Retry identity and review concurrency policy require engineering design. A stale reviewer must reread the current version; draft edits are not shown as saved until acknowledged.

## 10. Failure and edge states

| Trigger | Required experience |
|---|---|
| No sources/no coverage | “No current observation available” + latest known timestamp or unknown; list/tasks remain usable. |
| Data stale/fetch failed | Distinguish observation age from fetch failure; retain history and restrict stale-derived claims. |
| No reports | “No reports received for this scope”; never “no people affected.” |
| Bad units/reference/geometry | Hold comparison/derivation; show missing reason and review action. |
| Household shared phone/similar name | Unresolved association; separate records; no automatic merge. |
| Contradiction/out-of-order update | Show both attributed reports and temporal uncertainty; human chooses operating assumption with reason. |
| Duplicate/retry | Same submission has no second state effect; semantic similarity requires review. |
| Clinical facts/no recipient | Unassessed and qualified recipient unknown; owner/next review visible. |
| AI unavailable/unsupported proposal | Manual workflow; unsupported facts unknown, no authoritative mutation. |
| Call interrupted/permission declined | Preserve consented incomplete content only; truthful outcome, no rescue promise. |
| No team/resource/access confirmation | Unassigned or blocked task; open need/gap stays visible, no safe-route invention. |
| Task report/case outcome differs | Reported task completion does not close need; remaining needs stay visible. |
| Brief changed/concurrent approval | Outdated label, version check and rereview; acknowledgment tied to exact version. |
| Restricted role | Minimum necessary data; explicit denied action with no underlying data leakage. |
| Reset scenario | Authorized synthetic reset; evaluation logs preserved; no deletion of project files. |

## 11. Scope proposal and rationale

**Proposed hackathon core:** one bounded locality, source-labeled flood/footprint/population fixture, an area assessment gap with unchanged-area control, field/proxy text intake, real inbound call, event review/case association, restricted team task view, explicit resources/dependencies, one revised brief, administrative medical-status example and independent need outcomes.

**Conditional data option:** one lawful source-backed extent/footprint import with reproducible counts and original dates. Real data analysis would require separate authorization and suitability review; synthetic operational records remain mandatory. A genuine observed overlay cannot be presented as synthetic evidence of a historical household. If access fails, keep a labeled synthetic fixture; disclose that it demonstrates workflow rather than working satellite estimation or live R8/R9.

**Later:** live multi-source ingestion, custom flood/depth/building models, calibrated occupancy estimates, multi-agency integration, continuous GPS, offline sync, outbound contact/call transfer, clinical workflows, logistics optimization, automatic dispatch, broad individual volunteer onboarding/admin, household merge/unmerge and public reporting. These remain accepted-request definition gaps or deferred proposals, not denied user goals.

Expanded integrated scope estimate: **15–20 person-days** before a reliable presentation; lean fixed-import/synthetic workflow: **11–14 person-days**, both unvalidated estimates. Two people with six full working days provide roughly 12 person-days before interruptions. Therefore scope is tight even with cuts; no delivery guarantee. First authorized day time-box phone access/audio and source access. If blocked, seek an explicit scope change early rather than consuming UI time. Keep evaluation and presentation time protected. Do not spend the deadline day assuming an unverified cutoff.

Suggested lean allocation ranges: telephone 1.5–2; reviewed records/intake 2; fixed situation/assessment 1.5–2; response/team/dependencies 1.5–2; coordinator surfaces 1.5–2; evaluation 1.5–2; authorized deployment/materials 1.5–2. Ownership, true availability, model/API/provider/cost and final cut decisions remain open. No package/paid service is selected.

## 12. Demo and validation proposal

One integrated sequence: A potential-exposure gap with no calls → human-owned assessment → reviewed field discovery of H5 → household phone clarification → reviewed assistance plan → V1 unavailable affects linked plan; M2 unaffected → coordinator verification/revised brief and current-version acknowledgment → task outcome versus remaining medical need.

All transitions use fixtures defined in [demo scenario](demo-scenario.md). Aim at 170 seconds, prioritizing one real AI clarification plus visible review/impact. Editing can shorten waits but must disclose cuts and cannot substitute prerecorded scripted success for implemented behavior. No clinical care or local flood forecast is claimed. Prototype demo and integration evaluation are separate activities.

Retain the base [evaluation plan](prototype-evaluation.md); extension cases require frozen labels/effort allocation. Proposed reliability gates: no wrong-household merge/unauthorized mutation/duplicate application/premature closure; exact dependencies; 90% precision/recall on answerable held-out proposals; 10 controlled real calls with at least 9 completed intakes and actual latency reporting. Add exposure/gap tests only if that analysis is implemented. Synthetic tests cannot prove population coverage, field readiness, rescued lives, adoption or comparative human speedup.

## 13. Review decisions

Review these concrete proposals next: three-page navigation and role split; integrated demo; minimum R1–R9 treatment; medical boundaries; conditional real-data versus synthetic fixture; workload/cuts; phone geography/account owner/budget. No confirmation is recorded yet. Implementation, provider/model/framework selection, purchases, deployment, public repository and submission require their own human authorization.
