# 0009 — Implementation start and technical direction

Date: 2026-10-11 (Asia/Bangkok).
Status: **Accepted by the user (repository owner); partner confirmation required before this PR merges.** Items marked *joint* bind both humans only once the friend confirms in the PR review.
Human approval reference: the user's answers in the 2026-10-11 technical-planning session, recorded item by item in the [joint decision pack](../planning/joint-decision-pack.md#human-answers-recorded-2026-10-11-one-partner-friends-confirmation-pending). AI recommendations that the user did not explicitly choose remain proposed.

## Context

The prototype deadline is 18 October 2026, with no published cut-off time or timezone ([hackathon](../hackathon.md)). Scope v1 is accepted ([0005](0005-prototype-scope-proposal.md)) and the split is assigned ([0006](0006-two-person-work-split.md)), but nothing could be built because AGENTS.md forbade implementation. The pack compares options and records the research behind each answer.

## Decisions

| # | Decision | Kind |
|---|---|---|
| D1 | **Implementation is authorized from 12 Oct 2026** under the pack's §6 checkpoint plan: CP0 deploy (12 Oct), CP1 text report → reviewed need on map (13 Oct), CP2 offer → accept → resident window (14 Oct), CP3 full emergency walk-through + phone gate (15 Oct), feature freeze (16 Oct), submit by 17 Oct evening Bangkok time | joint |
| D2 | **Stack A:** React + Vite (TypeScript) on Firebase Hosting; FastAPI (Python) on Cloud Run as the only writer of shared state; Firestore with server-only writes and role-filtered derived view documents read through listeners; Firebase Auth with seeded demo roles. Monorepo `web/`, `api/`, `contract/`, `data/`, `docs/` | joint |
| D3 | **Google Maps JavaScript API** (restricted key) and **Gemini through Vertex AI**, server-side only through the Cloud Run service account | joint |
| D4 | **Google Cloud layout:** one shared project `reachpoint-main`, owned by the friend with the user as Editor, holding everything the demo needs. A user sandbox project holds Earth Engine (noncommercial) and prompt experiments. Its outputs are committed files, so nothing is merged later. Budget alert on every project; no keys or service-account files in Git | joint (friend must accept ownership) |
| D5 | **Inbound phone (R2):** first try the user's existing AIS postpaid number via carrier call forwarding to a paid Twilio number bridged to Gemini Live on Cloud Run. **Until that works, intake uses browser voice**, disclosed as browser voice in the video and deck. R2 is not complete until a real call passes the CP3 gate; a failed gate needs an explicit written scope revision by both humans | user decision; spend still open |
| D6 | **Flood data uses real past events instead of a fictional locality.** Main operational scenario: **Hat Yai / Songkhla, Nov 2025**. Second package: **Bangkok, 24–28 Sep 2026**, map and area briefing only, with no synthetic operational records. Extents are computed by ReachPoint from Copernicus Sentinel-1 and precomputed; the app makes no live Earth Engine calls. Households, teams, calls and quantities stay synthetic and labeled; landmarks stay generic (L1–L3, D1); no own depth model | user decision; revises 0005 |

## What this revises

- [0005](0005-prototype-scope-proposal.md) / [scope v1](../product/prototype-scope-v1.md): "one bounded fictional locality" becomes two real past-event packages (D6). The five experiences, rules, fixture IDs, quantities and acceptance checks are unchanged. The P-A/P-B/P-C geometry now sits inside the Hat Yai extent.
- [0007](0007-logical-architecture-proposal.md): the logical architecture now has a proposed physical mapping (D2–D4). The logical rules, including no AI write path to authoritative records, are unchanged.
- AGENTS.md / README / CLAUDE.md: implementation is no longer forbidden from 12 Oct, within D1–D6. Paid services still need the spend decision below. Deployment is limited to the hackathon demo on `reachpoint-main`.

## Amendments (user decisions later on 2026-10-11)

- **D5 superseded: no real phone line in the prototype.** The user decided that a real call isn't needed for this prototype. A browser **call screen** represents a phone call for elderly users who aren't comfortable with technology, and it is disclosed as such in the video and deck. R2 is deferred beyond the prototype ([requirements](../product/requirements.md)). A real Thai phone line is a TODO after the hackathon. The Twilio upgrade, the AIS forwarding question and the CP3 phone gate are no longer needed.
- **D1 checkpoint wording.** CP2 becomes "publish → a team takes a family group → resident window per group". CP3 drops the phone gate.
- **Pull model (design decision 21A).** Reviewed cases are published to shared priority lists; the first capable team to accept wins; there are no offers, timers or reservations before acceptance. The lifecycle (family groups, job endings, outdated-case checks, distance ordering, server-checked resident messages, coordinator-only solver) was settled in the eng re-check: see the [design doc](../designs/resource-split-and-live-loop.md) ("Eng re-check decisions") and the research in [real rescue practice](../research/real-rescue-practice.md).
- **Routine relief planner becomes a stretch goal (revises 0005).** The separate P-A planner and coordinator review of routine plans move after CP3; P-A supplies stay in the solver's split as supply listings.
- **Work split refinement (refines 0006).** The user also owns the shared priority tiers/sort and the coordinator split panel; see the [delivery agreement](../collaboration/two-person-delivery-agreement.md#who-owns-what).
- **Build-week review rule.** The owner may merge their own area after the checks pass; the other human reviews within about 4 hours; shared contract or state changes always need both.
- **Zone missions (D17–D20).** Non-emergency work is prioritised by zone and split into segments, one team each, following ICS divisions, INSARAG worksites and FEMA block search. RED emergencies stay one by one. The zone order is a fixed rule; the copilot may only propose changes. A synthetic vulnerable-residents register is coordinator-only. The "found a family who never called" scene is core in CP3, and the Bangkok package becomes a stretch goal.
- **Surge and the triage agent (D21–D24).** This is the headline "why": in Hat Yai, more than 20,000 people asked for help in one week.
  - AI files clear non-emergency requests automatically as "AI-read".
  - A triage agent ranks the live list directly, labelled and with reasons. A fixed safety floor applies, human overrides are final, and the agent never closes requests, promises times or assigns teams.
  - Any team may take an AI-flagged RED request at once and verify it on arrival.
  - A surge simulator is core in CP3.
  - This amends the requirement that AI proposals need coordinator approval; see requirements.
- These amendments are the user's decisions; like the rest of 0009, they bind both humans once the friend confirms.

## Still open (not decided here)

- Total spend cap and its split across projects (blocks CP0 billing). The Twilio and AIS questions are moot after the D5 amendment.
- Contract v1.0 freeze: the pack's §3–§4 record shapes, one assistance document per type per case, and resident visibility of reported-but-unreviewed problems.
- Thai intake with English for the other screens (still proposed).
- Exact Hat Yai P-A/P-B/P-C boundaries; whether Bangkok has a usable Sentinel-1 pass in the event window (checked first on 12 Oct).

## Consequences

Code work starts on task branches from `main` once this PR merges. Every claim in the video and deck must match a verified capability: real satellite extent (dated), synthetic operations, and a browser call screen that represents a phone call (no real phone line). No real resident data, clinical protocol or operational use is introduced.
