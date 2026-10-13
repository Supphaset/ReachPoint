# PART 1 — INDEPENDENT VERDICT

**63.5/100. A thoughtful prototype with stronger operational logic than its AI demonstration. Today, I would not put it in the finalist group.**

The strongest idea is **keeping rescue work connected when information changes—and noticing areas where nobody has called**. The weakest pitch is “Gemini reads flood requests and puts them on a map.” That already has close competitors.

These scores were locked **before** reading the other report.

| Criterion | Score | Weighted points | Evidence and judgment |
|---|---:|---:|---|
| Technical Merit & Gen AI Implementation — 40% | **6.0** | **24.0** | Real schema-based Gemini extraction, ADK tools, CP-SAT planning, rollback and retry protection. But the current server uses memory, has no enforced roles, and the agent’s ranking is deterministic. Live cloud operation and model quality remain unverified. |
| Problem Alignment & Impact — 25% | **6.5** | **16.25** | Concrete flood-response problems, distinct users, sensible attention to missed households and stale commitments. No operational partner, responder validation, or demonstrated adoption path. |
| Innovation & Creativity — 25% | **6.5** | **16.25** | Quiet-zone checks, whole-family allocation and withdrawing stale arrival estimates form an interesting combination. AI extraction, review, maps and duplicate suggestions are insufficient differentiation by themselves. |
| User Experience & Solution Design — 10% | **7.0** | **7.0** | Coherent role screens, bilingual controls, phone layouts, quoted evidence and truthful family status. Text-only intake weakens the elderly-accessibility premise; live usability was not verified here. |
| **Total** | | **63.5/100** | |

## What earns the points

**Technical substance exists.**

- Gemini receives a structured response schema and proposes facts with source quotations: `api/intake/extract.py:181–190`.
- ADK has four bounded read/propose tools; proposed links must reference eligible candidates: `api/ai/triage.py:29`, `:112–125`, `:176–191`.
- The solver uses genuine OR-Tools CP-SAT with successive objectives and explicit unmet-demand reasons: `api/rules/allocation.py:6–19`, `:32`.
- Writes run under a lock, roll back on failure, and remember successful submission IDs: `api/server/memory.py:106–118`.
- The core workflow has executable coverage: request → review → listing → claim → window → family status: `api/tests/test_core_loop.py:25–59`.
- The non-caller discovery scene is implemented and tested, including keeping partial coverage partial: `api/tests/test_b4_scene.py:22–57`.

**The operational design deserves more credit than the current AI pitch.**

The resource-failure workflow withdraws obsolete windows and relists unfinished work. That is a consequential behavior, not dashboard decoration. The implementation and checks live in `api/rules/failure.py` and `api/tests/test_s1_failure.py`.

The project distinguishes exposure estimates, reported needs, reviewed records and commitments. It also documents satellite blind spots and incomplete validation rather than calling blank areas safe: `data/SOURCES.md:82–98`.

**But several headline claims outrun implementation.**

- `/call` is a text form, not a voice conversation: `web/src/features/intake/CallPage.tsx:14–17`, `:90–98`.
- The health route explicitly returns `store: "memory"`: `api/main.py:75–77`.
- Queue ordering is danger-sign-first, then oldest-first. Agent reasons do not determine rank: `api/ai/triage.py:141–144`.
- The 1,200-request replay uses deterministic parsing and an isolated store: `api/rules/replay.py:1–6`, `api/server/flood_replay.py:1–8`.
- The brief acknowledges no interviews or confirmed clinical partner, and unresolved adoption: `docs/product/brief.md:5–19`.
- README claims “answers every caller in seconds,” but still says no backend exists: `README.md:5`, `:36`. Neither is an accurate description of this checkout.

Innovation also faces a substantial baseline: [thaifloodhelp’s own repository](https://github.com/winn/thaifloodhelp) describes Thai Gemini extraction, human review, duplicate detection and a mobile interface. ReachPoint needs to demonstrate its **response and reassessment advantage**, not claim ownership of AI intake.

## Validation and submission readiness

| Check | What I actually established |
|---|---|
| Backend tests | Using `--capture=sys` to avoid pytest’s temporary capture files: **204 passed, 1 failed, 7 warnings, 40.08 seconds**. The failure was notebook execution requiring a writable temporary directory. |
| Frontend tests | `npx vitest run` was blocked before tests by an `EPERM` error creating Vite’s temporary config file. |
| Local HTTP server | Uvicorn initialized successfully with AI off, but the sandbox prohibited binding port 8097. It shut down. No curl or browser walkthrough was possible. |
| Additional probes | Direct validator calls and in-process FastAPI `TestClient`, with AI off. Findings below. |
| Live prototype | No deployed URL established. Deployment checklist remains open: `docs/planning/build-week-tasks.md:35–40`. |
| Public GitHub | README identifies the public repository; my public fetch failed. Visibility was not independently confirmed. |
| Video / PDF deck | No submission-ready artifacts found in this checkout. They may exist elsewhere. |
| English | English documentation and code are present; final submission materials remain unverified. |

The organiser requires a functional Google AI prototype deployed through Cloud Run or Firebase, with English submission materials and a PDF deck. These are submission gates, not optional score improvements. [Official requirements](https://aibuildercup.com/themes.html)

**This is a provisional prototype score, not a declaration that the submission is eligible.** No files were edited, no paid APIs called, and no private environment file read.

# PART 2 — SECOND OPINION

The other judge scored **64.75/100**. Our only scoring difference is Impact: **their 7.0 versus my 6.5**. I give less credit to potential impact without evidence that an actual coordinator would adopt the workflow.

## Where I agree

- **Deployability comes first.** The reported container defects are supported by this checkout:
  - `api/rules/allocation.py:32` imports OR-Tools; it appears in development requirements, not `api/requirements.txt`.
  - `api/server/flood_replay.py:8` imports `data.surge`; `Dockerfile:20` copies only three data JSON files into the runtime image.
  - Location resolution loads GeoJSON from the data package: `api/location/geo.py:39–41`; those files are absent from that runtime copy.
  - I verified these dependencies statically; I did not reproduce the other judge’s container simulation.
- **The implemented AI route is not Vertex AI.** Extraction uses the Gemini API endpoint and an API key; ADK defaults Vertex mode to false: `api/intake/extract.py:26`, `api/ai/triage.py:168–169`. The deployment script supplies no Gemini secret: `scripts/deploy.sh:21–23`.
- **Voice, Firestore and production authentication are not demonstrated.**
- **The best video material is quiet-zone discovery and the boat-failure cascade.**
- **A real evaluation would earn more than another feature.**

Their **345 passing tests** cover a broader run than mine. I cannot independently endorse that count, but my sandbox-limited result does not contradict it.

## Where I disagree

**1. “The model cannot add a fact the caller didn’t say” is false.**

The validator checks quotation presence and value bounds, not whether the quote supports the value.

My direct probe supplied:

- Text: “There are **2 adults**. **Nobody is unconscious**.”
- Proposed adults: **50**, citing “There are 2 adults.”
- Proposed danger: **unconscious**, citing “Nobody is unconscious.”

**Both survived, with zero dropped fields.** Relevant code: `api/intake/extract.py:109–115`, `:135–137`.

The existing test even accepts a supplies need supported by a quote meaning “chest deep”: `api/tests/test_extract.py:11–16`.

That is provenance checking, not semantic verification.

**2. The safety floor does not hold “whatever the model says.”**

It holds **given the extracted danger signs**. A missed danger can lose priority and link protection; a false danger can gain both. `_danger()` reads the extraction output: `api/ai/triage.py:69–70`.

The keyword fallback also marked “Nobody is unconscious” as unconscious in my probe. Prompt-injection resistance and clinical-language interpretation need separate evaluation.

**3. The briefing validator cannot guarantee correct numbers.**

I supplied facts containing **0 evacuation requests** and **2 unchecked segments**. It accepted “There are **2 reviewed evacuation requests**.”

The validator checks numbers against one shared set, not against their meanings: `api/ai/briefing_text.py:98–103`.

**4. The duplicate-action UI is already built.**

The other report recommends adding visible Link / Not same cards. They already exist, with quotes and new-hazard handling: `web/src/features/desk/ReviewQueue.tsx:156–177`.

Use and improve them; do not spend time rebuilding them.

**5. “Hotlines and LINE groups can’t do this” is too broad.**

People using those channels can organize area checks. ReachPoint’s defensible advantage is making coverage gaps, evidence, ownership and changing commitments **visible in one workflow**. Competitor absence claims need evidence.

## What the report missed or understated

- **Cloud Run background execution risk.** Triage starts in a thread after intake returns; briefings also run in background executors: `api/main.py:84–85`, `:328`. Under default request-based billing, CPU allocation outside requests is restricted. A local background task succeeding does not prove deployed behavior. [Google’s billing documentation](https://docs.cloud.google.com/run/docs/configuring/billing-settings)
- **Minimum instances are not persistence.** Keeping one instance warm does not prevent restarts or state loss. [Google documents restart and minimum-instance limitations](https://cloud.google.com/run/docs/configuring/min-instances).
- **Authorization is missing on writes, not just reset.** My unauthenticated requests to the review queue **and report approval** returned HTTP 200. Protecting reset alone leaves actors able to approve and alter work.
- **The surge demo does not prove Gemini throughput or coordinator workload reduction.** Its parser and store are explicitly separate from operations.
- **Neighbor-count protections are incomplete.** The queue warns against summing neighbor reports, but approval creates ordinary counted cases without branching on report kind: `api/views/review.py:55–56`, `api/server/memory.py:268–310`.
- **The maps contain a credibility trap.** The city model is an unvalidated bathtub model; team guidance includes “Wading may be possible”: `data/SOURCES.md:131`, `api/views/team.py:78–84`. These distract from the strongest, safer product claim.

# PART 3 — HOW TO WIN

**Stop expanding the product. Build a short, measured proof that ReachPoint handles changing, ambiguous information better than a static request list.**

Deployment buys eligibility. Evaluation buys technical credibility. One memorable reassessment story buys differentiation.

## The five highest-value moves

Effort estimates are **person-hours**, excluding account/billing blockers. Score gains are directional estimates, overlap, and must not be added mechanically.

| Move | Concrete result by Saturday | Effort | Criteria / expected gain |
|---|---|---:|---|
| **1. Make the real cloud path dependable** | Fix runtime dependencies/data copies; deploy with real Gemini; verify intake, agent completion, claim, status and failure cascade on the deployed URL. Resolve background CPU behavior. Protect privileged writes/reset and prevent judges disrupting one another’s demo. | **6–10 h** | Technical: roughly **+1–1.5** criterion points; removes submission failure risk. |
| **2. Prove AI handles meaning, uncertainty and corrections** | A labelled bilingual evaluation, baseline comparison, repeated runs and one visible ambiguous/corrected-request demonstration. Fix failures the evaluation exposes. | **10–14 h** | Technical **+1–1.5**; Innovation **+0.5–1**. |
| **3. Stage the non-caller discovery as the emotional payoff** | A real deployed B-4 flow: zero calls → unchecked area → team checks → field report → reviewed rescue case. Estimates remain separate from confirmed need. | **3–4 h** | Innovation **+0.5–1**; Impact **+0.5**. |
| **4. Get one useful operator reaction** | Show the workflow to one actual rescue coordinator or foundation volunteer. Record the task, friction, requested change and whether they would try a bounded drill. Get permission before quoting. | **3–4 h**, plus response time | Impact **+0.5–1** if substantive; potentially better differentiation. |
| **5. Package the strongest proof** | Honest README, focused demo entry, English video under 3 minutes, PDF deck, Thai fallback/count-entry fixes, final phone rehearsal. | **7–10 h** | UX **+0.5–1**; improves how every other criterion is perceived. |

That is approximately **29–42 person-hours**. Two humans can do it, with clear ownership and room for deployment surprises.

Aim for the upper 70s or low 80s through demonstrated evidence. A first-place outcome still depends on the field; cosmetic additions will not manufacture a 9.

## The remembered moment

**“The map is quiet. The family isn’t safe.”**

Show B-4 with zero requests and an explicit assessment gap. The coordinator publishes a check; a team discovers an elderly couple who never called; their reviewed need becomes actionable. Keep “partly checked” visible afterward.

Then use the boat failure as a short second proof: the family’s obsolete arrival estimate disappears and a named next-update responsibility replaces it.

The pitch line:

> **ReachPoint turns flood reports—and gaps in reporting—into accountable rescue work, with status families can trust.**

This is stronger than “an AI-powered flood dashboard.” It explains who benefits and what changes.

## Gen AI depth: the safest high-return build

**Demonstrate bilingual interpretation across corrections and ambiguity, with human-approved consequences.**

Use three related synthetic messages:

1. A Thai request describes a household, water and mobility limitations.
2. A follow-up corrects the count or reports that some people already left.
3. Another report from the same landmark describes a different household—or a new danger.

Show Gemini extracting supported facts, retaining unknowns and identifying the correction. Show ADK retrieving candidate records and proposing an appropriate link or clarification. The human decides.

This needs language understanding. A keyword parser cannot reliably handle negation, corrections, relationships and overlapping reports.

### Work in these files

- **`api/intake/extract.py`**: tighten semantic grounding; explicitly handle negation, corrections and missing values. Where support is uncertain, abstain and request review. Do not claim substring validation proves truth.
- **`api/ai/triage.py`**: improve link reasoning and add a bounded proposed clarification, such as “Is this your household or another family at the school?” Same landmark must not imply same household.
- **`web/src/features/desk/ReviewQueue.tsx`**: display the clarification, evidence and model/fallback source beside the existing Link / Not same controls.
- **`api/scripts/triage_eval.py`**: expand beyond the six happy-path cases.
- **Proposed `api/scripts/extract_eval.py` and `contract/evals/`**: store labelled synthetic examples and reproducible evaluation logic.

Expose **actual ADK function-call events** from the runner. Currently the loop discards events: `api/ai/triage.py:184–185`. The internal `calls` list also includes nested tool invocations and rule fallback; it is not sufficient proof of model-directed tool use.

### The evaluation that would impress me

Use **40–60 labelled synthetic Thai/English examples**, with at least three runs and a keyword-baseline comparison. Keep challenge cases separate from prompt-development examples.

Include:

- Count corrections and overlapping categories.
- Negated and historical danger statements.
- Two different households at one landmark.
- Genuine duplicates expressed differently.
- New hazards attached to an existing case.
- Missing location, unknown counts and instructions embedded in reports.

Report:

- Semantic field precision/recall.
- Danger-sign false negatives and false positives.
- Duplicate-link precision and missed duplicates.
- Correct unknown/abstention behavior.
- Quote retention, fallback rate and p50/p95 latency.
- Model identifier, sample counts and variation across runs.

**Use measured numbers, including failures.** Do not relabel “8/8 checks” as “100% accuracy.” Do not count rules fallback as a successful Gemini run.

Also measure coordinator review time on a small synthetic task, with and without AI assistance. Two developers doing a drill is not responder validation, but it is an honest initial workload experiment.

**Skip Gemini Live and flood-photo interpretation this week.** Neither compensates for unmeasured semantic errors. A photo also invites unsupported depth/location claims. Voice is worth adding only if it already works reliably on another branch and can be integrated without destabilizing the core.

## What to cut or hide

- **Remove unsupported capability claims:** voice agent, Vertex AI, Firestore transactions, autonomous ranking, city-wide response capacity.
- **Keep the 1,200 replay out of the main AI proof.** If shown, label it deterministic synthetic replay. It demonstrates workflow mechanics, not model scale.
- **Hide modeled street-depth guidance and wading suggestions from the main demo.** Keep dated extent, blind spots and sourced observations.
- **Cut Bangkok, extra scenarios and the routine planner from the video.**
- **Do not lead with medical triage.** Show reported mobility needs and human decisions.
- **Do not present seat-unit assumptions as validated rescue loading guidance.**
- **Remove development controls from the judge’s main path.** Protect reset at the server, not merely by hiding its button.
- **Stop saying “every caller in seconds.”** Report observed latency and fallback behavior.
- **Keep uncertainty labels.** They are part of the value proposition, not clutter.

For architecture, show **what actually runs**. Cloud Run serving both frontend and API satisfies the hosting requirement; extra Firebase boxes do not earn points. Any change from the accepted technical direction needs the team’s explicit decision.

For adoption, propose one bounded operator-owned drill: existing-channel reports entered into the desk, one coordinator, two teams, synthetic households. Identify ownership, training, connectivity limitations and estimated operating costs. Do not name an organization as a partner without agreement.

## Suggested video: 2:50

| Time | Content |
|---|---|
| **0:00–0:15** | “A quiet map can hide a family who needs help.” Hat Yai replay context; clearly label real historical flood data and synthetic operations. |
| **0:15–0:45** | Thai message → Gemini facts with highlighted quotations. Show one unknown or correction handled correctly. English narration/subtitles. |
| **0:45–1:10** | Visible ADK candidate lookup and link/clarification proposal. Coordinator confirms; team takes the whole family; family sees an estimate. |
| **1:10–1:30** | Boat fails. Withdrawn estimate appears across roles; unfinished work reopens; next update has an owner. |
| **1:30–2:05** | B-4 has no calls but remains unchecked. Team checks, reports a previously unseen household, coordinator reviews, rescue work appears. |
| **2:05–2:25** | Measured AI results versus keyword baseline. Show deployment architecture and a visible fallback state. |
| **2:25–2:45** | Operator feedback if obtained; bounded adoption plan; honest operational limits. |
| **2:45–2:50** | Pitch line, live URL and public repository. |

Show the deployed application, not only `/demo` frames or architecture graphics. Leave ten seconds of margin below the strict three-minute limit.

## Suggested 10-slide PDF deck

1. **Promise:** the pitch line and one memorable product image.
2. **Problem:** sourced Hat Yai coordination evidence; distinguish requests from unique people.
3. **Users and adoption:** coordinator operator, team leaders, families; first bounded pilot.
4. **Core workflow:** report → evidence → review → claim → truthful status.
5. **Differentiation:** baseline workflows and published competitors; mark unknown capabilities honestly.
6. **Gen AI implementation:** extraction, ADK tool calls, corrections, clarification and human authority.
7. **Evaluation:** sample counts, semantic metrics, baseline, latency, failures and limitations.
8. **Actual Google Cloud architecture:** deployed components, credentials, background execution and state limits.
9. **Impact and business case:** proposed workload/coverage measures, operator ownership, costs and funding hypothesis.
10. **Live proof and next milestone:** demo/repo/video links, remaining constraints and responder-led validation.

**My deciding question:** after Gemini reads a messy request, can you show a demonstrably better decision process—and prevent a confident mistake from becoming somebody’s rescue status? Build the submission around that proof.