> Historical proposal snapshot, 2026-10-11. Current proposal: [prototype PRD](prototype-prd.md). This version is not implementation authority.

# Relief Ledger prototype PRD

Version: 0.3. Date: 2026-10-11. Status: **DRAFT — proposed scope, human approval pending**.

Prepared using office-hours Builder mode. Branch: `codex/project-foundation`. Remote repository not configured. Incorporates the user's rejection of quantity accounting as the central wow factor. Supersedes earlier demo recommendations in the [deep-dive](../research/relief-ledger-deep-dive.md); continues the [operational rethink](../research/relief-ledger-operational-rethink.md).

This document authorizes no implementation, procurement, deployment, publication or submission. [Accepted requirements](requirements.md) remain authoritative. All prototype people, cases, geography, source notices and operational actions must be synthetic. A tested prototype would demonstrate software behavior, not field readiness or disaster outcomes.

## 1. Product thesis

**Relief Ledger helps a response coordinator turn changing calls and messages into a current, evidence-linked view of which response plans need reassessment.**

Incoming reports do not represent everyone who needs help. No report is not evidence of no need; area assessment and household requests must remain separate. See the proposed extension in section 16.

The coordinator's job is to decide what needs attention, what can be done with verified available resources, who owns the next action and what information is missing. Success is a better-supported decision under constraints, not fulfilling every requested quantity.

The prototype's memorable moment: a resident's update changes a pickup assumption, a team's required vehicle becomes unavailable, and a destination closes. Relief Ledger shows which plans are affected, which remain unchanged and why. It asks the missing question before generating a reassessment brief. The human owns the decision.

## 2. Evidence, inference and unresolved premises

| Basis | Product implication | Limit |
|---|---|---|
| Thaiwater Hat Yai retrospective and government response briefing (O1–O2) describe coordination, priorities and resource constraints. | Show current operational assumptions, ownership and constraints together. | Neither validates Relief Ledger or a particular local desk's demand. |
| Public flood-response issue #37 raises stale-case concerns (O3). | Keep current-contact evidence and unresolved uncertainty visible. | One contributor concern is not a prevalence estimate or proof of another product's defect. |
| Public Thai project describes Gemini intake/review/deduplication (O4). | Those features are supporting capabilities, not our headline innovation. | Runtime and deployment untested. |
| INSARAG coordination documentation describes assignments and review (P1). | Use explicit assignments, dependencies and accountable reviewers. | USAR worksite guidance is not our household/flood SOP. |
| Telephone and Google documentation describe relevant building blocks (P3–P10). | Investigate a real inbound call and reviewable AI proposals. | Number availability, integration, language quality, quotas, region and complete cost unverified. |

See the [source register](../research/sources.md) for URLs, access dates and limitations, and [feasibility research](../research/prototype-feasibility.md) for the telephone gates.

Unproven premises: a desk has this recurring problem; its information is sufficiently linkable; humans can review proposals quickly; conversation improves on a good script; an operator will adopt and maintain the product. The demo and evaluation test selected technical hypotheses, not all these premises.

## 3. Users, setting and authority

Proposed setting: a small coordination desk during a flood response, receiving reports from residents and teams. Prototype assumption: one coordinator, two simulated team users, Thai resident intake and English coordinator interface/submission. Names, case references and location labels are fictional. Preserve original-language evidence; English translations are clearly labeled and reviewable.

| Role | Allowed prototype actions | Authority boundary |
|---|---|---|
| Resident / person reporting for others | Submit a report; clarify their own statement; state contact preference. | Caller ID does not authenticate a household or authorize access to prior callers' data. |
| Team user | View assigned brief; acknowledge its current version; report availability or task progress for their own team. | Reports do not approve themselves or prove household receipt. Access limited to necessary assignment details. |
| Coordinator | Review proposals, link reports to cases, approve current operating assumptions, revise assignment briefs, assign verification work and record decisions. | Prototype permission role, not a claim of real clinical, rescue or government authority. |

Approval means “accept this attributed report into the operating record,” unless a separate verification basis is supplied. It does not turn every caller assertion into a verified fact. Use two independent fields: review status (pending/approved/rejected) and evidence status (reported/corroborated/disputed/unknown). A checked fictional issuer notice is corroborated only through an explicit simulated operator/source check; the prototype does not establish actual authority. “Verified” in explanatory prose means a recorded corroboration basis, not a fifth evidence status. An established assignment link can confirm relevance without confirming the underlying report's truth.

## 4. Scope mapped to accepted requests

“Include” and “defer” below are proposals, not amendments to accepted requests.

| Request | Proposed prototype treatment | Reason |
|---|---|---|
| R1 Chat | Include one in-product text intake and a team update form. No LINE/WhatsApp integration. | Covers the same proposal/review flow without platform onboarding. |
| R2 Inbound telephone | Include a real two-way telephone call, subject to an early feasibility gate. | Accessible resident interaction and visible AI contribution; browser voice is not acceptance. |
| R3 Operations | Include current reports and changed assignments, owners and unknowns. | Centers the coordinator's next decision. |
| R4 Household map | Include a small context map of approved synthetic locations with uncertainty and source/time. | Helps distinguish locations; no route or flood-depth inference. If mapping cannot be licensed/budgeted, seek a scoped deferral rather than silently replacing it. |
| R5 Volunteer positions | Include manually reported team location and timestamp; defer continuous GPS tracking. | Sufficient context for the bounded workflow. Proximity is not suitability. |
| R6 Teams/resources | Include verified scenario capabilities, availability and assignment ownership; defer inventory administration and optimization. | Exposes whether a response option meets known constraints without building a logistics suite. |
| R7 Medical aid | Preserve reported medical needs as unassessed, with a coordinator review task; defer clinical service, diagnosis, prescribing and clinical prioritization. | No qualified partner or governance exists. Referral and confirmed care remain separate if represented. |
| R8 Flood context | Defer live ingestion/depth modeling; show a clearly synthetic, typed flood-context card with source, observation time, units/reference or explicit unknowns. | Demonstrates provenance semantics, not a functioning flood feed or complete R8. Human approval of this deferral is required. |
| R9 Satellite estimates | Proposed area-level satellite/footprint layer, building counts and separate population exposure estimates; synthetic fixtures initially, actual ingestion subject to scope/feasibility approval. | Helps surface settlements absent from intake; does not identify occupied homes, households or confirmed assistance needs. |

Exclude autonomous dispatch, rescue instructions, urgency prediction, route safety, social scraping, outbound calls/SMS, household merge/unmerge, public incident reporting, real resident data, broad organization administration and multi-agency integrations. Reports can be linked to existing cases by a coordinator; separate household records are not merged in this prototype.

## 5. Essential experience and pages

| Surface | Decision supported | Required contents and reason |
|---|---|---|
| Operations | What needs my attention? | Separate changes awaiting review, reviewed changes with established assignment links, and needs lacking an owner/confirmed option. List and linked map; source/freshness labels. Review and evidence status remain separate. |
| Review | What did this report actually change? | Original excerpt, current recorded assumption, proposed event and case association, ambiguity, supporting sources, edit/approve/reject/mark duplicate. One event per material change so approval is explicit. |
| Response | What are we committed to doing, and does that plan still hold? | Assignment, team/resources, pickup/destination dependencies, brief version, owner, acknowledgment, progress and reassessment reason. Show known constraints and missing checks. |
| Case detail drawer | What is this household's current reported situation? | Timeline, identity/location uncertainty, separate needs/outcomes, linked assignments and corrections. Accessible from all three coordinator pages; no fourth navigation destination needed. |
| Resident intake | What is the desk being told? | Phone or text; clear prototype scope, permission to process/store a synthetic transcript, focused clarification and a truthful “awaiting coordinator review” acknowledgment. No promised arrival. |
| Team task view | What changed in my assignment? | Restricted assignment brief, current version, acknowledgment and own-team update fields. This is a compact task surface, not a separate team-management application. |

Use readable operational language such as “Reported change,” “Needs verification,” “Awaiting team acknowledgment” and “No confirmed option.” Do not use green “safe,” a completion percentage or quantity coverage as a proxy for overall household resolution. Use keyboard-accessible controls, explicit text/status icons and large tap targets; color alone must not communicate state.

## 6. Core workflow

1. **Receive:** retain source ID, channel, observed/reported time, received time, language and consent. An interrupted intake remains an incomplete report; it does not change a case.
2. **Clarify:** AI identifies material statements and asks a question when subject, location, event or timing is ambiguous. It may use authorized case references but must not disclose another household's details.
3. **Propose:** create evidence-linked events and candidate associations. Unreviewed events appear in the attention queue with provisional impact hints. No operational record, assignment or receipt changes yet.
4. **Review:** coordinator approves, edits or rejects each event against the current record version. Conflicts remain visible; stale simultaneous approvals require rereading current state.
5. **Find dependencies:** after approval, deterministic checks identify assignments explicitly linked to the changed household pickup, destination or team/resource availability. These get a “needs reassessment” overlay; assignment progress is preserved. Possible links inferred by AI remain separately reviewable.
6. **Brief:** generate “what changed / affected assignments / unresolved facts / next checks / owner” from reviewed records. Every consequential statement links to evidence. Unknowns are not replaced with recommendations that assume facts.
7. **Decide and acknowledge:** coordinator assigns a verification action or revises a brief. A new brief version needs fresh team acknowledgment. Earlier acknowledgment remains historical. Lack of acknowledgment is visible and does not imply acceptance.

No step auto-closes a need because time passed, the resident moved, a team accepted, or no resource is available. A response may be constrained or deferred with a stated reason while the need remains open. Quantity and outcome semantics from the requirements stay intact beneath this workflow.

## 7. Functional acceptance criteria

These are proposed future acceptance criteria; no implementation or tests have run.

| ID | Requirement | Observable acceptance |
|---|---|---|
| F01 | Equivalent phone/text intake | A real telephone caller and text reporter each create a reviewable source report. Phone has two-way audio and one interruption; original evidence is available. Browser microphone alone fails R2. |
| F02 | Ambiguity and identity | “We moved; my neighbor stayed” produces distinct clarification/proposals. Same phone does not merge households. Unresolved case association remains unresolved. |
| F03 | Evidence-linked proposals | Each material proposed change has event type, subject candidate, source excerpt/offset, event time or unknown, received time and attribution. Unsupported values stay unknown. |
| F04 | Review authority | Only coordinator approval changes current records; edits/rejections and previous values remain in history. Team/resident accounts cannot approve their own reports or alter another team's assignments. |
| F05 | Repeat and temporal handling | Same submission ID has no second state effect. Similar messages with different IDs need semantic duplicate review. Older observations do not silently overwrite newer operating assumptions; conflicting timing is surfaced. |
| F06 | Precise impact | On the demo fixture, vehicle V1 unavailability affects M1/M3 because both explicitly require V1; destination D1 closure affects M1. Their union affects only M1/M3. M2 stays unchanged. T1 itself is not declared unavailable. Replaying events does not duplicate flags. |
| F07 | Current reassessment brief | Brief identifies changes, affected assignment IDs, known constraints, unknowns and proposed checks with citations. If underlying versions change, an earlier brief is marked outdated before it can be approved. |
| F08 | Ownership and acknowledgment | Coordinator can assign a verification action and revise a brief. Team acknowledgment names the brief version; a revised brief returns to awaiting acknowledgment without erasing previous progress/history. |
| F09 | Scarcity and boundaries | “No confirmed available team” leaves the need visible. No autonomous urgency, medical, safe-route or dispatch assertion. Medical facts remain unassessed until qualified review outside this prototype. |
| F10 | Context fidelity | Map locations and team positions carry source/time/uncertainty; an unlocated case remains in the list. Flood context distinguishes measurement types and is labeled synthetic; no invented continuous surface. |
| F11 | Recovery and concurrent review | Disconnect preserves consented received report content with an incomplete label. Retry is idempotent. A stale reviewer write is rejected/re-reviewed, not silently accepted. AI failure leaves manual intake/review available. |
| F12 | Minimal exposure and repeatability | No raw audio retention by the application; consented synthetic transcripts only. Restricted task access is checked. A controlled reset restores the fixture without overwriting the evaluation log. Product reset does not delete project files. |

## 8. Minimal domain contracts, not a database choice

- **Source report:** source ID, channel, consent, original language/text, transcript segment offsets, received time, event/observation time if known, reporter attribution and completeness. Ingestion identity is not household identity.
- **Case:** independent provisional ID, reported identity/location and confidence basis, contact permission, last contact, separate needs and outcomes. Unknown quantity and location are allowed.
- **Proposed/reviewed event:** subject reference or unresolved candidate, typed change, old/new claim, source links, review decision/actor/time, verification basis and supersession history.
- **Team/resource:** scenario-declared capabilities with reviewer/source, availability, reported location/time and commitments. Unknown capability is not a passed constraint.
- **Assignment:** ID, linked case/pickup/destination/team/resource IDs, human-defined required capabilities, owner, planned sequence, progress and brief version. Dependencies must be explicit for F06; free-text omissions remain a limitation.
- **Attention item:** reason, proposed/established dependency link, affected entity/assignment, owner, status and evidence. An established link does not corroborate the underlying report. Keep reassessment separate from mission progress.

Prototype event types: reported location change, situation/need update, team/resource availability change, destination availability change and assignment progress report. Quantity correction can be retained for invariant tests. No model-generated arbitrary state transition is allowed.

Proposed attention order is by explicit human-set attention category, then oldest unhandled item. Categories group work; they do not clinically rank residents. A freshness label always shows elapsed time; use configurable scenario thresholds for stale labels, never automatic case expiry. Final local thresholds require operator policy.

## 9. One synthetic demo, with a negative control

Fixture: four households (H1–H4), two teams (T1/T2), two vehicles (V1/V2), two destinations (D1/D2), three assignments and one unassigned need. All location labels/coordinates must be synthetic and visibly marked. No actual field operations occur.

| Assignment | Initial plan/state | Required capability and exact dependencies |
|---|---|---|
| M1 | H1 assistance plan, pickup L1, destination D1; T1 acknowledged brief v1; not started. | Scenario road-vehicle transport capability; H1.pickup, T1.availability, V1.availability, D1.acceptance. |
| M2 | H2 assistance plan, pickup L2, destination D2; T2 acknowledged brief v1; not started. | Same capability; H2.pickup, T2.availability, V2.availability, D2.acceptance. |
| M3 | H3 draft later task, pickup L4, destination D2; proposed T1/V1 after M1; unaccepted and not active. | Same capability; H3.pickup, T1.availability, V1.availability, D2.acceptance. Capacity/time confirmation pending. |

Initial evidence: case pickups are approved, attributed resident reports; T1/T2 capability and V1/V2 availability are corroborated synthetic scenario facts with operator-check sources at scenario minute 0. D1/D2 acceptance has corroborated fictional issuer sources. This does not certify route passability. H4 is a different household in the same coarse area L1, with its own reported need and provisional identity; it is not at the same verified street address. L3 is the resident's clarified new temporary location, “Harbor Community Building,” separate from destinations D1/D2.

H4 has an unresolved need with no confirmed resource/owner; it remains visible throughout. T1 is not double-booked: M3 is a sequential draft and capacity/time confirmation remains outstanding. Capabilities and recipient/destination acceptance are scenario data, not AI inferences.

Resident call: “I'm calling for the household in case H1. We moved to the community building. My neighbor H4 is still at the original place.” The assistant asks for the specific new location/reference and who “we” includes. It proposes an H1 location update and preserves H4 separately. Review records it as reported; no receipt or safety is inferred.

Then an authenticated T1 user selects V1 and reports it unavailable, stating that M1 has not started. The approved update has evidence status reported; it changes the V1 operating assumption, not the entire team's availability. A fictional issuer's checked notice says D1 no longer accepts arrivals, effective at the scenario time; its source-check basis is corroborated. Each event is independently reviewed.

Expected result: M1 has three reassessment reasons (H1 pickup L1→L3, V1 unavailable, D1 not accepting); M3 is affected by V1 availability; M2 has none. Original assignment progress and previous acknowledgments remain unchanged under the reassessment overlay. H4 remains unassigned. If no alternative satisfies verified prerequisites, show that plainly. The coordinator creates a verification task about destination alternatives and ownership, rather than approving an unsupported transport plan. Team acknowledgment of the new brief is visible separately from mission start or completion.

Suggested video timing: 0–20 seconds show the plan/unknowns; 20–65 actual inbound call and clarification; 65–95 evidence review; 95–125 team/notice changes and precise impacts; 125–155 coordinator action/acknowledgment; 155–170 actual evaluation result and limitations. Target **170 seconds**, strictly under three minutes. A live model interaction cannot be replaced by edited scripted success; disclose cuts, fixture inputs and any recordings. See [hackathon constraints](../hackathon.md).

## 10. Evaluation and product success

Use the [evaluation plan](prototype-evaluation.md). Product hypothesis: help a coordinator identify affected plans and produce an accurate reassessment with less effort. The current evaluable technical claim is accurate interpretation and reassessment on synthetic cases; no result has been measured. Measure interpretation and workflow separately so deterministic dependency checks are not presented as model reasoning.

Proposed prototype gates and a separate future efficiency target, set before measurement:

- Correct reviewed state, no unauthorized writes, wrong-household merge, duplicate application, premature closure or invented clinical/route assertions on the fixed invariant suite. Any failure blocks a reliability claim.
- On held-out material-change events, at least 90% recall and 90% precision for correctly sourced proposed changes; report denominators and unresolved cases. Abstention is allowed but does not count as recovering an answerable change.
- Dependency engine: exact expected affected-assignment set on all explicit-link cases. Report AI candidate-link errors separately.
- Product-efficiency hypothesis: at least 20% lower median human time than the structured-board baseline with no worse final accuracy. This is a future target, not a prototype release gate or an achieved claim: the current two authors cannot supply an independent blinded timing study. An optional controlled pilot is exploratory only; report review corrections now and leave comparative speedup untested unless a suitable independent protocol is authorized.
- Telephone feasibility: 10 controlled test calls, at least 9 complete the intended intake; interruption and disconnect are demonstrated. Target p95 spoken-response start within 3 seconds of end-of-turn; report actual timings, network and failures rather than claim guaranteed service.

The accuracy, invariant, dependency and telephone criteria are proposed prototype gates; efficiency is a future hypothesis. None is a sourced operational standard or achieved result. If a prototype gate fails, simplify scope or narrow the claim; do not fabricate scores or quietly lower targets after seeing results. “Unreachable” preserves uncertainty and is not a successful verified case.

## 11. Technical feasibility, costs and alternatives

No framework, database, Google model, region or telecom provider is selected. Functional responsibilities are intake/audio bridge, conversational proposal service, reviewed record store, deterministic impact checks and coordinator/team interfaces. The model has proposal/read-only capabilities; authoritative mutations require reviewer permissions and validation.

Research supports plausible candidates: bidirectional telephone audio and Gemini Live, with audio conversion and interruption handling; constrained proposals; streaming hosting with persisted shared state. Twilio's current Voice trial documentation blocks `<Stream>`, so this candidate path requires a suitable full account and separately authorized spend; it is not a free-trial promise. Exact account access and quotas are still gates. The [feasibility note](../research/prototype-feasibility.md) gives the sourced telephone cost illustration; total budget remains unknown until model, hosting and usage are priced. No paid feature may be enabled under this PRD.

| Approach | Benefits | Tradeoff | Recommendation |
|---|---|---|---|
| Structured intake/task board | Simple, reviewable and reliable dependencies. | Less flexible handling of unexpected referents and corrections. | Required serious baseline and manual fallback. |
| AI extraction into that board | Can reduce transcription/entry work. | Strong existing overlap; leaves clarification to humans. | Evaluation baseline, not the headline. |
| Adaptive clarification plus evidence-linked reassessment | Visible resident experience tied to an operational decision. | Phone complexity and review cost; benefit unproved. | Proposed bounded prototype. |

## 12. Conditional delivery sequence and scope gates

All future work below requires separate explicit implementation approval. Two humans should each own bounded tasks and review the other's PRs per the working agreement; do not assign named owners without agreement.

1. **Scope/feasibility gate:** approve the MVP/deferrals, synthetic role policy, language target, phone geography, account owner and cost ceiling. Confirm registration, exact submission cutoff and eligibility privately. Research does not establish these.
2. **Thin vertical proof:** a real call creates a source-linked proposal; a coordinator reviews it; one assignment is flagged correctly. Verify interruption/disconnect before substantial UI polish. If phone access fails, seek an explicit scope revision; text/browser voice does not satisfy R2.
3. **Core workflow:** implement versioned review, explicit dependencies, three coordinator pages and restricted team acknowledgment. Add the negative control and scarcity case.
4. **Evaluate:** freeze fixtures/reference labels, run baselines and held-out cases, inspect failures and measure reviewer effort. Cut secondary features if core behavior is weak.
5. **Presentation:** keyboard/mobile review, reproducible synthetic demo and a deck/video explaining the AI contribution, measured behavior and limitations. Deployment/public repository/submission require their own authorization.

Proposed rough budget: 12 person-days over six working days for two humans, with feature ownership agreed at kickoff. This is an unvalidated planning estimate, not a completion guarantee.

| Work | Person-days | Stop/cut rule |
|---|---:|---|
| Phone/account feasibility and audio vertical proof | 2.0 | Time-box the first authorized working day. If approval/number/audio is unavailable, stop secondary UI work and seek a scope decision; do not silently claim R2. |
| Reviewed records, identity/version/retry correctness | 2.0 | Keep; reduce fixture breadth before compromising review correctness. |
| Dependencies, reassessment brief and acknowledgment | 1.5 | Keep explicit links; cut inferred dependency discovery. |
| Three coordinator surfaces, restricted team view and context map | 2.0 | Use a minimal map and reusable drawer; any map/R5 scope reduction needs approval. No continuous tracking. |
| Frozen reference cases and accuracy/integration evaluation | 1.5 | Keep; cut optional effort-timing pilot and extra languages before accuracy checks. |
| Authorized deployment verification, video/deck and submission preparation | 2.0 | Prioritize an honest complete flow; publication remains separately gated. |
| Contingency | 1.0 | Do not spend on new features. |

If approval arrives by October 12, aim to complete the thin proof October 12, core flow October 13–15, evaluation October 16 and authorized presentation/deployment preparation October 17. Confirm the actual cutoff; do not rely on October 18 as a full working day. Later approval or unresolved account gates require re-estimating and narrowing scope. Named possible cuts needing human agreement: map/context cards, R5 manual locations, English intake testing, additional assignment scenarios. None is silently deferred beyond the table in section 4.

Cut optional context embellishments before review correctness, real phone acceptance and accuracy evaluation. Reusing third-party code/assets must satisfy the event's freshness/license rules; no comparator code has been copied.

## 13. Open decisions and adoption

| Decision | Required human/evidence input |
|---|---|
| Final scope and deferrals | Approve this PRD or a narrower alternative; the accepted R1–R9 list is not implicitly changed. |
| Phone and spend | Number geography, legal account owner, available approval documents kept private, budget ceiling and service authorization. |
| Google/runtime choices | Current model/API/region/quota/cost comparison and engineering review. |
| Operational deployment | Named operator, authoritative procedures, review/assignment responsibility, qualified clinical governance if ever added. |
| Data handling | Prototype application defaults: no raw audio retention, synthetic transcripts only, explicit processing permission, restricted access; vendor processing/log retention still requires verification before implementation. |
| Post-hackathon adoption | Who owns/funds/supports the desk workflow; whether it complements existing systems; usable integration/export and organizational permission. No partnership/API exists yet. |

Potential distribution is a private coordinator workspace with restricted team views, then a controlled synthetic judging demonstration. An eventual existing-system integration is a hypothesis, not part of this prototype. Public deployment/source must follow event requirements and separate human authorization, with no real personal data or secrets.

## 14. Honest judge-facing story

Problem: coordinators must act despite conflicting, outdated reports and changing resources. Demonstration: a resident conversation changes facts that matter to existing assignments. Technical contribution: source-grounded clarification and proposals, reviewed state and exact dependency checks, with a measured comparison. Impact claim: potential reduction in reassessment effort, not rescued lives or guaranteed fulfillment. Innovation: the evaluated interaction/workflow, not claiming the first AI relief dashboard. UX: an explanation the coordinator can inspect, correct and act on.

The published rubric weights technical merit/GenAI 40%, problem/impact 25%, innovation 25% and UX 10% (H2, rechecked 2026-10-11). No score or finalist probability is predictable from this PRD.

## 15. Review status

Independent office-hours review completed two iterations: 8/10 initially, 9/10 after revisions, for document quality only. Findings corrected: bounded workload and early telephone stop gate; explicit vehicle rather than whole-team dependencies; report review separated from corroboration; common clarification oracle and equal-channel baselines; comparative speedup left untested. The second review found no blocker to human scope review; its remaining claim/gate wording and baseline-script clarification were corrected before handoff.

Documentation validation: five changed/new documents checked; 19 local links resolved, P1–P10 source entries present, no trailing whitespace or sensitive-content pattern matches. These checks do not validate integration or product behavior. No calls, model evaluations or application tests have run. Human approval has not occurred. Architecture selection and unresolved account/operational decisions remain gates.

## 16. Proposed extension: assessment gaps beyond incoming requests

User concern, raised 2026-10-11: some people needing help will not or cannot contact the service. This limitation must be represented; the approaches below remain proposed. See [research and detailed design](../research/unreported-needs.md).

Retain known-case response and add a separate area-assessment loop. Proposed minimum: an Assessment gaps tab within Operations; proxy/field reports through existing review; and human-owned assessment actions through Response. Show potential exposure, last scoped assessment, contact attempts, owner and uncertainty separately. No current assessment is a knowledge gap, not confirmed unmet need or an automatic dispatch priority. A contacted resident or completed visit cannot certify an entire area safe.

F13 (proposed future criterion): on two synthetic areas, reviewed exposure plus missing relevant assessment can propose a gap; recent scoped evidence supplies a negative control. A coordinator can assign or defer verification with a reason. Partial/unreachable attempts preserve unknowns; a reviewed field discovery creates a provisional case without shared-phone merging or duplicate application. Area estimates never create individual cases or a numerical “missing people” count.

Live satellite/population ingestion, demographic prediction, autonomous outreach/dispatch, outbound calling and offline synchronization are deferred proposals requiring explicit approval. This extension changes the scope/estimate: the 12 person-day budget excludes it and needs re-estimation or agreed cuts. The previous independent review covered version 0.1; version 0.2's extension has not had that review. No new scope is accepted or implemented.

## 17. Satellite-informed building and population estimates

User requested satellite imagery for estimating houses and people on 2026-10-11; recorded as R9 and [decision 0002](../decisions/0002-satellite-estimation-request.md). The request accepts a capability to plan, not implementation or a data/provider choice.

Proposed workflow: inspect licensed imagery/derived building footprints within a defined area; filter and review detections; intersect with independently sourced flood extent; display potentially exposed buildings and a separate area population estimate from a documented population model. Spatial overlap is an exposure indicator, not proof that a building is flooded inside or occupied. Residential classification and household counts remain unknown without additional evidence. Do not multiply every roof by a default family size or ask a general-purpose vision model to invent an occupancy count.

The Assessment gaps view should show the imagery/footprint dates and versions, flood observation time and type, detected-building count and filter method, residential classification or unknown, modeled population estimate/reference year/method, uncertainty if supplied, and field-assessment scope/time. A detector confidence score describes a building detection, not occupancy or human need. No invented confidence interval; disclose missing uncertainty and use labeled sensitivity assumptions only when justified.

Candidate research: Google Open Buildings covers Thailand and supplies footprint geometry/confidence, but no building-use information (U5); WorldPop describes census-informed gridded population modeling and uncertainty from source ages/projections (U6). Neither is selected or tested locally. Existing data is a stronger first candidate than training a new detector within the deadline. Baseline and disaster-time data differ; displacement and imagery age prevent claiming current presence.

F14 (proposed future criterion): fixed synthetic footprints include a duplicate, non-residential/unknown-use buildings and a multi-household example. Reviewed counts use a frozen overlap/filter policy and do not equate buildings with households. Population is a separately sourced estimate, not derived from request totals. Missing imagery date/uncertainty and incompatible timestamps remain visible; replay does not inflate counts. These counts may support an assessment proposal, never automatic case creation, safe-route inference or dispatch.

Actual local imagery access, licensing, resolution, cloud/occlusion limitations, footprint accuracy, population suitability, processing costs and a labeled validation sample need a feasibility gate. R9 needs a scope/effort update before implementation; it is absent from the 12 person-day estimate. No imagery was downloaded, no live estimation ran, and version 0.3 has not received independent review.

## 18. Proposed flood situation updates

See [flood-source research](../research/flood-situation-updates.md). Proposed Operations layer separates observed flood extent, rainfall/station measurements, forecasts/warnings and reviewed local observations. Store observation/acquisition, publication and retrieval times separately; include geographic scope, units/reference, source/version and uncertainty. A stale/missing product remains visibly stale/unknown; a recent fetch is not a recent observation.

Candidate sources include HII/ThaiWater, TMD, GISTDA, Google Flood Hub/API and DDPM, each with distinct limitations. No source or live integration is selected. Google API access is waitlisted; do not depend on approval before the deadline. Verify authorized local data access before changing the proposed R8 deferral; synthetic context remains the current proposed fallback.

Updated compatible flood evidence may propose exposure/assessment review under deterministic spatial rules, followed by human action. It does not establish current occupancy, convert gauge elevation into street depth, predict a safe route or dispatch automatically. Testing must cover stale data, failed fetch, no coverage, source conflicts, forecast/observation distinctions and duplicate updates. Additional feed work requires explicit scope/effort review; no integration has run.
