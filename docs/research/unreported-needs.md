# People and places missing from intake

Date: 2026-10-11. Status: research and proposal, not approved implementation. The user identified a material limitation: people needing help may not reach out or be able to reach the service. No outreach, real data collection, calls or integrations occurred.

## Evidence and limits

- U1: [IFRC community engagement guidance](https://solutions.ifrc.org/national-society-capabilitiesbuild-community-engagement-and-accountability/engage-and-be-0) supports participatory assessments, varied communication channels and adaptation to connectivity/literacy. Local volunteers and community representatives matter. General organizational guidance does not establish a Thai partner or prove our proposed system works.
- U2: [WorldPop disaster exposure case study](https://www.worldpop.org/case_studies/measuring-populations-exposed-to-disasters/) describes combining population estimates with hazard information to support area-level response planning. These are exposure estimates, not individual household identities or confirmed assistance needs. Local currency, resolution, licensing and usability require checking before any integration.
- U3: [UNOSAT Bangladesh flood assessment, 24 June 2022](https://unosat.org/static/unosat_filesystem/3306/UNOSAT_Assessment_Report_FL20220525BGD_Bangladesh_24062022.pdf) reports disrupted electricity/mobile communication and publishes preliminary exposure estimates. Historical Bangladesh evidence supports the communication failure mode, not a current Thai outage or a household rescue count.
- U4: [IFRC CEA guide](https://www.ifrc.org/sites/default/files/2022-05/RCRC_CEA_Guide_2022.pdf): indexed excerpts recommend diverse community representatives and cross-checking findings. Full web fetch failed due file size; no complete guide review claimed. Do not rely on one leader as a census of a community.

See [sources](sources.md) for access details. The following design is our inference and recommendation.

## Product consequence

Incoming requests are a self-selected sample. A quiet map may mean low need, lost connectivity, displacement, fear, language/access barriers or lack of awareness. Without independent evidence we cannot choose among these explanations. Neither many requests nor no requests establishes area-level severity. The software can help coordinate attempts to find missing information; it cannot guarantee universal reach.

Keep two loops:

1. **Known-case response:** interpret reports, review facts and reassess assignments, as in the current PRD.
2. **Area assessment:** identify places with uncertain current contact/assessment, assign an appropriate verification action and retain its result/limits. New household cases arise only from reviewed reports or observations, not population-map arithmetic.

## Ways to reduce exclusion

| Approach | Product support | Boundary |
|---|---|---|
| Someone reports for others | Neighbor/volunteer intake records firsthand versus secondhand knowledge, area, observation time and unknown identities. | A shared phone is not a household ID. An aggregate report of several families does not create invented named households or count as a complete assessment. |
| Community outreach | Coordinator assigns a check to an authorized community contact or appropriate field team; records owner, attempts, scope and result. | No partner roster exists. Diverse sources and specific assessment scope are needed; one contact cannot prove everyone was reached. Field access decisions stay with authorized humans. |
| Area context | Reviewed hazard/exposure evidence, last scoped assessment and contact failures can prompt assessment attention. | Exposure is not confirmed need. Silence alone is not proof of distress. No model-generated vulnerability or urgency score. |
| Multiple access routes | Phone/text plus human-entered field, paper or community reports feed the same review flow. | Phone needs connectivity too. Advertising via radio/community channels and offline collection need operator arrangements; neither is implemented. |
| Follow-up on known cases | Missed check-ins/contact failures remain visible with reason and next owner. | No answer is not resolved, absent, deceased or safe. Any callback requires agreed consent and separately authorized outbound capability. |
| Offline field collection, later | Store observations locally, retain observation/receipt time, sync with duplicate/conflict review. | Proposed future capability requiring explicit scope, device/security and implementation review; not included in the current prototype. |

## Bounded prototype proposal

Add an **Assessment gaps** tab to Operations, reusing the task/review flow; do not add a fourth coordinator page or build a population prediction service.

An area assessment record contains area boundary/version; signal type/source/time/uncertainty; last assessment scope/time/source or unknown; attempted contact and outcome; action owner; resource/access constraints; and review/evidence status. Area-level data and household-level facts remain separate. Expose only necessary restricted details.

Useful states: no current assessment recorded, check proposed, assigned, attempted/unreachable, partial assessment, scoped assessment recorded. These describe knowledge/action state, not area safety. Completing a task records its limited observation; it never certifies every resident is safe. Different evidence types remain visible rather than flattened into a confidence score.

An explainable rule can propose attention when an area has reviewed potential-exposure evidence but lacks a current relevant assessment under an operator-approved recency policy. Missing coverage/time/policy stays unknown. This is a request to investigate, not automatic clinical priority or dispatch. Contact success with one resident does not clear the whole area. No subtraction of reported households from modeled population to label “missing people.”

AI's possible contribution is interpreting ambiguous proxy/field reports and producing evidence-linked assessment questions. Explicit coverage checks and permission/state rules remain deterministic. Generic hazard/population overlays already exist (U2); differentiation must be demonstrated in the review/action workflow.

## Synthetic demonstration and acceptance

Introduce two clearly fictional areas, A and B, without replacing the existing assignment fixture:

- A has reviewed synthetic potential-exposure evidence but no current scoped assessment. No resident has contacted us. Show an assessment gap, not fabricated household cases.
- B has a recent scoped observation of the relevant place. It does not get the same gap flag, but remains labeled with scope/time/limits, not safe.
- Coordinator assigns an assessment action subject to known resources and access checks. With none available, the gap stays visible and unassigned; no route is invented.
- A simulated field report discovers one household that did not call. After review, create a provisional separate case with its actual reported need. A neighbor using the same phone remains separate; A remains partially assessed.
- Replaying the report creates no duplicate case/action. An unreachable attempt does not resolve the gap.

Suggested additional tests: unknown denominator, stale exposure, mismatched area boundaries, no contact versus no need, leader/proxy report versus individual evidence, partial assessment and shared-phone duplicates. Measure correct gap flags and state invariants on synthetic fixtures; do not claim the fraction of actual missing people found.

The current 12 person-day estimate did not include this extension. Re-estimate after scope approval or replace optional context embellishments/extra scenarios. Phone feasibility, reviewed records and invariant checks remain protected. Within a 170-second video, use this as a short discovery beat only if demonstrated honestly; otherwise discuss the coverage limitation rather than simulate an implemented feature.

## Unresolved adoption questions

Who defines the areas and assessment recency/scope? Who supplies lawful, reliable local data? Who performs outreach and can safely access an area? Which excluded groups are absent from the available data/representatives? Who owns failed attempts and handovers? These require an operational owner; a software demo cannot establish them.

## Satellite imagery and building estimates — requested extension

The user requested satellite imagery to support house/people estimation. Plan a separate area-level layer: satellite-derived building footprints → reviewed building counts → potential overlap with sourced flood extent; population estimates remain a distinct modeled dataset. Buildings are not necessarily residences; households and current occupancy remain unknown without evidence. Counts support assessment planning, not a count of people waiting for rescue.

U5: [Google Open Buildings](https://sites.research.google/gr/open-buildings/) lists Thailand coverage and provides footprint geometry/confidence without building-use information. Its V3 inference dates to May 2023; local imagery dates and detection quality require checking. U6: [WorldPop Global2](https://www.worldpop.org/blog/worldpop-global2-global-high-resolution-population-estimates-for-2015-2030/) describes census-informed population estimates and source/projection uncertainty. Sources are candidates, not selected integrations.

Start with existing footprint/population data and a small reviewed fixture, subject to authorization, rather than developing a new detector. Display dates, overlap/count rules, classification unknowns and model/reference year. Never convert a building confidence score into probability of people needing help. See PRD section 17 for proposed acceptance and scope gates.
