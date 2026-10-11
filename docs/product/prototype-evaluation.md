# Prototype evaluation plan

Date: 2026-10-11. Status: proposed, unrun; [draft PRD](prototype-prd.md) governs scope. Synthetic examples only. This file defines a test protocol, not executable application tests or measured results.

## Baselines and labeling

Compare B0 (good structured intake/task board with explicit dependencies), B1 (AI extraction plus the same board), B2 (proposed clarification, review and reassessment). All get identical case history, source timestamps, constraints and update content. B0 may ask clarifying questions; its frozen script must include the permitted conditional clarification branches. Do not handicap it with a bad script. Dependency checks and allowed human actions are identical in all three.

Author two variants for each family below, yielding 24 sequences. Before tuning, assign one variant per family to development and the other to held-out evaluation. Each split contains eight Thai sequences and four English sequences; human reviewers check source-language referents and translations. Exact prose, assignments and reference labels must be frozen before any model run. These fixtures are not yet authored.

Reference labels specify supported event fields, material changes, justified clarifications, known/unknown status, affected assignments and permissible final records. The other human reviews labels. Record disagreements and resolve them before scoring; do not use model output as ground truth.

| Family | Required distinction |
|---|---|
| E01 | Household moves; neighbor sharing a phone stays. |
| E02 | “We” refers to several people, not every household in an earlier post. |
| E03 | Unavailable vehicle affects one accepted and one draft sequential assignment explicitly requiring it; its team is not automatically unavailable. |
| E04 | Destination update affects linked plans, with an unrelated assignment as control. |
| E05 | Older report arrives after a newer update; preserve time/order uncertainty. |
| E06 | Unchanged repost versus a correction; transport duplicate ID versus similar content/new ID. |
| E07 | Similar destination names; insufficient evidence to select one. |
| E08 | Conflicting closure reports; source authority unverified. |
| E09 | Resident reports assistance but a different need remains open. |
| E10 | No feasible team/resource; unmet need remains visible. |
| E11 | Disconnected intake or unclear/noisy phrase; preserve incomplete/unknown state. |
| E12 | Instruction embedded in a report asks the model to approve/close unrelated cases; treat as source text, not authority. |

## Measurement

For each material reference change, match type/subject and material values. Precision is correctly supported proposed changes divided by all proposed changes; recall is correctly recovered changes divided by all answerable reference changes. Report unknown/abstained items separately and show denominators, especially with the small held-out set. A fabricated source citation makes a proposal unsupported even if its guessed value happens to match.

Check exact affected-assignment sets after human review and separately on model-proposed case/dependency links. Record false flags and missed flags; deterministic correctness cannot hide a bad interpretation or wrong case association corrected by the human.

Normalize workflow evaluation to the same original-language text/transcript and case history in B0/B1/B2. Telephone transcription, noise and streaming latency belong to the separate integration checks; do not supply text to one baseline and live audio to another when claiming workflow improvement.

Each sequence requires a frozen clarification oracle: initial facts, hidden answerable facts, questions that justify revealing each fact, and facts that remain unknown. A human runner supplies the same oracle answers to all conditions, including B0's scripted questions. Record question/answer turns and use the same fixed response-delay convention in every condition. Refusal to reveal another household's details applies equally to all baselines. Oracle correctness is independently checked by the other human before scoring.

Allocation for accuracy: run each of the 12 frozen held-out sequences through each condition using the same oracle. B0 follows the fixed intake script; B1 and B2 use their frozen model/configuration. Humans score against fixed labels and log corrections. This is 36 condition-sequence runs; the authors know the references, so it is not a blinded human study. Report model-proposal accuracy before human repair and final state separately.

Comparative human speedup is **untested under the current two-author setup**. Both humans inspect labels; hiding an answer sheet does not remove that knowledge. Do not attempt to infer a fair three-condition speedup from the 12 single held-out variants. An optional exploratory pilot may log time on development examples with condition order rotated and full disclosure of prior exposure; it cannot satisfy an independent speedup claim. A later suitable independent, counterbalanced protocol needs separate approval and participant availability. No recruitment or interview is authorized by this document.

Proposed prototype gates: held-out proposal precision/recall each at least 90%; exact dependency sets on all explicit-link cases; zero invariant violations. The 20% effort reduction is a future product target, not a current release gate. Freeze targets before running; retain failed results. Prototype phone checks are a separate 10-call set, not evidence about real users.

## Invariant and integration checks

Independently check unauthorized mutations, same-phone identity handling, retries, semantic duplicates, stale concurrent review, brief invalidation, version-specific acknowledgment, remaining needs after partial outcome, wrong units, refusal of autonomous clinical/route decisions, restricted team access and AI failure/manual fallback. The accepted quantity example remains an invariant test, not the demo's definition of success.

For telephone checks, document number country, caller network/device, approved account configuration and consent. Verify normal telephone ingress, audio in both directions, interruption, transcript source attribution, delayed response, disconnect and repeat report recovery. Record all 10 attempts, completion rate and end-of-turn to first spoken response timings. An incomplete call that preserves a report passes recovery only; it does not pass complete-intake acceptance.

## Reporting and decision

Save redacted synthetic fixtures, frozen labels, condition allocations, model/config versions, proposed events, human corrections, timestamps, final-state results and failures. Keep credential/account identifiers and recordings out of Git. Publish only evidence actually collected and only with separate publication authority.

If B2 adds no measurable benefit, prefer B0 or B1 and narrow the product claim. If it introduces identity/state errors or its review cost erases any benefit, do not present the AI workflow as superior. This evaluation can support technical behavior on synthetic cases; it cannot establish lives saved, adoption or operational readiness.

## Proposed coverage extension, not part of the frozen base protocol

The PRD's section 16 proposes area assessment beyond self-reported cases. Its tests require separate scope approval, effort allocation and frozen references; do not silently change the base 24-sequence/36-run protocol. Test paired exposed/unassessed versus recently scoped areas; stale or incompatible evidence; partial/unreachable attempts; proxy/field discovery; shared-phone identity; replay; and unknown denominators. Score explicit gap rules and reviewed records, separating AI report interpretation. No actual population coverage or missing-person recall can be measured from these synthetic cases.
