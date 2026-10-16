# 0018 — Minimal desk approval and caller review progress

Date: 2026-10-16. Status: **Accepted by the user** in this chat: “let phone help_type and location required other than that if it’s null can approve”. The user also asked whether approval would update caller progress.

The previous completeness gate in [0016](0016-automatic-desk-review-and-human-approval.md) disabled approval when AI could not resolve transport or location details. Replace that gate with only three nonblank original caller fields: `phone_number`, help type (existing schema `type`), and `location`. All other caller facts and AI outputs can remain null/unresolved. Transport null remains the existing `needs_assessment` representation; null urgency stays unknown. Keep the immediate-danger flag and reject explicit Level 2/3 contradictions. Do not invent measurements, classifications or resolved locations to enable approval.

Approval still records the human reviewer, reason, time and input/review revisions. It may proceed without AI output or while AI is working; a later AI result cannot overwrite a human review. Revision conflicts require refreshing. Corrections and changed caller input invalidate current approval while retaining history.

Caller tracking advances only to Reviewing request after current human approval and uses the actual approval timestamp. AI review alone does not advance it. Team assignment, response progress, case creation and confirmed receipt remain separate events. No team acceptance or arrival is implied.

Rationale: incomplete optional data should not block review of a contactable, located request. Keeping the former completeness gate would conflict with the explicit user instruction. Consequence: approved requests may still need follow-up information, shown in the desk results and missing-information list.

Affected documents: [requirements](../product/requirements.md), [API contract](../../contract/api.md), [web guide](../../web/README.md). Tests use isolated synthetic records and verify null fields, missing required inputs, in-flight AI precedence, persistence and truthful caller progress.
