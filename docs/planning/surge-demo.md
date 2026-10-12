# Intake, flood map and rescue-planning demonstration

Updated 12 Oct 2026. Accepted demonstration scope: [decision 0010](../decisions/0010-surge-demonstration-and-exception-review.md). The user additionally requested map-based rescue planning and estimating water levels from multiple intake reports. Algorithms, thresholds, contracts and schedule below are **proposed implementation details**, not validated capabilities. Deadline: Sat 17 Oct, 21:00 Bangkok, as supplied by the user. Feature freeze: Fri 16, 18:00.

## Outcome

Demonstrate 1,200 synthetic requests becoming an evolving flood-observation map, actionable assistance lists, human exceptions, team commitments and truthful resident status. Text and simulated phone-call transcripts use the same pipeline; include a real browser voice interaction when integrated. Browser voice represents a phone call, not an actual telephone number. Humans do not approve every clear routine request. AI organizes evidence; deterministic rules enforce state and quantities; humans approve response commitments and qualified personnel govern medical assessment.

Production throughput proof, a real phone line, new paid services and autonomous routing are outside this demonstration. Keep the existing FastAPI, React/Vite/TS, deterministic rules and tokens. Begin with the existing MemoryStore behind a storage interface; clearly disclose restart resets. Firestore/Auth remain planned platform work and must not silently become a dependency for the local replay. Public deployment requires appropriate access controls or a clearly isolated synthetic sandbox.

## Existing versus missing

| Capability | Current evidence | Remaining work |
|---|---|---|
| Intake | Text extraction, status token, background triage | Save before extraction, common voice adapter, processing state |
| Automatic organization | Ranking/link suggestions | Explicit AI-read routine filing and exception workflow |
| Map | Historical extent, geography, blind spots, reviewed caller markers | AI-read observations, conflicts, evidence drawer, three modes |
| Water estimation | Precomputed package depths; newest reviewed band per segment | Comparable multi-report estimates with evidence and uncertainty |
| Rescue operations | Solver, team claims/progress/outcomes, resident status, S1 failure | Live solver inputs, real direct asks, map planning integration |
| Demonstration | Small fixtures and scene tests | 1,200-report dataset, replay controls and measured outcomes |
| Durability/access | In-memory records, demo roles | Firestore/Auth/rules and deployment verification, separate platform stream |

## End-to-end flow

Receive → store original report and submission ID → acknowledge with status reference → extract quote-backed facts → match location → safety screening and visible rank → automatic routine filing or exception → assistance and water-observation views → planning suggestion → coordinator ask/team acceptance → progress/outcome → resident update.

Processing states are received / processing / processed / failed; evidence states are AI-read / verified / disputed / superseded. These are separate from assistance progress and commitments. AI failure leaves a saved report available to the desk, not a fabricated result. New danger is visible immediately through deterministic screening of the received text, with its limitations labelled. Ranking is operational attention, not clinical triage.

## Proposed records and shared contracts (work item W1)

- `Report`: ID, submission ID, channel, original text/transcript, received time, replay metadata, extraction state/version, supporting quotes. Optional observation time must never default silently to received time. Audio consent/retention are explicit; do not retain audio by default for the synthetic demonstration.
- `AssistanceRequest`: report links, anonymous place/household references when established, party/groups, assistance type, location precision, review state, priority reasons, override and revision. Check-on and neighbour observation must not invent confirmed assistance or household counts.
- `WaterObservation`: report link, observed time or unknown, received time, location/source/precision, indoors/outdoors/unknown, ground/floor/unknown reference, qualitative band or measured depth with units, reported trend, firsthand/hearsay/unknown, evidence state and correction history.
- `WaterEstimate`: supported location/geometry, time window, band or numeric interval, estimator version, evidence IDs, dependence groups, conflicting evidence, freshness, uncertainty reasons and status: available / qualitative-only / insufficient-evidence / conflicting / stale.
- `Replay`: scenario version, deterministic seed, cursor, virtual clock, state and counters. Evaluation truth is stored separately and must never be read by processing or AI.
- `PlanSuggestion`: input revisions, existing commitments, proposed pickup groups, suitable resources, remaining unmet needs and explanation. Team asks are recorded events; accepting an ask uses existing claim rules.

Update contract/api.md and shared TS types together. Proposed operations: intake/status; map views; exception corrections; replay start/pause/step/reset; live split and asks. Reuse existing routes where possible. No exact household coordinates or transcripts in shared map responses. Existing integration-map contracts must be reconciled: older review-gate wording cannot require approval of every clear AI-read record.

## Automatic filing and exception policy (W2)

Auto-file clear non-emergency assistance only when required facts have supported quotes, an acceptable location match, consistent quantities and no unresolved identity conflict. Do not use an uncalibrated model confidence score as the sole gate. Missing information remains unknown; incomplete assistance can still contribute a valid independent water observation.

Urgent reports remain immediately visible while unverified, including those needing clarification. Medical facts enter qualified attention without autonomous assessment. Human attention handles ambiguous locations, conflicting counts, uncertain household identity, material corrections, disputed evidence and assignment decisions. Teams may take eligible AI-flagged urgent work under the existing accepted surge policy and deterministic capability/claim rules; do not add an approval bottleneck solely because evidence is unverified.

Group possible duplicates for review, retaining all messages. Automatic submission retries have exactly-once effects; possible household duplicates do not automatically merge identities. Shared phones and common buildings do not prove a shared household. A new hazard gets its own visible attention even when linked to an existing case. Overrides persist through subsequent processing.

## Multi-report water estimation (W3)

First release estimates at supported local observation clusters, not a continuous citywide depth surface.

1. Partition by compatible location, observation-time window and measurement reference. Unknown time, floor or reference limits eligibility for numeric estimation, but not visibility as evidence.
2. Link repeated evidence and count dependence groups. Where independent observers cannot be established, report independence as unknown. Never claim independence from different phone numbers alone.
3. Keep body-level terms as ordinal evidence or documented broad intervals; do not silently map waist/chest to exact metres. Numeric measured reports require known units/reference. A photo is optional corroboration, not a measurement without a supported reference.
4. For comparable numeric observations, evaluate a robust estimator such as weighted median; preserve intervals and uncertainty floors for instrument/reference, location, time and terrain. Weighting and cutoffs are versioned, evaluated rules, not accepted facts. Avoid shrinking uncertainty merely because many correlated messages agree.
5. If evidence cannot support a combined interval, expose disagreement or separate local groups. Keep a high-depth report visible to operational safety screening even when an aggregate is lower. No single outlier silently changes the whole segment.
6. Derive a reported trend only from explicit statements or comparable dated observations. Unknown observation time does not support a temporal trend. Stale observations stay available in history, not presented as current estimates.

Later experiment: water-surface elevation = ground elevation + ground-relative depth, with a common vertical datum. Interpolate only where suitable ground-terrain data, connected water and compatible times support it; account for barriers and separate pools. Surface/building-height models are not automatically ground models. Return unknown outside support. Gauge elevation must not be substituted for street depth. A validated continuous surface is deferred; satellite extent and estimated depth retain distinct layers/dates.

Validate against withheld synthetic observations and known synthetic conditions, including rising water, different ground elevations, duplicated reporters and barrier-separated pools. Report interval coverage, error on eligible numeric cases and abstentions. Synthetic correctness cannot establish accuracy in Hat Yai. Field validation is required before real response use.

## Map interface (W4)

| Mode | Visual encoding | Actions |
|---|---|---|
| Water | Existing-token blue depths/bands; shapes/patterns for evidence state; age labels; conflict markers | Inspect quotes/time/reference; request clarification/check |
| Needs | Urgency colours; separate AI-read/verified quantities; assistance filters; unmet groups | Review exceptions; inspect family groups; plan area |
| Response | Accepted jobs, team capability/status freshness, segment checks, held work | Compare resources; ask teams; inspect progress |

City zoom shows zone summaries; closer zoom shows segment clusters and observations. Aggregate by known geography initially, without adding a mapping package. Urgent cases must remain discoverable inside clusters. List/map selection uses identical IDs. Add a time slider, start/pause/step controls and a 'What changed?' list. Historic satellite dates remain visible; retrospective peak extent must not masquerade as contemporary evidence.

Evidence drawer shows observations, original quotes permitted by role, time, AI-read/verified status, dependence/duplicates and contradictions. No reports means unknown. Quiet/populated or satellite-blind areas become candidates for checking, not proven flooded or dry. Depth colour and urgency colour are separate. Use brief arrival highlights, respect reduced motion, and keep keyboard-accessible lists and readable legends. No constant flashing, forced map pans or inaccessible colour-only states.

## Rescue planning (W5)

Select area → inspect unmet needs and evidence → compare suitable teams/resources → review suggested pickup groups → send recorded asks → team accepts and sets window → track progress/outcomes.

The solver reads current listings, revisions, resources, family groups and commitments, not fixture totals. Preserve family integrity, seat units, capabilities and reserved capacity. Urgency stays visible when no resource can serve it. Explain infeasibility and unmet needs. Distance from map points is approximate proximity, not travel time or route safety. Water observations inform suggested equipment, reconfirmation and field checks; no inferred boat navigability or autonomous safe route.

Suggestions expire when relevant inputs change. Acceptance must recheck revisions/capacity atomically. A stale suggestion returns the current facts for review. S1 failure withdraws estimates, relists unfinished groups and invalidates affected plans while unrelated drafts, areas and medical missions stay intact. Corrected observations never independently cancel commitments. Team observations and capability freshness are shown separately from plan recommendations.

## Scenario and replay (W6)

Proposed dataset: **1,200 submissions** in mutually exclusive scenario categories: 600 routine requests, 150 urgent reports, 150 additional updates/possible duplicate reports, 120 water-only observations, 120 ambiguous/conflicting reports, 60 malformed/injection/processing-failure cases. These are scenario labels, not expected outcome counts. Use simulated calls and texts across categories and all relevant segments; retain Thai/English variants. No real names, telephone numbers, household data or recordings.

Distribute synthetic flood conditions over time and terrain, including blind spots, quiet areas, conflicting reports and separate pools. Keep generation truth in evaluation-only records; the processor sees only intake content/channel and user-supplied location evidence. Distinguish hidden synthetic identity from identity actually established by the application.

Replay enters the common intake pipeline. Provide a deterministic offline extraction adapter labelled simulation, plus a representative separately evaluated Gemini sample when authorized. Never present prerecorded/precomputed extraction as live AI. One browser voice interaction demonstrates the actual channel, separately from replayed transcripts.

Judge sequence: reports arrive → auto-organized map and exception counters → investigate a quiet area → team finds a previously unreported household (B-4) → compare a pickup plan → team accepts → S1 fails → map shows held work/unmet need and withdrawn times → compare replacement plan → show partial/completed outcomes.

## Delivery order and suggested ownership

Existing two-person responsibilities remain; no delegation or remote tasks are created by this plan.

| Work | Owner / reviewer | Depends on | Completion evidence |
|---|---|---|---|
| W1 Contracts, states, sample records | Both | — | Shared shapes and 12 representative fixtures agreed; legacy review-gate wording reconciled |
| W2 Intake, automatic filing, exceptions | Friend / You | W1 | Routine case needs no individual approval; emergency/unknown/override tests |
| W3 Observation aggregation and estimator | You / Friend | W1 | Independent evidence, time/reference/conflict tests; estimate metrics |
| W4 Three map modes, drawer, counters | You / Friend | W2, W3 | Live derived views; role privacy; no misleading depth/urgency encoding |
| W5 Live split/asks and map planning | You solver/UI; Friend writes / Both | W2 | Actual team prompt, stale-plan rejection, atomic claim and S1 scene |
| W6 Generator and replay controls | You generator/UI; Friend replay API / Both | W1 then W2–W5 integration | 1,200 preserved submissions, disclosed processing mode, full walkthrough |
| W7 Browser voice adapter | Friend / You | W1, W2 | Thai call → transcript → same pipeline; interruption/failure fallback |
| W8 Demo access, deploy, polish, submission | Friend deploy; Both acceptance | W4–W7 | Deployed rehearsal, phone/keyboard checks, video/deck/live URL |

Suggested calendar: Mon 12 contracts/samples; Tue 13 filing/observations/generator; Wed 14 map/estimator/live split; Thu 15 replay integration and voice; Fri 16 acceptance/polish, freeze 18:00; Sat 17 submission buffer, finish before 21:00 Bangkok. This is a dependency plan, not a promise of effort or readiness.

## Verification and honest demo metrics

- Run API, data and web tests, TypeScript and token checks for implementation changes. Add meaningful scene tests for every state transition and negative control.
- Repeated submission IDs never double-count. Replay pause/resume and retry reproduce the same state; reset removes only scenario data or uses an isolated replay store, never unrelated work.
- Received = pending processing + processed + failed at a consistent snapshot; separately count auto-filed records, exceptions, verified records, possible duplicates, water observations, eligible estimates, unmet groups and accepted/completed assistance. Categories overlap only where explicitly defined. Do not publish invented automation percentages.
- Inject late danger, AI failures, partial transcripts, duplicate locations, conflicting water, stale observations and changed resource capacity. Evidence-based abstention is an expected outcome.
- Estimates improve under genuinely independent compatible evidence, retain conflicts and uncertainty floors, and never reveal restricted coordinates. Dense reporting does not automatically outrank a quiet emergency.
- Full browser walkthrough: text/call → map → exceptions → plan → claim/window → progress → S1 failure → replacement; B-4 discovery; resident timing; unrelated-area/medical negative controls.
- State whether outputs are deterministic simulation, precomputed AI or live AI. Report measured evaluation results and limits. No claim of production throughput or field accuracy.

## Cut order if behind

Cut continuous depth modelling, inferred image measurements, decorative 3D, real phone service, production load testing and new queue infrastructure first. Keep automatic organization, exception workflow, map evidence/uncertainty, local estimate or explicit qualitative-only result, live team workflow and disclosed replay. If voice is incomplete, retain simulated call transcripts and clearly say browser voice is unfinished; do not call that successful call integration.

## Later production scale

Firestore durability and roles; durable queued processing with idempotent workers; bounded model calls/retries; incremental summaries and paginated views; per-role permissions; retention and observability; field calibration and operational governance. Queue/provider/budget changes require their own review. Load-test separately before capacity claims. No provisioning is performed by this plan.

## Research basis

Sources checked 12 Oct 2026 are recorded as FM1–FM6 in [sources](../research/sources.md). They support provenance, uncertainty, report-bias handling and cautious modelling, not validation of the proposed ReachPoint estimator.
