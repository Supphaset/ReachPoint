# 0006 — Two-person work split

Date: 2026-10-11 (Asia/Bangkok).
Status: **Accepted human work assignment; detailed handoff recommendations proposed. Implementation remains unapproved.**

## Human instruction

The user assigned their friend the resident/coordinator side, including chat/voice intake, reconciling inputs and updating the database. The user assigned themselves the main volunteer workspace and flood map, and requested a document describing mutual expectations and suggested scope changes.

## Accepted assignment and rationale

Divide ownership along connected product workflows: the user owns volunteer planning/map work; the friend owns resident intake and coordination work. This is an explicit assignment, not a framework, provider or implementation authorization. Keep the accepted [prototype v1 boundaries](../product/prototype-scope-v1.md).

The [two-person delivery agreement](../collaboration/two-person-delivery-agreement.md) records these assignments and recommends concrete deliverables, a two-way data contract, shared records and integration checks. Its additions—user ownership of team mission/update surfaces and planning rules; friend ownership of resident status, routine-plan review and shared state enforcement—are proposed responsibilities for both humans to review. They support the existing product scope rather than add new capabilities.

## Alternatives and consequences

A one-way chatbot-to-database handoff would omit team acceptance/progress and resident timing feedback. Independent mission/state stores would risk conflicting versions and promises. The recommended contract retains a single logical record/state boundary while leaving physical architecture open.

Exact schema/API, technologies, shared persistence ownership details, phone/source feasibility, permission policy, effort, deployment/budget and real operational governance remain unresolved. No code, service, integration, account, paid feature or deployment is authorized by this assignment. No message was sent to the friend.

Affected documents: the delivery agreement, [draft volunteer/backend integration contract](../collaboration/volunteer-backend-contract-v1.md), [working agreement](../collaboration/working-agreement.md), [decision index](README.md) and [project entry point](../../README.md). The later request for more detail authorizes expanding the documentation; it does not accept the proposed interface names or authorize implementation.
