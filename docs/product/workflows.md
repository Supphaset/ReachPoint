# Candidate workflows for discussion

These are synthetic thought experiments, not an approved operational protocol or final screens. Invariants and quantity example live in [requirements](requirements.md).

## Report → review → follow-up

1. A household contacts a coordinator by chat or an inbound phone call. Capture reported facts and source/time; channel feasibility is open.
2. Establish a candidate household/location with uncertainty. A shared phone is only contact evidence. A repeated report creates a matching proposal, not an automatic merge.
3. AI may propose separate needs/events and clarification questions linked to original evidence. A designated reviewer decides what becomes authoritative; designation is open.
4. A team makes a commitment. Record progress, failure/expiry and delivery reports separately from receipt. Confirmation responsibility is open.
5. Partial confirmed aid reduces only the relevant need. The rest remains outstanding; medical referral/care follows separate records.
6. Corrections retain original evidence and approval history. Follow up outstanding and unconfirmed outcomes; hand over unresolved uncertainty.

## Contradiction and displacement scenario

“The volunteer brought six packs, not eight. My mother still needs medical help. We're staying with our neighbor now.”

Propose three separate changes: a disputed quantity, continuing medical need and reported location change. Clarify identity/location before linking; keep the earlier receipt record visible pending approved correction. Use the accepted quantity example to inspect the result. Do not infer medical urgency or confirmed care from this statement.

## Exceptions to decide

| Situation | Proposed behavior to discuss | Unresolved authority |
|---|---|---|
| Same phone, different household | Keep distinct candidates pending evidence | Who may link/merge/unmerge? |
| Team reports delivery, household disagrees | Preserve both accounts; receipt remains disputed | Who resolves and how? |
| Commitment expires or team unreachable | Flag follow-up; keep need visible | Expiry/cancellation policy |
| Connection drops during intake | Preserve/retry without double-counting | Storage, sync and recovery semantics |
| Flood report differs from gauge | Display types and provenance separately | Supported sources and interpretation |
| Medical need is unassessed | Keep uncertainty and attention visible | Qualified reviewer/handover |

## Proposed evaluation, later

Compare manual spreadsheet/chat review, simple structured extraction and proposed conversational reconciliation on the same synthetic sequences. Include duplicates, ambiguous identities, corrections, partial delivery, stale commitments, displacement and unassessed medical reports. Score attribution, household matches, accepted-event quantities, false closure, uncertainty preservation and reviewer effort. Humans must approve test labels and targets; no claims of clinical efficacy or disaster impact from synthetic results.
