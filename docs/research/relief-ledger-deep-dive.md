# Relief Ledger: deeper problem and competitor review

Date/access date: 2026-10-11. Status: research and proposed scope; no implementation or MVP approval. Builds on the [brief](../product/brief.md), [requirements](../product/requirements.md) and [source register](sources.md).

Follow-up: the user rejected the quantity-gap demonstration as the wow factor. Its recommendation is superseded by the [operational rethink](relief-ledger-operational-rethink.md); retain this report as earlier research, not the current demo recommendation.

## Finding

Keep researching Relief Ledger, but narrow its differentiation hypothesis. A platform containing requests, maps, teams and delivery tracking substantially overlaps established humanitarian systems. The promising question is whether evidence-linked reconciliation of messy conversations helps a coordinator maintain accurate outstanding needs with less effort. That advantage remains untested.

Proposed positioning: **Relief Ledger helps coordinators turn conflicting calls and messages into reviewed records of what each household still needs.**

This is a workflow hypothesis, not a claim that competitors cannot do it. No customer, operational partner, adoption evidence or local frequency estimate has been established.

## What the evidence supports

| Evidence | Supported finding | Implication and limit |
|---|---|---|
| [IFRC emergency community-engagement guidance](https://solutions.ifrc.org/national-society-capabilitiesbuild-community-engagement-and-accountability/engage-and-be) (R9) | Identifies challenges in systematic feedback collection, continuous communication and coordination; unclear coordination can create unrealistic promises. | Investigate feedback-to-action work. Guidance does not establish how often household receipts are incorrectly reconciled in Thailand. |
| [UNICEF September 2024 regional flood report](https://www.unicef.org/media/162161/file/EAP-Humanitarian-SitRep-Yagi-Floods-18-September-2024.pdf) (R10) | Reports Thai flood-related disruption to roads, telecommunications and electricity, alongside essential household needs. | A telephone channel requires functioning telecom service; it is not an offline solution. A record cannot overcome inaccessible roads or inadequate supplies. |
| [Thai Red Cross PhonPhai description](https://rtrc.redcross.or.th/ewt/rtrc_web/New_appphonphai.php) (R1) | Describes coordinated requests, maps, resource allocation, reporting and delivery tracking. | Broad local feature overlap. This is an institutional product description, not our runtime audit. |
| [PhonPhai manual on a DDPM domain](https://backofficeminisite.disaster.go.th/apiv1/apps/minisite_TRANG/204/content/11058/download?filename=8ed927a2472c548a5e7dcfa2bcd14227.pdf) (R3) | Describes delivery tracking followed by entering recipient information. | Do not claim existing local systems stop at dispatch. Historical manual; precise recipient-confirmation policy and current implementation unverified. |

The evidence supports a relevant problem area, not product-market fit. We have not established that the main bottleneck is data reconciliation rather than staffing, transport, supply, access or trust.

## Stronger comparators than other hackathon entries

All rows refer to documented capabilities. No product was installed or exercised; absence from a page means unknown.

| Comparator | Documented overlap | Consequence for our claim | Still unknown |
|---|---|---|---|
| PhonPhai (R1–R3) | Request coordination and delivery workflow in Thailand. | A generic Thai flood-coordination platform is weak positioning. | Conversational correction handling, partial household receipts, merge/unmerge behavior, APIs and review effort. |
| [Sahana Eden](https://sahanafoundation.org/) and [request guide](https://140-211-166-108-openstack.osuosl.org/wiki/UserGuidelines/Requests) (R4–R5) | Logistics, inventories, requests and resources; legacy request documentation distinguishes commitments, transit and fulfillment. | Separating a pledge from arrival is established practice. | Household-level reconciliation of free-form corrections; current deployment behavior. Legacy guide retrieved through search extraction; direct fetch failed. |
| [WFP SCOPE introduction](https://usermanual.scope.wfp.org/cash-accounts/content/common_topics/introduction/1_introduction.htm) and [cash reconciliation manual](https://usermanual.scope.wfp.org/cash-accounts/content/cash_accounts/performing_distribution_reconciliation/performing_distribution_reconciliation__cash_based__.htm) (R6–R7) | Beneficiary management, deduplication, delivery tracking and comparison of instructed transfers with provider reports. | Reconciliation is not a new humanitarian concept. | Suitability for a small flood-response team; cash transaction reconciliation is not identical to informal in-kind household reports. |
| [KoboToolbox dynamic linking](https://support.kobotoolbox.org/dynamic_data_attachment.html) and [audio processing](https://support.kobotoolbox.org/transcription-translation.html) (R8) | Linked follow-up projects, audio transcription/translation and review. | Forms plus longitudinal records plus speech processing form a serious baseline. Voice transcription alone is insufficient differentiation. | Performance on our scenarios and total configuration/review effort. Audio forms are not proof of inbound conversational telephone support. |

The strongest practical baseline is a well-designed intake script or form, linked case records, explicit receipt/commitment fields and deterministic calculations. Compare against that, not a deliberately confusing spreadsheet.

## Three possible emphases

| Proposed emphasis | Advantage | Weakness | Recommendation |
|---|---|---|---|
| Broad operations platform | Shows many requested features. | Heavy competitor overlap and too many dependencies for a two-person prototype. | Do not lead the hackathon story with breadth. |
| Conversational intake | Accessible resident interaction; visible AI capability. | Transcription and basic slot collection are familiar; identity and telephone feasibility remain unresolved. | Use it as the entry point into a consequential reconciliation case. |
| Conversation reconciliation and unresolved-needs review | Connects corrections and contradictions to a decision the coordinator must make. | May increase review workload; differentiation and reliability unproven. | Best hypothesis to test next. |

## Proposed primary user and bounded job

Primary user hypothesis: one coordinator at a local response desk handling household reports and team updates across a shift. The beneficiary is the household whose unmet need should remain visible. A named organization, language mix, volume, shift procedure and authority to confirm receipt are still unknown.

Bounded job: **after a new report arrives, identify what changed, review the evidence, and determine what remains outstanding and who has committed to help.**

Proposed initial demonstration: one relief item, explicit units, a few synthetic households, two teams and an accountable reviewer. Keep ambiguous identities separate until resolved. Medical reports can remain reported needs awaiting qualified review; they must not imply an approved clinical service. A map can support locating a case, but should not be the main demonstration.

## The memorable demonstration

The demonstration should reveal a consequential discrepancy and show an auditable correction. Every input below is synthetic.

1. A household requests 20 water units. An approved record says 8 were received; a team commits to the remaining 12.
2. A resident calls: “The driver brought eight, but took two back. We only kept six.”
3. AI proposes a correction from 8 to 6 with the relevant transcript evidence. It distinguishes items brought from items retained and asks clarification when that distinction is uncertain.
4. The coordinator reviews the proposal. Only approval changes the record. Deterministic calculation shows 14 outstanding, 12 committed and 2 unassigned.
5. Replaying the same submission does not apply the correction twice. A neighbor calling from the same phone creates an identity question rather than an automatic merge.
6. A shift-handover summary points to the newly uncovered 2-unit gap and the still-unconfirmed commitment, with links to the supporting records.

The numerical states are from the accepted synthetic example. The dialogue and presentation are proposals. The system must also handle alternatives: “eight” could mean packs rather than bottles, two could have been transferred to a neighbor rather than returned, and a driver could describe stock issued rather than receipt. Do not manufacture certainty to make the demo flow.

The potential memorable moment: **a case that appeared fully covered reveals an unmet gap after a corrected receipt.** This is an operational hypothesis about useful presentation, not evidence of impact or a prediction of selection by judges.

## Proposed pages and why

These are documentation proposals only; no screens were built.

| Destination | Coordinator's question | Minimum useful content |
|---|---|---|
| Review | What does this new report change? | Source excerpt, proposed event, ambiguity, related cases and approve/edit/reject controls. |
| Case | What does this household still need? | Separate needs, commitments, reported deliveries, approved receipts, corrections and source history. |
| Operations | What needs attention now? | Unassigned remainder, unresolved reports and stale commitments. Optional map with source/freshness, no invented flood surfaces. |
| Response | Who has committed to do what? | Team assignment, item/unit/quantity, commitment state and delivery report. |

Resident phone/chat and a volunteer update view are entry points into these records, not reasons to build additional broad portals. For the proposed hackathon focus, defer standalone medical management, continuous volunteer tracking, flood-depth modeling, route recommendations and comprehensive inventory/organization administration. This is a scope recommendation; accepted requests remain recorded until humans approve an MVP.

## Where AI might earn its place

Potentially useful: interpret a correction expressed in ordinary language, distinguish a promise from a receipt report, connect an ambiguous update to candidate cases, ask a targeted question and produce a concise evidence-linked handover.

Deterministic responsibilities: quantities, units once approved, permissions, state transitions, repeat-submission handling, arithmetic and committed-versus-outstanding totals. The model should not infer household identity from a shared phone or turn a narrative into an approved fact.

An AI-generated summary without evidence, or a chatbot followed by ordinary CRUD screens, would leave the technical case weak. The project needs an evaluation showing an advantage on unstructured ambiguity while retaining correct reviewed state.

## Evaluation proposal and rejection conditions

No evaluation has run. Before choosing the final MVP, author a fixed synthetic test set with reference events and expected final states; split development examples from held-out examples. Have the other human check the references. State sample size, language, labeling procedure and limitations when reporting results.

Compare three approaches using equivalent information: (1) structured intake and deterministic case records, (2) transcript extraction without interactive clarification, and (3) proposed AI clarification plus reviewed event proposals. Separate model errors from errors corrected by the reviewer. Track time spent on clarification and review; count it rather than hiding it in a human-in-the-loop claim.

Cover same-household repeats, different households sharing a phone, conflicting names/locations, corrections versus additional requests, partial receipt, canceled commitment, duplicate delivery messages, unclear units, unrelated needs, noisy wording and interrupted calls. Test resubmission identifiers separately from semantic duplicate detection. No automatic household merge should be treated as safe merely because it passed a small synthetic set.

Measure:

- Accuracy of proposed event type, quantity/unit and household association; citation support for each proposed change.
- Unsupported assertions, missed ambiguities and reviewer corrections.
- Final outstanding/committed/unassigned values, accidental double counting and premature closure.
- Clarification and review time, unresolved-case rate, and telephone latency/failure behavior if later implemented.

Choose acceptance thresholds before testing. Reject or reduce the conversational approach if the strong structured baseline performs similarly, review costs erase the benefit, identity errors persist or dependable telephone access cannot be demonstrated. Synthetic improvements would support technical merit, not claims about real disaster outcomes.

## Next research priorities

1. Audit available PhonPhai manuals/demonstrations for partial delivery, corrections, case status and recipient confirmation; maintain an unknown column rather than assuming omissions.
2. Define one desk workflow and reviewer authority from an accessible SOP. Do not infer it from a software feature page.
3. Create the synthetic comparison set and reference states as documentation, then review whether the proposed AI tasks are essential.
4. Investigate inbound-phone country/number availability, costs, consent and recovery as feasibility research before making a prototype promise. No provider, model or stack is selected.

An integration or export to an existing response system is a possible adoption route, not an available integration. Establish API access, ownership and permission before claiming it. Online-only discovery limits what we can establish about willingness to adopt; this remains a visible risk.

## Validation and research limitations

Primary pages/manuals were checked online; source-specific access failures and dates are in the register. No competitor runtime, model, telephone service or operational workflow was tested. Some legacy documentation was available only through indexed extracts. Findings revise research assumptions, not accepted requirements.

Validation performed: checked the four affected research files, resolved nine local links, and checked trailing whitespace plus basic credential/private-machine-path patterns; no issues found. No application tests were needed for documentation-only changes. External fetch failures are recorded rather than counted as successful link checks.
