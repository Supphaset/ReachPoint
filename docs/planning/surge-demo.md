# Connected surge demonstration

Accepted scope, 12 Oct 2026: [decision 0010](../decisions/0010-surge-demonstration-and-exception-review.md). Implementation approach below is proposed; this document does not claim the features exist.

## Current capability, inspected 12 Oct 2026

- Text intake extracts proposed facts, returns a status token and schedules triage. Extraction currently happens before persistence.
- Triage proposes ranking and duplicate links; coordinator approval currently creates cases and listings. Automatic routine filing is not implemented.
- Records are in memory; restarts reset them. No production-scale durability or throughput demonstration exists.
- Historical flood geography and extent, blind spots and reviewed caller-water markers exist. New AI-read water observations are not yet a map layer.
- Caller-water aggregation chooses the latest band per segment and counts records, without explicit distinct-observer corroboration or conflict presentation.
- Team claim/progress/outcomes, resident status and S1 failure exist. Split-panel data and direct-ask results still use fixtures.
- The intake screen accepts text. Browser voice and the connected 1,000+ replay are not implemented. Simulated call transcripts do not prove voice integration.

## Proposed bounded build

1. Generate a deterministic 1,000+ report dataset using synthetic household/place identifiers in the existing Hat Yai segments. Include Thai/English texts, simulated call transcripts, transport/supplies/check-on requests, observations, duplicates, updates, ambiguous locations, contradictory water reports, injection attempts and new hazards. Store expected relationships separately as evaluation truth; processing must not read those answers.
2. Add start/pause/step/reset replay controls and a replay clock; label all operational reports synthetic and retain historical layer dates. Exercise the common intake pipeline rather than inserting pre-approved cases. Precomputed AI outputs, if used, must be disclosed; evaluate a representative live AI subset separately.
3. Add automatic filing for clear routine requests with explicit AI-read state, quote validation and deterministic safety checks. Rank urgent reports visibly even while unverified. Route uncertainty and potential identity merges to exceptions. Human overrides win; no autonomous clinical assessment, assignment, promise or closure.
4. Build separate water-observation records with observation time, submission time, source, original quote, location precision, review state and qualitative band or measured units/reference. Group distinct evidence, show conflicts and stale reports, retain corrections. No invented continuous depth, dry areas or safe routes.
5. Extend map/list summaries with AI-read versus verified need, reported flooding, urgent attention, unmet assistance, team coverage and information gaps. Shared maps stay at segment/landmark level. Add filters and drill-down so 1,000 markers are not the only interface.
6. Connect live split suggestions/direct asks, team acceptance, progress and resident status. Replay S1 failure and B-4 discovery using the existing deterministic rules.

## Acceptance evidence

- Exactly-once effects for repeated submission IDs; messages, distinct requests and verified households are separate counters.
- Clear routine reports can reach AI-read lists without individual desk approval; uncertain records go to an explained exception queue.
- Late-arriving danger stays visible; duplicate suggestions never erase new hazards; overrides survive subsequent AI processing.
- Map observations preserve provenance/time/review state; repeated reports are not independent corroboration; conflicts and unknowns remain visible.
- Demonstrate team commitments and outcomes, then S1 hold/relist/window withdrawal with negative controls intact.
- Report actual filing, exception and correction counts. Do not claim an automation percentage before measuring it.
- Include one actual browser voice interaction once available; label replayed phone transcripts as simulated.

## Future scale plan, not a prototype acceptance gate

Persist before AI processing; return acknowledgment promptly; process new/changed records with a durable queue, bounded concurrency and retries; use idempotent workers, pagination and incremental summaries. Choose infrastructure within a separately reviewed scope and budget. Test production throughput separately before claiming capacity. This replay demonstrates workflow only.
