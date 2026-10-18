# Comparisons and inspirations

Sources C1–C4 in [sources](sources.md), checked 2026-10-11. These are published descriptions, not hands-on feature audits.

| Project | Supported description | Questions to investigate; no absence claim |
|---|---|---|
| MySelamat | APU describes SOS, social-media crowdsourcing, verification, coordination and route planning | How are identities, contradictions, corrections, partial deliveries and confirmed outcomes handled? |
| FloodMesh | ETDA describes an offline flood-alert and rescue-coordination toolkit | What works without internet, how is shared state reconciled and what is its operational deployment? |
| Alert X | Call for Code describes incident analysis from live video, nearby services and reports to authorities | Where does human review occur; does it track household outcomes? |
| Project OWL | Call for Code describes a hardware/software mesh for disaster communications | What transport assumptions and adoption lessons matter for us? |

None of these sources establishes that reconciliation or fulfillment tracking is absent. The comparison below focuses on the implemented synthetic prototype; operational differentiation remains unvalidated.

## Winning-project references

The user-supplied 2024 list and individual URLs remain in [context](../context.md). Individual rechecks and access limitations are recorded under W1–W9 in [sources](sources.md); several project descriptions were rechecked on 2026-10-11. None was runtime-tested.

Our interpretations: useful niches can emerge from constraints or consequential moments; distinguish operator from beneficiary; complete actions and verify outcomes; ground suggestions in current facts; place assistance where uncertainty occurs; let beneficiary needs shape experience. These are team interpretations, not published judging explanations. Awards do not prove adoption or efficacy.

## Operational comparators added 2026-10-11

The deeper review (removed 2026-10-11; in git history) examines stronger baselines than award entries: Thai Red Cross PhonPhai (request/resource/delivery coordination), Sahana Eden (requests and fulfillment stages), WFP SCOPE (beneficiary and transfer reconciliation), and KoboToolbox (linked follow-up data and audio processing). Evidence and limitations are registered as R1–R10.

These establish material feature overlap. They do not establish whether conversation-level corrections, ambiguous identities or partial household receipt are handled adequately. ReachPoint must test its proposed reconciliation advantage; a map, dashboard or speech transcript alone is insufficient differentiation.

## Local AI-intake comparator and revised focus

[winn/thaifloodhelp](https://github.com/winn/thaifloodhelp) describes Thai social-post extraction using Gemini, human review, duplicate detection and natural-language search (O4). These capabilities overlap our proposed AI intake; runtime is untested. Its [issue #37](https://github.com/winn/thaifloodhelp/issues/37) raises stale-case concerns (O3), but is not proof of an unmet market or of deficiencies in another platform.

The operational rethink (removed 2026-10-11; in git history) replaces the rejected quantity-gap demo recommendation with a proposed test of current-case verification and response reassessment when information changes. Field distinctiveness remains unproven.

## How ReachPoint differs

Checked 2026-10-13. ✓ = supported within the stated scope; partial = a narrower capability; ✗ = absent from the plain channel alone; unknown = evidence insufficient. Competitor entries describe published material, not runtime tests. ReachPoint entries describe code/demo behavior, not rescue outcomes.

| Workflow | AI reads messy messages | Every AI fact quotes the caller | Asks for missing facts by chat/voice | Exact location from caller (GPS/map) | Finds people who never called (quiet zones) | Honest arrival times withdrawn when boat fails | Whole family assigned to one team | Per-family status link |
|---|---|---|---|---|---|---|---|---|
| 1669/1784 hotlines | unknown | unknown | partial | unknown | unknown | unknown | unknown | unknown |
| LINE groups / Facebook posts (plain channel) | ✗ | ✗ | partial | partial | unknown | unknown | unknown | ✗ |
| Shared spreadsheets (Cajun Navy style) | ✗ | ✗ | partial | partial | unknown | unknown | unknown | unknown |
| thaifloodhelp | ✓ | unknown | unknown | partial | unknown | unknown | unknown | unknown |
| ReachPoint (synthetic prototype) | ✓ | partial | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

Hotline “partial” means human call-taking, not verified AI chat. Plain groups permit human follow-up and shared location links; the channel alone does not provide the listed AI or family-status workflow. Spreadsheet “partial” refers to reported callback vetting and recorded locations, not a caller map interface ([rescue-practice review](real-rescue-practice.md)); its Cajun dispatch source could not be reopened today, so other capabilities remain unknown.

[thaifloodhelp's README](https://github.com/winn/thaifloodhelp) describes Gemini extraction of Thai posts, human review, vector duplicate detection, natural-language search and a mobile-first interface. Coordinates are stored, but a caller GPS/map capture flow was not established; a stated policy to extract only explicit facts does not establish field-level quote enforcement. ReachPoint's quote column is partial because [request extraction](https://github.com/Supphaset/ReachPoint/blob/e3432e5d36f6f7578e86422ad6dca670d682b303/api/intake/extract.py) checks field quotes, while the [chat record](https://github.com/Supphaset/ReachPoint/blob/e3432e5d36f6f7578e86422ad6dca670d682b303/api/intake/conversation.py) does not attach a quote to every field.

ReachPoint makes coverage gaps actionable: no calls leave a segment unchecked, and field discoveries become reviewed cases. It makes status accountable: a failed boat withdraws affected estimates instead of leaving families with stale times. Its grounded request extraction gives reviewers caller quotes and code checks, while human review remains necessary; these are defensible demo differences, not claims that other systems lack them.

Evidence: [NIEM call-taking handbook](https://www.niems.go.th/1/uploadattachfile/2023/ebook/417715_20230405201236.pdf), [DDPM](https://www.disaster.go.th/home), [published channel review](https://rocketmedialab.co/flood-relief-system/), thaifloodhelp README above, and ReachPoint's [current flow](../OVERVIEW.md). Access methods and limits are in [sources](sources.md#judge-documentation-verification--2026-10-13).
