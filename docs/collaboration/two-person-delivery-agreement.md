# ReachPoint — two-person delivery agreement

Date: 2026-10-11. Owners: **You** and **Friend**; replace these labels with agreed names when sharing.

**Accepted assignment:** you own the volunteer workspace and flood map; your friend owns resident/coordinator experiences, chat/voice intake, reconciliation and database updates. Human instruction is recorded in [decision 0006](../decisions/0006-two-person-work-split.md).

**Recommended handoff design:** the detailed responsibility boundaries, logical data contract and milestones below are proposals for both of you to review. They do not select a framework, database, provider or deployment. This document describes delivery expectations; implementation is authorized separately by [decision 0009](../decisions/0009-implementation-start-and-technical-direction.md) from 12 Oct. Product boundaries remain in [approved scope v1](../product/prototype-scope-v1.md), [requirements](../product/requirements.md) and the [design doc with approved mockups](../designs/resource-split-and-live-loop.md).

For concrete screen reads, write operations, logical table ownership, proposed fields, synthetic request/response examples and errors, use the [joint decision pack](../planning/joint-decision-pack.md) §3–§4. It is the detailed companion to this responsibility agreement; its names are proposed interfaces, not implemented endpoints.

The [proposed architecture diagrams](../planning/architecture-overview.md) show the whole-system connections and the emergency-to-resident feedback flow, with both workstreams identified.

## What you are delivering together

A leader can choose an area and plan a useful relief trip. A resident can report an emergency. A coordinator can reconcile the report and offer an appropriate mission. The team can accept and update it. The resident then sees the confirmed assistance and its current expected window. A changed location, unavailable resource or field discovery affects the relevant records and views.

The handoff goes **both ways**. Intake must provide reviewed needs to planning; planning must provide team availability, proposals, acceptance and progress to coordination and resident status. Neither side is complete as a standalone map or chatbot.

## Responsibility split

The human assignments above remain accepted. The detailed division is recommended: your side includes the team mission/update surface; your friend's side includes resident status and routine-plan review; your friend leads shared persistence/state enforcement, with you supplying planning calculations.

| Area | You deliver | Friend delivers | Review together |
|---|---|---|---|
| Volunteer daily workspace | Map/list, area detail, attention reasons, coverage and mission planner | Reviewed needs, commitments and permitted team data | A leader can explain why their proposed trip is useful |
| Flood/building/population context | Bounded source package, area boundaries, typed overlays, exposure method/uncertainty and source detail | Store/publish agreed source references with access rules | Extent, depth, buildings, exposure and actual needs stay distinct |
| Resident intake | Area/landmark reference catalogue and location-review component specification | Chat, genuine inbound-phone feasibility/integration after authorization, clarification, interrupted-intake recovery | An ambiguous/unlocated report remains usable without a false pin |
| Reconciliation and coordinator desk | Planning/area context and reusable map component if useful | Source-linked proposals, identity/location review, corrections, emergency offers and routine-plan review | AI proposals require review; duplicate reports do not inflate counts |
| Team/resource workflow | Own-team profile/update form, mission proposal, acceptance, brief acknowledgment, progress/delay/field reporting | Permission checks, saved versions, availability/resource conflicts and canonical state transitions | An offer is not accepted; resource loss flags the linked plans |
| Resident help status | Team/coordinator window input and progress reports from volunteer UI | Protected own-request status, separate assistance types, delay/unknown states and next-update ownership | No assignment means no confirmed arrival; stale windows are withdrawn |
| Quantities and summaries | Shared planning calculation specification and matching preview logic; area summary definition | Integrate the agreed logic with reviewed records and shared persistence | No second incompatible quantity/state calculation |
| Integration and evaluation | Map/planner/team evidence and checks | Intake/review/status evidence and checks | One joined demonstration, meaningful baseline and failure checks |

Your friend has the heavier integration burden: chat, phone, reconciliation, coordinator UI, resident status and shared persistence. Keep those narrow. You take the bounded geospatial package, planner calculations, team workflow and shared scenario preparation to balance the split. Do not add more channels, live feeds or separate administration pages before the shared flow works.

## Your work brief — volunteer and map owner

**Goal:** a team leader can answer “Where can we contribute, what should we bring, and what is our current accepted task?”

Deliver these reviewable outcomes:

1. **Area map/list and briefing.** Three planning areas with identical IDs across map/list/detail. Show dated flood evidence, separate modeled exposure, known reviewed needs, response mode with reviewed scope, received aid, accepted commitments and assessment gaps. Missing/stale data stays visible; tile failure retains list/detail work.
2. **Bounded flood/exposure package.** Supply area boundary IDs/versions, source observation and retrieval times, measurement type, units/reference, method/uncertainty and clear synthetic-versus-source-backed labeling. Describe what the package cannot establish. No own depth model, live-feed promise, trapped-person inference or safe-route claim is required by v1.
3. **Mission planner.** Select target scope/period, intervention, proposed load/capacity and required capabilities; show overlap and unresolved payload/access/destination checks. Drafts are separate from commitments. The preview and persisted result must use the same approved calculation rules and input version.
4. **Team mission and update surface.** Show offers/current brief, team acceptance, version-specific acknowledgment, preparation, responsible estimated window and last update. Submit own-team progress, unavailable-resource reports and scoped field observations to the common review/update path.
5. **Handoff package.** Give your friend the area/landmark catalogue, source-package specification, planning-rule specification, permitted team update requirements and synthetic examples. Include expected unknown, delayed and failed-layer behavior, not only a normal screenshot.

**You need from your friend:** versioned permitted area summaries, reviewed need scope/count basis, commitments, team/resource records, mission offers/briefs, update outcomes and clear rejection/conflict responses. A full medical narrative, raw call or telephone number is not necessary for the general volunteer map.

**Your side is done when:** a leader can compare the three areas, prepare the matching relief proposal, accept a separate emergency offer and report a resource failure through the shared records; the map and planner reflect reviewed changes without inventing coverage, locations or receipt. The bounded source package has an agreed, disclosed provenance and limitations; a synthetic package cannot be claimed as actual satellite analysis. Visual completion alone does not satisfy this.

## Friend's work brief — intake and coordination owner

**Goal:** a report becomes reviewed, accountable assistance that both the volunteer and resident can follow.

Deliver these reviewable outcomes:

1. **Resident chat and voice intake.** Capture reported location/landmark, assistance needs, people/count basis, source/language/times and unresolved questions. Preserve original meaning alongside translation. Real inbound telephone access has a separate feasibility gate; browser voice is not equivalent. Use synthetic controlled callers only after implementation/account authorization.
2. **Reconciliation and review.** AI may suggest attributed events or possible associations. The desk supports review/edit/approve/reject, provisional identities, shared phones, duplicate/group overlap, changed locations and corrections with history. Save pending evidence without silently overwriting authoritative facts. Incomplete suspected emergencies remain visible with an owner.
3. **Coordinator workspace.** Review operational facts, record the separate synthetic qualified assessment where required, inspect capability/availability and offer scoped emergency missions. Review routine proposals for coverage and readiness. Keep offered, accepted, preparing and reported outcomes distinct; unresolved capacity/access blocks a ready claim.
4. **Shared persistence and state boundary.** Lead the proposed shared record/read/update contract, permissions, retry handling, version conflicts and linked-plan changes. Integrate your partner's planning rules rather than inventing another gap calculation. “Update the database” means persist evidence/proposals and apply authorized reviewed changes with history, not write the AI conversation directly into final case state.
5. **Resident status.** Provide a protected own-request view and the same status for authorized telephone contact. Show each assistance type independently, accepted team, current window or unknown, update time, delay and next-update ownership. No public lookup by phone number; outbound SMS/callback/push stays deferred.
6. **Handoff package.** Supply the agreed logical contract, synthetic records in normal and failure states, read/update behavior and permission boundaries. Demonstrate what happens when a review is rejected, a write is retried or a newer version exists.

**Friend needs from you:** stable area/boundary/landmark references; typed source data and uncertainty; planning-rule definitions; team/resource information; proposals, acceptance, brief acknowledgment, window/progress/resource updates and field reports using the agreed IDs.

**Friend's side is done when:** the same reviewed request appears in coordinator, team and own-resident views; suitable scoped offers require team acceptance; a reviewed delay withdraws the stale resident window; duplicate/ambiguous reports remain reviewable without corrupting counts. Required controlled inbound telephone behavior must be verified, or its failed gate must be recorded for an explicit scope revision; text/browser voice alone cannot mark R2 complete. A completed conversation alone does not satisfy this.

## Shared contract to agree before either side depends on the other

This is a **logical contract checklist**, not an implemented database schema or API. Names below describe concepts; freeze actual field names, types and transport together during technical planning. Each side must be able to work from the same synthetic examples before a live integration exists.

| Shared concept | Minimum agreed content | Lead for meaning and handoff |
|---|---|---|
| Area and landmark | Stable area ID, boundary version, geometry/reference, landmark ID, label and parent area; unknown/ambiguous location behavior | You define; Friend references/persists |
| Hazard/exposure evidence | Evidence ID, scope/source, observed/acquired versus retrieved time, measured/modeled/qualitative type, units/reference, method/uncertainty, synthetic flag | You define validity; Friend integrates storage/access |
| Incoming report / proposed event | Report/event ID, channel, source attribution, received/observed times, original/translation references, proposed facts/associations, unresolved fields, review state | Friend; your field reports enter the same pipeline |
| Reviewed case and needs | Case ID distinct from report/contact IDs, provisional/resolved identity, scoped current location/time, assistance type, quantity/unit/period/cohort basis, overlap/uncertainty, reviewed source references and record version | Friend; You consume permitted fields |
| Area planning summary | Area/scope/version and generation time, reviewed response-mode basis, target versus modeled exposure, received/committed/unassigned values with units/period, known evacuation demand versus conditional capacity, missing assessment and attention reasons | You define calculations/presentation; Friend supplies reviewed inputs and integrates publication |
| Team and resource | Team/resource IDs, declared/reviewed capability basis, availability/window, usable capacity assumptions, existing commitments, any permitted reported position/time | You define leader inputs; Friend enforces shared availability/state |
| Proposal / mission | Proposal/mission ID, area/case/need references, target scope/period, team/resources, readiness/dependencies, offer/acceptance state, brief version/acknowledgment, pickup/destination and responsible window basis | You own routine proposal/team inputs; Friend owns coordination/review transitions |
| Resident assistance status | Own case/assistance reference, included scope, accepted mission/team or none, progress, current arrival window or unknown, last update, delay, next status-update time and responsible owner | Friend derives from shared authoritative records; You supply team reports |
| Update result / history | Submission ID, actor/role, expected record version, resulting status/version, approval/pending/rejection, changed dependencies and attributable history | Friend leads; both UIs handle the result |

Before freezing the contract, agree these rules:

- **One ID system.** Case, household/provisional identity, report, contact, area and mission are different concepts. Both channels may refer to the same case after review; a shared phone never establishes household identity. Unresolved case association cannot silently create another authoritative count.
- **Unknown is representable.** Unknown quantity/location/capacity is not zero. Quantities include units, scope and period; population exposure cannot be added to confirmed needs. Unknown overlap prevents a falsely exact coverage total.
- **Time and versions are explicit.** Agree timezone handling and freshness policy; retain source observation time separately from retrieval/update time. A newer fetch does not make old flood evidence current. Map summaries identify the input versions they represent.
- **One business-rule definition.** You lead planning arithmetic and summary rules; Friend leads review/mission state rules. Both review both. The backend uses the same agreed planning logic as the preview, or rejects a stale proposal and asks for refresh. It must not trust a client-submitted total as authoritative.
- **Reads respect roles.** Coordinator can access necessary review evidence; team leaders get area summaries and minimum necessary own-assignment details; residents get their own assistance. General volunteer map/search/export must not reveal unrelated medical narratives or precise household data.
- **Writes are explicit submissions.** Each update carries attribution, submission ID and expected version. Retrying the same submission cannot create another need/commitment. Permission and conflict checks apply before an authoritative change; consequential corrections preserve prior history.
- **Refresh is visible.** Agree how one side learns of accepted changes; polling versus subscriptions remains open. Both views expose pending/stale/conflict/failed states. A saved proposal is not proof that another view has refreshed.

## What crosses the boundary

| Producer → consumer | Action/data | Required consequence |
|---|---|---|
| You → Friend | Publish proposed source/area package | Validate references/versions; publish with original provenance and access rules |
| Friend → You | Reviewed needs, mode, commitments and permitted team/mission data | Update versioned planning summary/map; unreviewed proposals do not become authoritative coverage |
| You → Friend | Submit routine mission proposal | Save draft/submission; coordinator reviews overlap/readiness; no stock or gap change merely from a draft |
| Friend → You | Offer approved mission/brief | Team sees its scoped offer; no resident arrival promise before acceptance |
| You → Friend | Accept offer / acknowledge brief / report window | Apply authorized transition to the stated version; acceptance and acknowledgment stay distinct; update own-resident status only for included scope |
| You → Friend | Report delay/resource unavailable | Create attributed review attention; once reviewed, hold/revise linked mission and withdraw stale window; unrelated plans remain intact |
| You → Friend | Field observation of unreported need | Retain scoped evidence/proposed events; coordinator reviews before changed need totals or assessment coverage |
| Friend → You | Reviewed location/need correction | Flag mismatched pickup/plan dependencies; keep old brief/history until explicit revised plan and new acknowledgment |
| Friend → resident | Publish accepted status/change | Same mission version and per-assistance timing as the shared records; next-update time is distinct from arrival |

Do not maintain independent mission/status databases on the two sides. The proposed shared boundary can use one selected store/service later; its physical architecture remains open. You may develop presentation against declared fixtures after authorization, but neither side can call fixture-only behavior a completed integration.

## First integration sequence and handoff expectations

These are ordered milestones. Their dates (CP0–CP3, 12–15 Oct) are in the [joint decision pack §6](../planning/joint-decision-pack.md#6-first-tasks-and-integration-checkpoints-proposed); [0009](../decisions/0009-implementation-start-and-technical-direction.md) authorizes the build steps. Before that, complete specifications, source/phone feasibility and sample-state reviews.

1. **Joint contract review.** Freeze the core concepts, IDs, access, units, timestamps, transitions and failure responses. Use the [shared walk-through scenario](../planning/joint-decision-pack.md#7-walk-through-one-synthetic-emergency-all-records-fictional): P-A/P-B/P-C, T-R/T-S/T-M, C-01 and M-01. Older packs use different scenarios; do not combine their numbers.
2. **Parallel specification handoff.** You supply the source/area catalogue and planning rules; Friend supplies report/review/mission/status rules. Together define synthetic examples for pending review, unknown location, accepted assistance, delay and version conflict. Resolve phone and source gates early; report blockers before promising delivery.
3. **First joined slice.** One resident text report → review → permitted need on your map/list. This establishes the shared record boundary before advanced AI, more layers or phone polish.
4. **Complete planning/response slice.** Your routine proposal → Friend's coordination review; Friend's emergency offer → your team acceptance/window → Friend's resident status. Check versions and actual scope inclusion.
5. **Change and discovery slice.** Resource failure withdraws the stale window; a scoped field report remains pending then changes only reviewed scope. A location correction requires explicit plan revision and acknowledgment.
6. **Required channel/source verification and demo.** Add genuinely verified bounded source/phone behavior within authorized scope. If a required gate fails, revise scope explicitly together; do not substitute a mock under the same claim. Run the joint checks below before visual polish and submission work.

At each handoff provide: what is ready, affected contract version, matching synthetic example, checks actually run, known limitations and the next dependency. Report a blocker when it threatens the other's work. A short daily check-in covers changed contract/fixture, completed shared flow, blocker/owner and next integration step. Never surprise the other person with renamed fields or changed meanings.

## Joint acceptance checklist

These are future checks, not test results:

| Check | Expected result | Lead / reviewer |
|---|---|---|
| P-A supply planning | Target 80, received 20, other accepted commitment 30: remaining 60/unassigned 30. Your draft 30 does not reserve stock or close the gap. Matching reviewed acceptance changes planned coverage, not receipt. | You / Friend |
| P-B overlap and scope | The emergency's three people are already within reviewed demand 24; repeat chat/call cannot make 27. Modeled exposure remains separate. Ambiguous association stays unresolved. | Friend / You |
| Assignment and timing | Emergency offer alone gives no confirmed arrival. Accepted transport can have a window while separate medical assistance remains pending/unknown. | Friend / You |
| Resource loss | Review S1-unavailable, hold/revise M-01, withdraw its current window; next-update ownership visible. Unrelated P-A draft and independent medical state stay correct. | Both |
| Current location versus pickup | Reviewed resident move does not silently move old pickup. Revised brief requires its own acknowledgment. | Friend / You |
| Silent area / field discovery | P-C exposure remains distinct from known needs. One scoped observation cannot clear all P-C; unknown quantity remains unknown. | You / Friend |
| Retry / conflicting edits | Retry one submission without duplicate effects; reject/resolve stale version without overwriting newer review. | Friend / You |
| Permission / source failure | Resident cannot retrieve another case; general map hides restricted data; failed tiles retain list/detail; unavailable depth stays unknown. | Both |
| Outcome semantics | Preparing/en-route/completed team report does not prove receipt, rescue completion or clinical care. Suspected urgency remains visible during incomplete validation. | Friend / You |

## Changes, collaboration and unresolved decisions

Keep [CONTRIBUTING](../../CONTRIBUTING.md) and the [working agreement](working-agreement.md): one bounded task/owner/branch or worktree, one editing tool per checkout, shared-file ownership reserved before edits, the other human reviews the PR when remote publication is authorized. Neither partner changes a shared field/state/quantity meaning alone. Propose the change with a before/after example and migration/fixture impact; both review, then record consequential acceptance in [decisions](../decisions/README.md).

Still open: actual field/API names and schema, datastore/hosting, Google AI selection, telecom number/region/cost/consent, bounded source/locality, refresh mechanism, resident access/recovery, deployment owner/budget, exact effort and real operational/qualified governance. Your task split does not settle these choices. Both own the integration/demo story; the friend does not inherit every unspecified task by being the database updater.

## Documentation validation

Original agreement checks: five changed/new Markdown files and 44 local links including fragment targets, whitespace and sensitive-pattern scans passed. Detailed integration-contract update: five changed/new Markdown files and 45 local links/fragment targets, the same scans and five JSON example checks passed. `git diff --check` passed; the separate file checks cover the untracked documents in this checkout. No application tests or operational verification ran. No application code, database schema, integration, provisioning, package installation, commit/push or message to your friend was produced by these documentation tasks.
