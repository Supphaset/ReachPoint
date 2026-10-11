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

## Still open (not decided here)

- Total spend cap and its split across projects; who pays for the Twilio upgrade (blocks D5 testing and CP0 billing).
- The AIS answer on international forwarding (call 1175).
- Contract v1.0 freeze: the pack's §3–§4 record shapes, one assistance document per type per case, and resident visibility of reported-but-unreviewed problems.
- Thai intake with English for the other screens (still proposed).
- Exact Hat Yai P-A/P-B/P-C boundaries; whether Bangkok has a usable Sentinel-1 pass in the event window (checked first on 12 Oct).

## Consequences

Code work starts on task branches from `main` once this PR merges. Every claim in the video and deck must match a verified capability: real satellite extent (dated), synthetic operations, browser voice unless the phone gate passes. No real resident data, clinical protocol or operational use is introduced.
