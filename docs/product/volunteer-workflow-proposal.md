# Volunteer planning and emergency response — proposed product workflow

Date: 2026-10-11. Version: 1.0. **Proposed workflow, not approved implementation or operational protocol.** Responds to the human's correction: understand volunteers' daily decisions, residents' requests/status and coordinators' emergency allocation before drawing more pages. Accepted requested jobs are recorded in [requirements](requirements.md) and [decision 0004](../decisions/0004-workflow-reframe-request.md). The prior wireframes are reference drafts, not acceptance of this direction.

## Product purpose

Help organized response teams decide where their capabilities are most needed, prepare the right mission and resources, and coordinate urgent assistance while residents can follow the status of their own request.

Primary planning user: an organized volunteer **team leader**, rather than an individual browsing a disaster map. Coordinators manage competing plans and emergencies. A resident/proxy submits a request and sees truthful progress. Clinical and water-rescue professionals have distinct capabilities/authority; an ordinary volunteer is not assumed qualified for either.

Accepted operating direction from the human's follow-up answer: team leaders choose areas and propose ordinary relief trips; the coordinator assigns emergency missions. The human also requested enough area information to distinguish support at home from evacuation. Proposed mechanics: coordinator review of routine coverage/dependencies/commitments and qualified clinical/rescue judgments where applicable; exact policies remain unapproved. No real organization, responder interview, clinical partner or local response protocol exists.

## Research and interpretation

- [IFRC 2025 needs assessment guidance](https://www.ifrc.org/sites/default/files/2025-11/IFRC_Emergency_Needs%20Assessment_and_Planning.pdf), relevant decision/analytical framework sections inspected: considers conditions, affected groups, response capacity and gaps, including who is responding where. **Product inference:** show unmet needs and existing coverage alongside hazard/population, rather than ranking flood severity alone.
- [INSARAG flood-response reference](https://insarag.org/wp-content/uploads/2025/08/Flood-Response-%E2%80%93-Capacity-Building-%E2%80%93-Technical-Reference-Note.pdf), March 2025 hazard/capability/logistics sections inspected: distinguishes response capabilities and discusses hazards beyond depth. **Product inference:** team suitability and transport constraints are separate from the demand estimate; the map cannot certify safe access.
- [Copernicus flood depth announcement](https://mapping.emergency.copernicus.eu/news/the-copernicus-emergency-management-service-improves-flood-depth-monitoring/) describes depth estimates using elevation data and a geospatial method. **Product inference:** useful depth maps are possible, but must be labeled modeled, dated and source-backed. No usable local product or live access has been verified here.
- [WHO emergency medical team standards](https://www.who.int/publications/i/item/9789240029330/) describe a framework for capable coordinated medical teams; [WHO triage overview](https://www.who.int/tools/triage) describes its tool as facility-based. **Product inference:** an app's report validation is not medical triage; do not turn that tool into a telephone chatbot protocol.
- [IFRC community engagement](https://www.ifrc.org/our-work/inclusion-protection-and-engagement/community-engagement-and-accountability) emphasizes honest communication and feedback. **Product inference:** residents need request progress, changes and a way to update the report, not an unsupported rescue countdown.

Access date: 2026-10-11. These are published practice references, not interviews, proof of local demand or endorsements. See [source register](../research/sources.md), V1–V5.

## Two connected workflows

**Daily planning:** team check-in → review affected areas and unmet needs → choose mission type/target → plan load and required capabilities → coordinate coverage and availability → accept a mission brief → report field conditions/outcomes → update the next plan.

**Emergency response:** resident/proxy report → urgent review attention and clarification → operational validation plus qualified clinical/rescue assessment where required → capability/availability matching → coordinator allocation → team acceptance → resident status/window update → progress, delay/reassignment and separately evidenced outcome.

Urgent reported danger can need escalation while verification is incomplete. Exact escalation responsibilities, time targets and emergency-service handoff require an approved local protocol; the prototype must not require every identity/detail field before exposing a request for human review. Suspected emergency, operationally validated request and clinician-assessed urgency are distinct.

## What the team leader needs before leaving

| Decision | Required information | Product output |
|---|---|---|
| Where should our team help? | Hazard condition/trend/time, assessed needs, people potentially exposed, recent assistance, committed coverage, overlooked/unassessed areas. | Map and shortlist with explainable attention reasons, response gaps and source age. |
| What kind of mission? | Relief delivery, scoped assessment, qualified evacuation/rescue or medical response; known requested outcomes. | Explicit mission type and scope, not generic 'help area'. |
| How much should we bring? | Target cohort and period, supplies already usable/received, demand units, pending commitments, own payload/inventory. | Editable load plan, shortfall, assumptions and remaining uncovered needs. |
| How much evacuation capacity? | Known people requesting/requiring assisted evacuation, scenario demand for unassessed exposure, passenger capacity, feasible trips/time, mobility/transport needs and destination acceptance. | Known demand versus contingency scenario; conditional capacity estimate and missing checks. |
| Do we need medical professionals? | Reported medical requests, qualified assessments where available, requested capabilities, case-specific coordination requirements. | Separate medical work and suitable team capability requirement; no AI diagnosis or kit prescription. |
| Can we undertake this mission? | Verified team capability, availability, staging/pickup reference, authorized access, equipment, transport, communications, destination acceptance. | Readiness checks and a coordinator-reviewed brief; unknown checks do not pass. |
| Are others already covering it? | Relevant team plans/accepted commitments, intended population/need, delivery window and last update. | Potential overlap warning and uncovered gap; a promise is not delivered assistance. |
| What changed while we traveled? | New reports, resource failures, location/need changes, assignment changes. | Reason/evidence, updated brief, acknowledgment and resident update where relevant. |

## Area card and map

Each selected area combines four distinct sections:

1. **Flood conditions:** observed extent, sourced measured or modeled depth, qualitative local reports, separate forecast/trend and observation/acquisition time. Show range/spatial variation when supported, not one invented exact depth for an entire village. Station level/reference remains distinct. Unknown areas remain visible.
2. **People and needs:** building detections, separate modeled population exposure/reference year, locally assessed present population where available, reported needs and uncertainty. Evacuation demand, relief recipients and medical cases are different counts. Unknown overlap prevents adding them into a unique-person total.
3. **Response coverage:** aid confirmed received/usable, accepted active commitments with scope/window, completed assessment scope, remaining known needs and unassessed population exposure. Old visits and pending promises do not imply adequate current coverage.
4. **Recommended next action:** evidence-linked planning suggestion such as 'coordinate a relief trip', 'seek qualified rescue capacity', 'medical request awaiting qualified review', or 'assess a silent exposed area'. Show reasons/missing information and allow coordinator revision; no opaque universal priority score.

Prioritization is mission-specific: rescue, medical and relief delivery cannot share one population-times-depth score. Show requested urgency, assessed/authorized priority basis, vulnerability evidence, unmet coverage and data gaps separately. Exact ranks/weights and authority need human/operational governance. An inaccessible area stays important even when the current team cannot reach it; suitability filters offer options without removing unmet needs.

A supply team may have a better contribution in a moderately flooded underserved area while a qualified rescue team addresses a smaller acute incident elsewhere. Large/deep flooding is a planning signal, not proof that every exposed person needs evacuation.

## Which response does an area need?

The human explicitly requested planning information that distinguishes people who can remain at home with supplies from people needing evacuation. Proposed area modes are **Support in place**, **Evacuation assistance needed**, **Mixed needs** and **Assessment needed**. These describe a reviewed need/planning basis for a stated scope; they are not a universal safety label or evacuation order.

Each mode retains source, assessment time, reviewer, affected subset, confidence/unknowns and exceptions. Support-in-place evidence should address reported presence/ability to remain, essential service/supply needs, isolation/access and preferences under a later approved local assessment policy. Evacuation planning uses reviewed assisted-evacuation requests/field assessments and appropriate authorized decisions. High modeled depth/population motivates attention and contingency planning but cannot alone declare every household's required action.

An area can contain both groups; split mission target/scopes rather than suppressing exceptions. An independent medical request remains open under any area label. Where evidence is missing, old or contradictory, show missing questions and assessment/review ownership, not an automatic 'food only' classification. Field updates can change the operating assumption and flag linked plans for human revision.

For efficiency, let the team leader compare two proposed contributions: target/coverage gained, unresolved people/needs, load versus own payload, required extra teams, commitments/overlap and conditional timing. The planner can stage supplies while a suitable rescue/medical team serves another subset. Show capability fit and outstanding gaps, not just distance. Actual ranking/optimization policy and route feasibility remain unselected.

## Capacity and load planning

**Relief:** select target cohort, assistance period and explicit approved item/unit allowance; compare with matching usable stock/confirmed received aid. Keep active commitments as planned coverage, not delivered coverage. Show remaining demand, planned coverage and unassigned gap separately. For group reports, disclose count basis, scope, overlap and uncertainty; do not manufacture household IDs or double-count group and household needs.

**Evacuation:** begin with reviewed case/field counts as known demand. Exposure helps construct explicit contingency scenarios for people not yet assessed; it never automatically becomes a trapped-person count. For each scenario, estimate passenger movement capacity from reviewed usable capacity per trip and feasible trip count within a stated period. Crew/equipment, mobility/medical transport, travel/access conditions, availability and receiving-site capacity require separate checks by appropriate personnel. If those inputs are unknown, show a conditional scenario and outstanding checks, not a dispatch-ready fleet recommendation or completion time.

**Medical:** qualified people determine clinical urgency and required capability under a later approved protocol. The product helps allocate an available suitable team, coordinate transport and recipient acceptance, and track handover/care separately. Population alone cannot determine a patient-specific medical team or drug/equipment requirement. Area-level health-service planning and individual emergency dispatch remain distinct.

### Synthetic arithmetic example, independent of the older demo fixture

A fictional planning card shows modeled exposure 120 people and **24 people with reviewed assisted-evacuation requests**. Presence/evacuation needs for the rest remain unknown. A qualified operational reviewer supplies illustrative assumptions of two usable resources, six passenger places per trip each and two feasible trips in the planning window: `2 × 6 × 2 = 24 passenger movements`. This is conditional arithmetic, not a safety/capacity norm, verified boat specification, time guarantee or medical transport plan. If feasible trips are unknown, capacity remains conditional. Losing one resource changes this scenario to 12 movements; 12 known requests are uncovered, and the coordinator must revise the plan. The exposure estimate remains 120; it never becomes '120 people rescued'.

For a separate fictional one-day food-pack target of 120, with a planner-selected allowance of one pack per person and 50 matching packs already confirmed usable/received, remaining need is 70 packs. Another accepted mission plans 40 in that period; it leaves 30 unassigned, while all 70 remain undelivered until confirmed receipt. No universal aid standard or procurement instruction is implied. If coverage scope/overlap is unknown, do not claim an exact unassigned gap.

## Emergency desk and allocation

Queue shows reported urgency, received/observed time, validation state, clinical assessment state, location confidence, owner and allocation status. A non-clinical coordinator can review attribution, identity, location, repeat reports and available corroboration; that does not clinically declare a patient non-urgent or determine treatment. The app never labels an unanswered request false or low priority merely because it is unverified.

Capability matching is proposed decision support, with an explanation: required capability, evidence of team qualification, availability/window, transport/resource needs, existing workload, contact/acceptance and destination coordination where relevant. Closest is not automatically suitable. Medical case narratives are visible only to necessary roles, not general volunteer map markers.

Assignment is a team-specific accepted commitment, not merely a pin. Plan changes preserve history and flag relevant missions. Resource allocation, preparation and any urgency decision are distinct; requests remain open if no suitable team is available. Validation/clinical policies, authority, escalation and partner integrations are unresolved; a prototype can use a clearly fictional qualified-review fixture without claiming actual clinical service.

## Resident experience

Low-friction request by the accepted chat/real telephone channels, or a proxy/field reporter when the person cannot contact the desk. Preserve location/landmark, number needing assistance, requested help and source/time, plus ambiguity. Any medical narrative is restricted. The resident may update location, cancel/correct a request or report that the team has not arrived through reviewable events.

Own-request progress: received → under review → accepted for coordination → suitable team being sought → assignment accepted → preparing → team-reported en route → arrival/outcome reported → separately confirmed outcome. Clinical assessment and each need remain independent; these labels do not diagnose or guarantee help.

Timing: before assignment, 'No team confirmed; arrival time unknown.' After a responsible accepted plan, show a **team/coordinator-provided estimated arrival window**, update time and limitations. An area relief trip does not prove that this household is included. Before the team travels, its planned window is distinct from a reported en-route estimate. If delayed, unreachable, cancelled or outdated, revise/withdraw the old window and assign an update owner; no fake countdown. Outbound SMS/callback, automated travel ETA and secure reference verification remain channel/security scope decisions; no such integration is enabled.

Residents without connectivity also need an assessment mission, local contact/community liaison and field reporting path. Satellite estimates identify where to investigate; they do not ensure every person is reached. No new public household map is proposed.

## Proposed experiences to design next

| Experience | Main decision/action |
|---|---|
| Area map and daily briefing | Where can our team contribute most, and why? |
| Area detail and mission planner | What target, load, capabilities and coverage does this mission require? |
| Emergency desk | What needs immediate human attention, what has been validated/assessed, and who can respond? |
| Team mission view | What is our accepted brief, preparation list, location/window and current instruction? |
| Resident request/status | How do I ask/update, and what help is actually confirmed for my request? |

Team/resource roster supports planner and dispatch; it need not become a separate hackathon navigation destination. The previous three page names are not a constraint. Do not generate a replacement screen pack until the user reviews these jobs and operating model.

## Small coherent prototype recommendation

One fictional locality, three areas, two declared team capability profiles, one reviewed area source package, one relief plan and one emergency case with a synthetic qualified-review outcome. Demonstrate:

1. A leader sees underserved areas and existing plans, not just a flood map.
2. The leader opens an area and creates an editable target/load/capability plan with explicit assumptions and missing checks.
3. A controlled real telephone emergency intake clarifies the resident's location/need; operator review and a fictional qualified clinical/rescue decision remain separate.
4. The coordinator selects a suitable available team; acceptance gives the resident a truthful status and conditional team-provided window.
5. A resource failure reduces scenario capacity, flags the linked mission and withdraws its outdated resident window; unrelated plans stay unchanged.
6. A scoped field report discovers an unreported need and updates assessment/coverage, without treating the whole area as fully assessed.

AI contribution: multilingual clarification, evidence-linked area brief/proposed updates, and explanations of missing information or changes to a reviewed mission. Computation of quantities/capacity, permissions and allocation state is deterministic. Clinical decisions and access authorization stay with appropriate humans. This is a proposed demo, not run evidence or proof of novelty/field readiness.

Deferred: complete inventory suite, live multi-feed guarantees, own depth model, automatic route/ETA calculation, continuous GPS, offline sync and unsupervised clinical dispatch. Previous 11–14/15–20 person-day estimates do not cover this revised scope reliably; re-estimate after workflow/capability/source/phone gates. No package/service/account/deployment is selected or enabled.

## Review gates and meaningful checks

The human has settled who proposes routine missions and assigns emergencies. Next define routine commitment approval, which organized team types/locality we represent, the area-response-mode evidence and what qualifies a medical/rescue decision. Then validate the area input package and smallest end-to-end scenario before page layout. Direct responder validation would strengthen this hypothesis, but none has occurred and online-only discovery remains the present boundary.

Future checks: no duplicate/unknown-count inflation; map/list same object; no promised-as-received aid; no exposed-as-evacuation-demand conversion; time/capacity units and crew basis explicit; no resource double booking; urgent report visible during incomplete validation; qualified assessment distinct; team acknowledgment required; no unassigned ETA; delay removes stale window; inaccessible/silent needs remain visible; outcome/receipt/care distinct. No application tests or operational actions have run.

Documentation validation: 14 touched Markdown files and 97 local links checked; whitespace/sensitive-pattern checks passed; R1–R12 and new references V1–V5 each appear once in their registers. Public sources were accessed as noted; no application tests or integrations ran.
