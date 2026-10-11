# Wireframe review package

> Prior design draft: the human requested a workflow rethink after these artifacts. Review the [volunteer planning and emergency workflow](../product/volunteer-workflow-proposal.md) before treating these pages/features/scenario as the current proposal. Artifacts are preserved; no final screens or MVP were accepted.

Date: 2026-10-11. Version: 1.1. Status: **proposed static design for human review**. No product implementation, integrations, services or infrastructure were built. Drawn controls have no application behavior. All displayed data is synthetic; the map is a schematic, not satellite imagery or verified flood conditions.

Start with the [eleven-page PDF](../../output/pdf/relief-ledger-wireframes-v1.1.pdf), then review the [detailed product proposal](../product/product-detail.md) and [consolidated PRD](../product/prototype-prd.md). The [demo fixture](../product/demo-scenario.md) defines one intended sequence; pages show selected states at different steps, not a simultaneous snapshot.

## Proposed design context

User purpose: coordinate flood evidence, population/building exposure context, emergency calls/messages, reported medical needs and volunteers. Audience: desktop coordinator/intake desk, team lead on mobile and resident/proxy reporter. Proposed tone: calm, clear, practical. These layout/brand choices are assumptions offered for review; no final brand/style is approved. Wireframes are grayscale so discussion can focus on information and actions.

Primary user action: establish an owned next step from reviewed evidence while keeping uncertainty and constraints visible. Layout: three main destinations, focused evidence/detail panels, lists as alternatives to maps, shared case detail and restricted supporting mobile views. Final fonts/color/motion remain open. Role-based visibility and clinical boundaries are product requirements to implement later, not implemented controls.

Key design principles: source and time are visible; estimate is distinct from confirmed need; map/list selection has one object identity; event review is explicit; unavailable resources never erase needs; no optimistic authoritative approval. Supporting implementation references after authorization: shape/impeccable spatial, interaction, responsive and UX-writing guidance, adapted to review/permission rules.

## Page index and what to review

| PDF page | Drawing | Main review question | PNG |
|---|---|---|---|
| 1 | Review guide and story | Does this connect the product into one useful workflow? | [Guide](../../output/wireframes/map-review-01.png) |
| 2 | Situation / assessment gap | Can an operator distinguish exposure, missing assessment and confirmed needs? | [Situation](../../output/wireframes/map-review-02.png) |
| 3 | Contact Center / field report queue | Is intake source/identity/scope clear before a case is created? | [Inbox](../../output/wireframes/map-review-03.png) |
| 4 | Contact Center / individual event review | Are original evidence, uncertainty and approval consequences clear? | [Event review](../../output/wireframes/map-review-04.png) |
| 5 | Response / tasks and constraints | Are owner, resource dependency, progress and unrelated control visible? | [Response](../../output/wireframes/map-review-05.png) |
| 6 | Response / draft revised brief | Is the draft distinct from an authoritative saved version? | [Brief](../../output/wireframes/map-review-06.png) |
| 7 | Shared case / medical and outcomes | Do need, referral and actual care/receipt remain separate? | [Case](../../output/wireframes/map-review-07.png) |
| 8 | Supporting team mobile and resident text | Is the task/intake simple, restricted and truthful? | [Mobile](../../output/wireframes/map-review-08.png) |
| 9 | Recovery states | Are incomplete, conflicting and unknown states actionable without false success? | [Recovery](../../output/wireframes/map-review-09.png) |
| 10 | Situation / expanded map workspace | Are extent, building overlap, assessment gap and selected-area action readable? | [Situation map](../../output/wireframes/map-review-10.png) |
| 11 | Response / expanded map workspace | Are current location, planned pickup and unavailable position data separate? | [Response map](../../output/wireframes/map-review-11.png) |

The [map experience proposal](../product/map-experience.md) specifies all layers and interactions, including a Contact Center location inset and own-task mobile map. Those two supporting map views are specified, not additional drawings. The previous [nine-page pack](../../output/pdf/relief-ledger-wireframes-v1.pdf) is preserved.

## Interaction intentions, not implemented behavior

- Situation: select map/list item → inspect sources/scope → create a draft assessment → Response checks/ownership. Mobile map becomes a list-first view; selected details remain available.
- Contact Center: select report → inspect original/translation → clarify subject/time → edit/link/leave unresolved → approve each attributed event against current version. Approval is not corroboration. Distinct event decisions remain visible.
- Case location changes do not rewrite planned pickup. Response: inspect dependencies → assign verification/revise/hold → save reviewed version → team acknowledges that saved version. Older progress/history remain.
- Team view: own task only → acknowledge version → submit own update for review. Resident view: processing permission → report/clarify → receive truthful intake acknowledgment. No outbound callback or offline-sync promise.
- Recovery: incomplete report keeps consented received content only; stale approval requires rereading; unreachable assessment preserves coverage uncertainty; disputed receipt preserves both attributed reports and remaining needs.

For each page, empty/loading/source-failed/permission-denied and unlocated/unassigned states are defined in [product detail](../product/product-detail.md). Essential actions must be keyboard-accessible with labels; evidence cannot require hover; uncertainty must use text rather than color alone. Formal accessibility/runtime testing has not occurred.

## Independent review and validation

Two independent read-only reviews examined workflow semantics and deadline/scope. Findings incorporated: granular event review; location versus planned pickup; precise V1 rather than whole-team impact; assessment action versus knowledge scope; medical governance unavailable; historical review scores kept separate; expanded workload estimate; destination closure removed from the main 170-second story.

The follow-up reviewer inspected the initial eight-page drawing pack and detailed docs. Corrected localized findings: VFY-01 has explicit desk ownership; medical need first appears when CALL-01's event is reviewed; independent need/clinical/progress/outcome axes; draft brief label and current-version acknowledgment. A ninth recovery page was added and visually checked by the primary agent; it was not part of the independent eight-page inspection.

Previous v1.0 validation: 10 documentation/helper files and 67 local links passed link, whitespace and sensitive-pattern checks; drawing-helper syntax checked. The original PDF has nine pages, the static/synthetic boundary footer on every page, and 2,177 extracted words with no out-of-page text. Rendered pages were visually inspected; a footer overlap, long annotation title and premature draft-acknowledgment badge were corrected. Final render completed with no renderer log output. Pattern checks are not a guarantee against every sensitive datum. No calls, AI/model evaluation, live feed, satellite inference, real clinical or field action was executed. Static review readiness does not establish implementation feasibility.

Map update validation: six changed Markdown documents and 44 local links passed link, whitespace and sensitive-pattern checks; drawing-helper syntax parsed. The new PDF has 11 pages and 2,766 extracted words, with the synthetic footer on each page and no out-of-page text. All pages were rendered without renderer output; the new map pages were visually inspected, and the earlier pages checked in a contact sheet (their bodies are unchanged except the opening subtitle). An overlong assessment badge and a landmark overlap were corrected. The two map pages were authored by the primary agent; the prior independent review does not cover this extension. No application/map interactions or source integrations were tested.

## Concrete choices for human review

1. Keep these three destinations and supporting case/team/resident views?
2. Agree the core demonstration and its clinical/data limits, or revise them?
3. Choose the lean fixture/import scope and explicit deferred capabilities; verify phone/data feasibility before implementation.
4. Confirm desktop/mobile emphasis and tone before visual styling.

The shape skill's brief remains proposed until user review; no skill output grants product implementation authority. The complete application, source integrations and public submission remain separately gated by the shared instructions.
