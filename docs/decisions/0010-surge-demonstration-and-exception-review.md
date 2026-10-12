# 0010 — Surge demonstration and human exception review

Date: 2026-10-12. Status: Accepted user clarification.

## Approval and context

In the ReachPoint working conversation the user requested generating 1,000+ requests to create a useful map and demonstrate management during a flood, clarified that future scale needs a plan rather than proven throughput, and stated that humans cannot review everything. The user then instructed: “add that and is our system able to do that now or not?” This confirms the demonstration and operating-model requirements, not completion of implementation.

## Decision

Use a replayable synthetic scenario with text and simulated phone-call transcripts, plus browser voice under R2. Clear routine requests are organized and filed as AI-read automatically, with visible ranking reasons and deterministic safeguards. Human attention goes to exceptions and commitments. Assistance and water observations are separate outputs with distinct evidence/review states. Keep AI-read and verified counts separate. Preserve history, privacy, medical boundaries and truthful timing.

## Alternatives and consequences

Reject mandatory individual approval of every routine request: it contradicts the accepted D21–D22 surge model. Defer production-scale infrastructure and throughput proof. A controlled replay can demonstrate workflow but cannot substantiate real-world response effectiveness, AI accuracy or production capacity. No new provider, paid service or infrastructure provisioning is approved by this record.

## Affected documents

- [Requirements](../product/requirements.md)
- [Build-week tasks](../planning/build-week-tasks.md)
- [Surge demonstration plan](../planning/surge-demo.md)

Implementation details and evaluation thresholds remain proposed until implemented and validated.

## Later user clarification — 12 Oct 2026

The user requested using the flood map for rescue planning, estimating water levels from multiple intake reports, and then instructed “Now plan all for me.” These requested capabilities are accepted. The consolidated [implementation plan](../planning/surge-demo.md) records dependencies, proposed records, uncertainty treatment, demonstration acceptance and cuts. Numerical algorithms, thresholds, interpolation and UI details remain proposed and require validation. This documentation update does not claim implementation or authorize new services/spend.
