# Relief Ledger: operational rethink after the quantity-demo critique

Date: 2026-10-11. Status: research and proposed direction; no implementation approval.

## Human correction and revised recommendation

The user rejected requested-versus-received quantities as the central wow factor: assistance depends on the situation, and disasters do not guarantee full satisfaction of each request. That critique supersedes the previous recommendation to center the demonstration on a two-unit gap. The quantity example remains a useful correctness test under the [requirements](../product/requirements.md), not a validated definition of operational success or a household entitlement.

The new research question is: **when help is scarce and information changes, can Relief Ledger help a coordinator discover which cases still need attention and which response plans require reassessment?**

Proposed primary job: keep current needs, uncertainty, response ownership and changes visible to a coordinator. AI could interpret updates and draft questions/briefings; accountable humans set priorities and approve response actions. This is a product hypothesis, not an approved command system or rescue protocol.

## What this research round found

| Source | Finding | What it supports; what it does not |
|---|---|---|
| [Thaiwater Hat Yai November 2025 retrospective](https://www.thaiwater.net/uploads/contents/current/2025/hatyai_nov2025/summary.html), O1 | Its water-management section highlights fragmented data, unclear priorities and coordination failures. | Supports examining decisions and response coordination. It is an institutional retrospective, not measured evidence that our software would have changed outcomes. |
| [Thai government response briefing, 26 November 2025](https://www.prd.go.th/th/content/category/detail/id/33/iid/447819), O2 | Describes combining reports, assigning zones and equipment, and competing demands for boats with operators. | Resource availability must include people/capabilities and competing uses. A briefing describes government actions and claims, not an independent performance audit. |
| [Flood-response repository issue #37](https://github.com/winn/thaifloodhelp/issues/37), O3 | Contributor warns stale pending cases can make prioritization harder; proposes call-center updates and deduplication. | Direct evidence of a developer-raised workflow concern. One open issue is not confirmed prevalence or proof that Jitasa has the alleged deficiency. |
| [winn/thaifloodhelp README](https://github.com/winn/thaifloodhelp), O4 | Describes Gemini extraction from Thai posts, human review, duplicate detection, filters and natural-language search. | Strong overlap with our prior AI-intake proposition. Documentation claims were read; runtime and production deployment were not verified. |
| [INSARAG flood-response reference note](https://insarag.org/wp-content/uploads/2025/08/Flood-Response-%E2%80%93-Capacity-Building-%E2%80%93-Technical-Reference-Note.pdf), O5 | Distinguishes flood-response skills and capabilities and describes context-specific hazards. | A nearby available volunteer is not automatically an appropriate responder. This note does not authorize us to write operational rescue rules. |
| [Thai PBS / The Active recovery coordination reporting](https://theactive.thaipbs.or.th/news/social-movement-20251203-2), O6 | Describes different recovery functions, community coordination and existing maps of services/resources. | Response involves specialized work and changes by phase. Reporting is secondary evidence, not a current product feature audit. |

These findings move the discussion beyond counting supplies. They also weaken originality claims for AI extraction, deduplication, maps and chat-based search. None of those should carry our innovation argument alone.

## Three decision failures worth investigating

### 1. The case list stops reflecting the situation

A report can remain pending after a household moves, receives some assistance elsewhere, changes its request or becomes unreachable. Many repeated posts can make one situation appear larger; few reports can conceal a poorly connected community.

Proposed support: display last contact, source, unresolved questions and a reviewable account of what changed. During an inbound call, ask a targeted question that resolves an actual uncertainty. A future authorized outbound workflow could be investigated, but no outbound integration or contacting residents is authorized here.

Do not expire an unresolved need into “resolved,” assume silence means safety or rank need by message count. If communication fails, the current situation remains unknown. This extends the issue's concern; it does not adopt all its proposed fixes.

### 2. A real need has an unsuitable or unowned response

“A volunteer is nearby” leaves important questions unanswered: can that team perform the task, is it already assigned, does it have the necessary crew/equipment, has someone accepted responsibility, and is the reported location usable?

Proposed support: present verified team capabilities, current commitments and missing prerequisites alongside the need. Differentiate “no suitable option confirmed” from “low need.” Record human decisions, ownership and acknowledgment. Never infer competence from proximity, a job title or ownership of a boat.

This does not solve resource shortages or create a fair prioritization policy. Human governance, local procedures and current field assessment remain necessary.

### 3. A new report invalidates an earlier assumption

A team becomes unavailable, an intended destination stops accepting people, or a resident reports having moved. A case-based dashboard may contain all the facts while the coordinator still has to identify which plans depend on the changed fact.

Proposed support: AI extracts the reported change and its evidence; a reviewer resolves ambiguity. Once approved, explicit links identify affected assignments and briefings. The system queues reassessment and drafts an explanation of what changed, what is uncertain and who owns the next check.

Dependency checks and capability constraints should be deterministic after review. The model must not invent routes, infer passability from water level or automatically dispatch an alternative team.

## Compare possible prototype centers

| Candidate | Why it could matter | Judge-facing weakness | Assessment |
|---|---|---|---|
| Supply accounting | Correct partial outcomes and traceability. | Useful but not a compelling central disaster decision; user rejected it as the wow factor. | Keep as background correctness. |
| AI intake and deduplication | Reduces manual structuring of reports. | A public Thai flood-response project already describes much of this. | Necessary entry capability, insufficient headline. |
| Current-case verification | Makes uncertainty and stale information visible; supports targeted clarification. | Could look like a call-center status tool; actual effort savings unproved. | Strongest bounded problem lead from this round. |
| Change-aware response review | Connects a new field update to assignments and ownership that require reassessment. | More engineering, governance and data dependencies; novelty unverified. | Strongest proposed demonstration if limited to one scenario. |
| Autonomous urgency ranking/rescue routing | Visually dramatic. | No validated policy, field model, qualified governance or safe-route data. | Do not propose as approved behavior. |

Recommendation: investigate **current-case verification plus one change-aware response-review loop**. This stays inside Relief Ledger's coordination problem, but changes the proposed center of gravity from a delivery ledger to current situational understanding and accountable next actions. Do not expand into a comprehensive command platform.

## A stronger synthetic demonstration

All people, locations, sources and operational events below must be fictional. This is a scripted design test, not proof of a working model or advice for an incident.

Initial view: several cases, two response teams and a human-approved plan. It shows reported needs and operational attention separately from available options. Team and destination statuses have sources and timestamps. No real map, route or live feed is implied.

1. A resident calls with an update: “The people in the old post have moved to the community building. I'm calling for my neighbor; their address is different.” The assistant asks which people moved and which household still needs help. It proposes changes rather than silently merging everyone.
2. A team reports: “Our vehicle is unavailable. We haven't started the assigned task.” The assistant distinguishes assignment acceptance from departure and proposes an availability update.
3. A verified fictional destination update says the community building is no longer accepting new arrivals. The reviewer approves the source update.
4. The system identifies plans referencing that destination or the unavailable team. It shows affected tasks, the supporting changes and unresolved prerequisites. A reported relocation is not automatically treated as receipt of aid or resolution of need.
5. The coordinator asks, “What changed, what needs reassessment, and what do I need to verify before approving another option?” The system provides a concise, evidence-linked brief, candidate resources with explicit known constraints, and the missing checks. It does not claim any alternative is safe or dispatch it.
6. The coordinator chooses an action and owner in the scenario. Acknowledgment is visible. Other cases remain visible even when no suitable resource is available.

Potential wow factor: **one ordinary-language update exposes several now-invalid response assumptions, and the coordinator can see exactly what needs attention next.** This is more consequential than a numerical shortfall, but its usefulness and distinctiveness still need testing.

The model's part is interpreting referents, distinguishing reported events and producing focused clarifying questions and evidence-linked briefs. The trusted system's part is maintaining reviewed state and explicit dependencies. Test whether a human can achieve the same result equally well with simpler tooling.

## What the product experience would emphasize

- A coordinator's “Needs attention” view: changed reports, missing owners, unavailable assigned resources and plans awaiting reassessment. No opaque AI priority score.
- A case timeline: reported situation, last contact, uncertain identity/location, needs, review and response history.
- A response view: tasks, accountable owners, acknowledgments, verified capabilities and unresolved prerequisites.
- Phone/chat intake with adaptive clarification; source evidence stays accessible to the reviewer. Real inbound telephone access remains a requested capability with feasibility unresolved.

These are proposed functions, not built screens or approved navigation. A map supports context, with uncertainty and freshness; it does not certify a safe route. Quantities, partial receipt and care/referral distinctions remain valid requirements underneath the experience.

## Evaluation that matches the revised claim

Do not measure success by percent of requests fulfilled: capacity may make fulfillment impossible. Evaluate the narrower claim the prototype can demonstrate.

Compare a structured case/task board, that board with AI extraction only, and the proposed clarification plus change-review workflow. Give each the same sources, history and human-approved constraints. Hold out variations from examples used to tune the system.

Measure missed affected assignments, falsely flagged assignments, unsupported claims, wrong case links, premature closure, necessary clarification questions and total human time to produce an accurate reassessment brief. Record how often reviewers must repair proposals. Separate a correctly preserved unknown from a missed answer.

Include: an unchanged repost, a late-arriving older update, a false closure report, a team unavailable for a different task, a shared phone, an ambiguous destination name, an unreachable resident and no feasible resource. Require the system to retain unmet needs under scarcity and to show uncertainty when evidence is inadequate. These are prospective tests; no scores exist yet.

Reject the hypothesis if simple filtering plus explicit task links performs equally well, review overhead dominates, or the proposed AI behavior relies on guessing clinical urgency, routes or team competence. A synthetic benchmark establishes technical behavior, not rescued lives or field impact.

## Remaining homework and boundaries

We still need a credible desk-level procedure describing who confirms situation changes, controls assignment decisions and acknowledges work. A named operator, partner, local demand estimate, system integration and prioritization policy remain unknown. Existing tools' change-review behavior must be checked before claiming a gap.

No quantity-centered demo should be presented as the current recommendation. No framework, provider, implementation, outbound calls or deployment has been approved. See the [source register](sources.md), O1–O8, for access details and limitations.

Documentation validation: checked four affected research files and resolved 13 local links; no trailing whitespace or matches in basic credential/private-machine-path checks. No application or competitor runtime tests were performed.
