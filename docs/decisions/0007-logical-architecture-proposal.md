# 0007 — Logical architecture proposal

Date: 2026-10-11 (Asia/Bangkok).
Status: **Proposed architecture; no implementation or technology selection approved.**

## Request and context

The human requested an architecture diagram showing how the two workstreams and shared system connect. Accepted product scope is [0005](0005-prototype-scope-proposal.md); assigned human work split is [0006](0006-two-person-work-split.md). The [interface contract](../collaboration/volunteer-backend-contract-v1.md) remains proposed.

## Recommendation and rationale

Use one logical shared read/action boundary with permission/retry/version checks, distinct pending evidence/reviewed changes, deterministic planning/state rules, shared records/history and permitted derived views. The user supplies flood/exposure context and volunteer actions; the friend leads intake, coordination, resident status and persistence integration. AI proposes source-linked changes rather than directly updating authoritative quantities/assignments.

The [architecture overview](../planning/architecture-overview.md) diagrams this recommendation and the emergency/status feedback sequence. The boxes are logical responsibilities, not deployment units or selected products.

## Alternatives and consequences

Independent state stores on each UI would require reconciling competing mission/status truth. Separate services for every box would create additional integration boundaries; that complexity is not necessary to specify the bounded prototype. Physical service/store choices remain open rather than accepted by this diagram.

Actual components, phone/source access, permission policy, costs/regions, refresh approach and operational governance need technical review. Human authorization is required before implementation/provisioning/account changes. Diagram creation does not demonstrate a running API, data analysis, inbound call or clinical/rescue service.

Affected documents: architecture overview, decision index, project entry point, delivery agreement and integration contract.
