# ReachPoint — prototype scope v1

Date: 2026-10-11 (Asia/Bangkok). Status: **Accepted prototype product scope.** Human approval: “approve” to the concrete v1 final review; see [decision 0005](../decisions/0005-prototype-scope-proposal.md). [Requirements](requirements.md) and [accepted decisions](../decisions/README.md) retain authority. Implementation, paid services, publishing and deployment remain unapproved.

> **Revised by [decision 0009](../decisions/0009-implementation-start-and-technical-direction.md) (2026-10-11):** the bounded locality is now real past-event flood geography. Hat Yai / Songkhla, Nov 2025 hosts P-A/P-B/P-C and the emergency sequence; Bangkok, Sep 2026 is a second map/briefing package with no operational records. Extents are computed from Sentinel-1 with dated acquisitions. Everything operational below stays synthetic, and the fixture IDs, quantities and rules are unchanged.

## Product definition

Help organized volunteer teams decide **where to help, what response is needed and what resources to bring**; help coordinators validate and allocate emergency assistance; help residents know **what help is confirmed and when it is expected**.

Accepted operating direction: team leaders plan ordinary relief trips; coordinators assign emergency missions. Requested inputs include map/flood context, satellite-informed exposure, reported needs, volunteer/resources and medical coordination. Own-request help timing is a core resident feature. The prototype mechanics/boundaries below are accepted for this scope; no real clinical protocol, automatic evacuation decision or operating partner is approved.

## Scope boundary

One bounded fictional locality, three planning areas, three small declared team capability profiles (relief, rescue, medical), one daily relief mission and one household emergency sequence. Profiles/qualified decisions are synthetic, explicitly labeled; they do not establish actual qualifications or provide clinical care. One approved bounded source package/fixture supports the map. Thai intake and English coordinator/demo UI remain proposed.

The scope prioritizes complete planning → allocation → resident progress → revised plan behavior. No expanded platform build or speculative feature is necessary to show that sequence.

## Five reviewable screens

| Screen | User and primary action | Essential content |
|---|---|---|
| 1. Area map / daily briefing | Team leader: compare where our team can contribute. Coordinator: inspect uncovered needs. | Flood evidence/time; separate exposure estimates; reviewed response mode; known needs; existing aid/commitments; assessment gaps; attention reasons; map/list/detail selection. |
| 2. Area detail / mission planner | Team leader: propose a useful trip. Coordinator: coordinate scope/coverage. | Target cohort and period; mission type; load and conditional capacity; extra capability requirements; overlapping commitments; readiness checks; remaining gap; submit/review plan. |
| 3. Emergency desk | Coordinator: review a request and allocate suitable responders. | Telephone/text report, original evidence, location/identity clarification, event review, reported urgency/qualified assessment, suitable options, owner and team acceptance. |
| 4. Team mission | Team lead: prepare, acknowledge and report against the current brief. | Scope, preparation/load list, necessary location/staging/destination details, version, window, constraints, progress/resource/field updates and blocked/delayed reasons. |
| 5. Resident request / help status | Resident/proxy: request/update help and follow their own assistance. | Requested help, review/assignment state, accepted team, per-assistance estimated window or unknown, update time, delay/change, location/situation correction and non-arrival report. |

A small team/resource roster is a panel under planning/dispatch. Case/source detail is a drawer. Request and status can be states of the same resident surface. Role-specific visibility is required; screen count does not define a framework or route schema. Previous wireframes are reference drafts. The [approved mockups](../designs/resource-split-and-live-loop.md#approved-mockups) interpret these five accepted experiences; visual layouts remain open for review.

## Core features and limits

| Capability | Include in v1 | Limit |
|---|---|---|
| Map and area needs | Pan/zoom, layers, selected area/case, synchronized list, source/time, unlocated queue. | One locality; no public household map or inferred safe routes. |
| Flood and exposure | One bounded typed flood/footprint/population package, measured/modeled/qualitative distinctions. | No continuous depth coverage promise. A synthetic fixture demonstrates behavior only; real analysis requires verified source/method and separate authorization. |
| Response mode | Support in place / evacuation assistance needed / mixed / assessment needed, explicit reviewed scope and evidence. | No autonomous safety classification or blanket evacuation order. Exceptions and medical requests remain separate. |
| Mission planning | Editable target/period/load; known evacuation demand versus contingency scenario; capability fit; coverage/overlap and capacity checks. | Small planning manifest, not procurement/full inventory/route optimization. |
| Emergency intake and allocation | One text channel, manual/field input and real controlled inbound call if approved telecom feasibility passes; review evidence and select a suitable team. | No AI clinical triage; no raw recordings by default; browser voice cannot substitute for accepted telephone R2. |
| Team workflow | Small roster, declared capabilities/availability, own-task brief acknowledgment and timestamped progress/resource/field reports. | No continuous GPS or offline-sync promise. Reported position appears only if supplied/permitted. |
| Resident help timing | Own request with per-assistance status and responsible team/coordinator window, change/delay handling and update path. | No team acceptance means no confirmed arrival; no automatic travel ETA or guaranteed rescue time. |
| Clinical/referral coordination | Reported facts, synthetic qualified-review outcome, medical capability allocation and recipient/handover states where relevant. | No real clinical service, diagnosis/prescribing or partner integration. Actual clinical governance remains open. |

Requested R1–R12 are represented within these bounded behaviors; external channels, continuous feeds and broad automation are deferred in the approved v1 scope, not claims that the broader requested capabilities no longer matter. A failed required call/source gate must produce an explicit revised scope for human review; do not relabel a mock as a working integration.

## Planning rules to freeze for the prototype

1. Show why an area needs attention: reviewed emergency/medical basis, known supply/evacuation gap, existing coverage and missing assessment. No universal population-times-depth score. Urgency and team suitability are distinct; local weighting/clinical thresholds are unselected.
2. Area modes are reviewed planning assumptions with scope/time, not proof that every household can stay safely. An area can have support-in-place and evacuation subsets simultaneously.
3. For supplies, use selected target, period and explicit item/unit allowance. Received/usable aid reduces remaining demand; active commitments are planned coverage. Unknown overlap prevents an exact coverage total.
4. Evacuation capacity uses reviewed usable passenger places and feasible trips/window. Crew/equipment, mobility/medical transport, access and destination checks remain explicit. Exposure only supports separately labeled contingency planning; it is not an evacuation count.
5. AI proposes source-linked clarifications/events/briefs. Humans review consequential facts and plans; deterministic rules control counts, permissions, dependencies and states.
6. A request's validation, qualified clinical/rescue assessment, team acceptance, progress, receipt and care are distinct. A suspected emergency stays visible during incomplete validation. No available team leaves an open need with an owner.
7. Shared phones do not identify households; repeat/group reports cannot inflate counts. Current reported location and planned pickup remain distinct until a reviewed revision.
8. A change flags exactly linked plans; the old brief/window/history remain inspectable. Revised authoritative briefs need version-specific acknowledgment.

## Resident help timing — required for demo acceptance

Each assistance type has its own status/window: evacuation, supplies and medical help cannot share a misleading universal ETA. The resident sees what is confirmed, an assigned team when accepted, preparing or team-reported en-route state, responsible estimated window, last update and known delay.

Before acceptance: 'We are seeking a suitable team; arrival time is not confirmed.' Coordinator can supply a separate **next status-update time**, labeled as an update commitment rather than arrival. An area-wide relief trip cannot establish household inclusion without explicit scope evidence.

A team/coordinator supplies the window and its basis; planned arrival is distinct from en-route estimate. A delay/cancellation/resource failure withdraws or revises the stale window in the resident view. If the replacement time is unknown, say unknown and assign follow-up. No countdown, stale estimate masquerading as current or completion inferred from task progress.

For v1 the proposed minimum is an in-product own-status view, and the same reviewed status can be communicated during telephone contact. Outbound SMS/callback/push is deferred until channel/cost/consent is selected and authorized. Use a protected synthetic request reference/session in the prototype; real access/recovery policy needs engineering review. No public lookup by phone number.

## One demonstration story

All records below are fictional planning fixtures, independent of earlier demo IDs. Nothing has been executed.

| Area | Initial planning evidence | Intended response |
|---|---|---|
| P-A | Dated flood/assessment fixture; assessed one-day target 80 people; matching 20 packs confirmed usable/received and 30 planned by another accepted mission. Allowance: explicitly fictional one pack/person/day. | Support-in-place subset. Remaining 60 packs, planned 30, unassigned 30. Leader proposes a matching 30-pack mission; no promise counted as delivered. |
| P-B | Separate modeled exposure 90; 24 assisted-evacuation needs established in reviewed fixture; reviewed usable scenario capacity 12 passenger movements within a stated period. | Evacuation subset with known gap 12; area medical demand remains separate. The emergency household's three people are already part of 24, not added again. |
| P-C | Separate modeled exposure 50 and no relevant current assessment/report. Actual household presence/needs unknown. | Assessment needed; silence is not safety. Proposed scoped visit/outreach rather than invented victim records. |

Sequence: leader compares P-A/P-B/P-C and prepares the P-A relief trip → a controlled synthetic caller from P-B reports a changed location, three people and medical assistance → desk clarifies/reviews facts; a clearly fictional qualified-review fixture supplies the assessed capability requirement → coordinator allocates a suitable rescue/medical response with explicit resource/access/receiving checks → accepted response gives the resident a per-assistance estimated window → a linked resource becomes unavailable → coordinator holds/revises the mission, resident's stale window is removed and next update ownership is visible → a field report identifies an unreported need in a scoped part of P-C; the rest stays unknown. Unrelated P-A mission remains unchanged.

The video can select states with disclosed cuts; it must distinguish real running phone/model behavior, synthetic evidence and simulated field/clinical events. No real rescue/clinical outcome, live satellite processing or universal coverage claim. This integrated story is the differentiator hypothesis; no winning/adoption claim is established.

## Validation and success criteria after implementation approval

- The leader produces a mission proposal containing target, period, load/capacity basis, capability needs, coverage, outstanding checks and owner.
- Map/list selection identifies the same object; source ages/types and unknowns remain visible.
- The three planning fixtures keep exposure, target recipients, evacuation demand, medical cases and coverage distinct, including the known cohort overlap.
- Intake clarification handles location/shared-phone ambiguity; each approved event is attributed and checked against current record version.
- Allocation depends on relevant capability/availability and explicit checks, not proximity alone; no double booking or unqualified clinical decision.
- Team acknowledgment is version-specific. The resident sees only their own request, confirmed scope, responsible window/state and updates.
- Resource failure changes exactly linked mission/status; removes stale arrival window; negative-control relief mission remains unchanged.
- Partial field assessment cannot clear an entire area; team completion cannot prove receipt or care.

When drawing replacement pages, review empty/unknown, conflicting, delayed, unassigned, disconnected and permission-denied states. Future evaluation compares the same synthetic decisions against a good structured/manual planning/intake baseline. Measure actual time/clarification/reviewer effort and critical semantic failures; do not claim field benefit from synthetic results. No runtime tests have run.

## Delivery order and open technical gates

1. Human scope review — completed: v1 accepted; inclusion/deferrals recorded in decision 0005.
2. Replace old wireframes with the five experiences and one shared scenario; verify role/actions/states against this scope.
3. Technical planning: bounded source package, genuine phone access, Google AI/hosting options, permissions, operating cost and effort. Read-only feasibility/documentation is authorized; paid setup, integration spikes/code and provisioning require explicit implementation/account authorization.
4. Once authorized, complete one planning → intake → review → allocation → team acceptance → resident status slice before additional polish; add source/phone integration as honestly verified capabilities, with manual recovery.
5. Run meaningful checks/baseline, then prepare authorized deployment and submission artifacts. Protect review/testing time; do not keep expanding v1.

Remaining feasibility details do not require reopening the product's purpose: local data/depth availability, telecom account/number/region, selected Google components, qualified operating responsibilities, secure status access and actual effort. They can change delivery scope if blocked. Earlier workload estimates are stale; no new schedule or cost guarantee is made. No implementation, dependency installation, infrastructure or publishing has happened.

Documentation validation: 10 changed/new Markdown files and 77 local links checked; whitespace and sensitive-pattern checks passed. Replacement PDF validation is recorded in the wireframe guide (removed 2026-10-11; in git history). These checks validate documents, not runtime integrations or operational capability.
