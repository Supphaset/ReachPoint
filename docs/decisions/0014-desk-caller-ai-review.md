# 0014 — Caller table and desk AI review

Date: 2026-10-15. Status: **Accepted by the user** for the synthetic demo in this chat: “change table name to callers and implement features in \"/desk\" api”, following the transport/emergency draft and optional volunteer summary request. The user revised routine/non-emergency from Level 0 to **Level 3**. No real clinical protocol, production authentication, deployment or paid service is approved here.

## Decision and terminology

`callers` stores original caller-confirmed form/chat/voice details. Startup migration renames `help_requests` while preserving retained values. **Caller-confirmed** means the caller approved their submission, not independently verified.

A **desk review** is a versioned operational recommendation: boat/truck candidate or needs assessment; Level 1a (suspected medical emergency), 1b (urgent flood rescue), 2 (priority assistance), or 3 (routine/non-emergency); AI/Human provenance; evidence and reasons; optional volunteer preparation summary. Unknown stays unresolved. **Human reviewed** records a review action, not professional accreditation or a clinical assessment. Immediate reported danger remains visible before AI finishes and takes priority across 1a/1b.

Original statements remain separate from reviews/history so AI cannot rewrite reports. AI results require caller quotes; failure requires human review rather than defaulting to routine. Human changes use input/review revisions and survive older or repeated AI results. Summaries use supported excerpts about water, medication, mobility and other preparation needs, never prescriptions. Their absence does not block review or case approval.

## Consequences and limitations

The desk gets `/api/desk` reads plus AI/human review actions. New confirmed callers and unreviewed rows loaded by the desk receive background review using the existing Gemini configuration. Existing validated allocation tiers, clinical gates, case approval and team acceptance remain separate; recommendations never dispatch or close cases. The optional summary appears only in the responding team's active accepted job and leaves the team view on closure/hand-back.

A fixed numeric boat/truck cutoff was rejected: indoor depth is not an access-path assessment, and suitability depends on actual conditions and qualified responders. [NWS flood guidance](https://www.weather.gov/safety/flood-during), [Defra rescue-asset guidance](https://www.gov.uk/guidance/applying-to-join-the-defra-flood-rescue-national-asset-register), accessed 2026-10-15. Medical signs justify qualified escalation, not diagnosis. [WHO IITT](https://www.who.int/tools/triage), accessed 2026-10-15; facility-based guidance is not a validated telephone/AI protocol.

### Presentation amendment — 15 Oct 2026

Transport/evaluation amendment, 16 Oct 2026: [0017](0017-desk-depth-threshold-and-evaluation.md) adds the user-selected 50 cm boat planning preference and explicit unmet-need Level 2 guideline. The numeric-cutoff rejection above remains historical; route clearance, clinical assessment and human-approval constraints remain in force.

The user approved implementation of the selected “Preparation first” draft (“ok implement it”). `/desk` uses a left request-card queue with the reported area as its headline and the situation underneath. The selected request shows the optional volunteer preparation brief and key facts beside the human review form on wide screens. Original caller fields, recommendation reasons, supporting quotes and review history remain accessible through disclosure controls. Narrow screens switch between the queue and request details. Missing area information stays explicitly unknown; the UI does not infer a location or change review/dispatch semantics.

Local SQLite/single-process and demo-identity limitations remain. Mocked tests do not establish live Gemini accuracy or real operational suitability. A database containing both old and new caller tables is refused without deleting either, requiring reconciliation rather than guessing which records to keep.

Affected documents: [requirements](../product/requirements.md), [API contract](../../contract/api.md), [README](../../README.md). Earlier decisions retain their historical wording.
