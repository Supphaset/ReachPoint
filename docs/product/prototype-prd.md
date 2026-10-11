# ReachPoint prototype PRD

**Accepted prototype scope:** [Prototype scope v1](prototype-scope-v1.md) specifies the approved inclusion/deferrals, five screens, resident arrival-window behavior, demo fixture and acceptance checks. Human approval is recorded in [decision 0005](../decisions/0005-prototype-scope-proposal.md); no implementation authorization is inferred. [v0.5](prototype-prd-v0.5.md) is preserved.

Version: 1.0. Date: 2026-10-11. **Prototype v1 scope accepted; implementation unapproved.** The human corrected the prior page-first design and confirmed a hybrid operating model: volunteer team leaders plan ordinary relief trips, while the coordinator assigns emergency missions. Teams need enough information to distinguish support-in-place from evacuation and other response needs. [Detailed workflow](volunteer-workflow-proposal.md), [requirements](requirements.md), [decisions](../decisions/README.md) and [sources](../research/sources.md) are the current review starting point.

The [v0.4.1 PRD](prototype-prd-v0.4.1.md), [prior feature matrix](product-detail.md), [wireframes](../design/wireframe-guide.md) and [prior demo](demo-scenario.md) are preserved drafts. They are not current approved screens. No implementation, architecture, provider, clinical protocol or paid service is selected.

## Product thesis and jobs

Help an organized volunteer team leader decide **where our team can help most, what mission is needed and what people/equipment/supplies to prepare**, using affected-area evidence, assessed needs and existing response coverage. Help a resident request urgent assistance and understand their own response status. Help the coordinator validate reports, coordinate coverage and allocate suitable emergency responders.

The core product output is an **actionable, evidence-linked mission proposal**, with explicit target, load/capability plan, ownership, conditions and remaining gaps. A flood map supports that decision; reviewed records support it. Neither is the whole product.

The working hypothesis is unvalidated by direct responder interviews or a local partner. No autonomous clinical triage, evacuation order, safe-route claim or exact arrival guarantee is approved.

## Accepted operating direction versus proposed mechanics

Accepted requested jobs: affected-area map and flood context; satellite-informed exposure; chat/real phone; team/resource updates; daily needs/capacity planning; medical aid coordination; emergency validation/allocation; resident status/help timing (R1–R12). Accepted operating model from the follow-up answer: team leaders propose routine trips; coordinators assign emergency missions.

Proposed mechanics: coordinator review of routine coverage/commitments, mission-specific explainable attention ordering, response-mode cards, editable supply/evacuation scenarios, capability matching and team-provided estimated windows. The bounded prototype treatment is accepted in scope v1; these have not become real operational standards. Qualified medical/rescue decision authority remains an unresolved dependency.

## Connected workflows

1. Team leader checks availability/capabilities/resources and opens the daily area map/list.
2. Area detail shows dated flood conditions, people/needs, response mode, existing coverage, missing assessments and required capabilities.
3. Team leader selects an intervention, target cohort/period and supply/load/capacity assumptions; compares contribution and uncovered gaps.
4. The proposed mission is coordinated against other plans, availability, access and receiving-site requirements; the team accepts the authorized version.
5. A resident/proxy urgent report receives prompt human review attention. Clarification/report validation is distinct from qualified urgency/response assessment.
6. Coordinator allocates a suitable available team; team acceptance produces a truthful resident status and any responsible estimated window.
7. Field updates, delays/resource failures and newly discovered needs revise relevant plans, coverage and resident information; outcomes remain separately evidenced.

Unknown access/capacity is not dispatch readiness. Incomplete validation does not hide a suspected emergency. No team confirmed means arrival unknown. A routine area trip does not automatically include every household in that area.

## Proposed experiences

| Experience | Content and action | Why |
|---|---|---|
| Daily area map/briefing | Hazard, needs, response coverage, response mode, mission-specific attention reasons, timestamped sources; shortlist relevant options. | Team leaders decide where their capabilities can contribute. |
| Area detail/mission planner | Assessed target, required capabilities, supplies, conditional evacuation capacity, commitments and comparison of alternatives; propose trip. | Prepare an appropriate mission and expose remaining gaps. |
| Emergency desk | Reported urgency, validation/qualified assessment states, evidence, owner and suitable-team options; allocate/coordinate. | Turn urgent reports into accountable assistance. |
| Team mission | Accepted brief, preparation list, staging/pickup/destination references, progress/window, changes and field reporting. | Execute the current authorized task and improve area knowledge. |
| Resident request/status | Low-friction request/update; own request progress, accepted assignment, responsible window or unknown, delay/change notice. | Reduce uncertainty without inventing a promise of rescue. |

A roster supports planning and dispatch. Exact navigation/layout is interpreted in the [replacement static wireframes](../design/workflow-wireframe-guide.md); do not preserve the previous three pages merely because they were drawn.

## Area response mode

Proposed labels: **Support in place**, **Evacuation assistance needed**, **Mixed needs**, **Assessment needed**. These describe dated reviewed planning information for an explicit scope; they are not blanket declarations of household safety or evacuation orders. Record reviewer/source/time, reported or assessed basis, exceptions, missing information and affected subset.

Support-in-place planning considers reported present people, ability to remain, essential supplies/services, access and assistance preferences/needs under later approved assessment policy. Evacuation demand comes from reviewed requests/assessments and appropriate authorized judgments. One medical request is independently routed; a relief label cannot close it. Contradictory or stale evidence opens review and can leave response mode unknown. A deep/high-population area is a signal to investigate and plan contingencies, not 'everyone must evacuate'.

## Planning logic and AI contribution

Relief plan: target cohort × explicitly approved allowance × stated period, compared with matching usable/received supplies; active commitments are a separate planned-coverage layer. Conditional evacuation movement capacity: reviewed usable passenger places × feasible trips in a period, compared with known assisted-evacuation demand; unassessed exposure drives separately labeled contingency scenarios. Medical capabilities come from qualified assessment/declared verified team capacity, not an AI-generated treatment kit.

AI clarifies messy source-language reports, proposes attributed updates and summarizes area planning evidence/missing questions. Deterministic logic computes quantities/capacity, enforces permissions and state transitions, and checks explicit dependencies. Appropriate humans approve mission/clinical/rescue/access decisions. Show why a recommendation fits the mission and where assumptions remain.

Efficiency means useful uncovered assistance within available capability/time/resources, consistent with authorized urgency and equitable attention. Do not optimize only for shortest drive, largest population or fewest supplies. Inaccessible or silent areas remain visible even when no current team can respond. Actual optimization weights/algorithm are unselected.

## Small coherent prototype proposal

One fictional locality/three areas; two synthetic team profiles; one bounded flood/population/field source package; one relief plan; one emergency case with an explicitly fictional qualified-review outcome; a real controlled inbound call only if telecom gate passes; resident status with team-provided window. Include field discovery of an unreported need and one resource change that revises capacity/assignment/status while an unrelated plan remains unchanged.

Core demo question: **Can a leader produce a sensible mission plan, then can the coordinator handle an urgent request and keep both team and resident informed when the plan changes?** Synthetic depth/response-mode fixtures cannot establish real-world safety or clinical efficacy. A simple structured/manual baseline must remain for comparison; no uniqueness/adoption/winning claim is established.

Deferred proposals: own depth model, complete inventory suite, multi-feed live guarantee, continuous GPS, route/ETA automation, offline synchronization and unsupervised medical dispatch. Inclusion/deferrals are agreed for prototype v1; requested capabilities outside that bound remain future needs. No new workload guarantee: earlier 11–14/15–20 person-day estimates preceded this revision. Re-estimate after the chosen scenario and data/phone/authority gates.

## Review and evidence gates

- Define one organized response-team setting, locality and available flood/depth/assessment package; verify source date, permissions and validity. Modeled depth is possible in published services but no usable local depth feed is verified.
- Agree routine commitment approval, report validation, emergency escalation and qualified clinical/rescue boundaries; prototype uses synthetic review authority until real governance exists.
- Agree minimal resident status channel, secure reference/privacy and who can issue/change a window; outbound SMS/callback and automatic ETA remain unselected.
- Future checks: no exposed-as-trapped count, duplicate/group overlap inflation, promised-as-received coverage, unassigned ETA, stale-window persistence, resource double booking, invisible suspected emergencies or unauthorized clinical priority. Test plan changes precisely, with a negative-control mission.

No application tests, phone calls, local source ingestion or real dispatch have been executed. Documentation is ready for workflow review; implementation/publishing/deployment remain separately authorized actions.
