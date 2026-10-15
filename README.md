# ReachPoint

Working direction for the Google Cloud AI Builder Cup 2026, Sustainability & Social Impact.

**Why ReachPoint:** in the Nov 2025 Hat Yai flood, more than 20,000 people asked for help in one week, and many were never reached. ReachPoint answers every caller in seconds and puts the most urgent at the top for everyone to see. The rest becomes zone missions, so a handful of people can run a city-wide flood response. See [how it works](docs/OVERVIEW.md).

We are two Data Scientists exploring how organized volunteer teams could plan where to help and what resources to bring, while coordinators validate/allocate emergency assistance and residents follow their own request status. The problem, operational partner and smallest useful scope still need evidence.

**Current phase: build week (12–18 Oct 2026).** [Decision 0009](docs/decisions/0009-implementation-start-and-technical-direction.md) authorizes implementation and sets the stack: React on Firebase Hosting, FastAPI on Cloud Run, Firestore, Gemini via Vertex AI, Google Maps. Flood data comes from real past events (Hat Yai Nov 2025 main, Bangkok Sep 2026 second); operational records are synthetic. The [joint decision pack](docs/planning/joint-decision-pack.md) holds the contract proposal, the walk-through and the daily plan. The old discussion prototype is not the specification and its code is not reused.

## Start here

**New here? Read [docs/START-HERE.md](docs/START-HERE.md) first.** It lists the few files each of us needs and what is safe to skip.

1. Read [shared AI instructions](AGENTS.md) and [working agreement](docs/collaboration/working-agreement.md).
2. Read the [brief](docs/product/brief.md), [requirements](docs/product/requirements.md) and the [design doc](docs/designs/resource-split-and-live-loop.md).
3. Check [decisions](docs/decisions/README.md), [hackathon rules](docs/hackathon.md) and [source register](docs/research/sources.md).
4. Consult [skills and verified status](docs/collaboration/skills.md) and the [discovery roadmap](docs/planning/roadmap.md).

[Context summary](docs/context.md) records the project history. Current topic documents remain authoritative. Raw supplied discussion is retained only in an ignored local archive.

## Local setup

### Temporary local persistence

The API uses in-memory demo state unless `REACHPOINT_DB_PATH` is set. To keep synthetic caller conversations, confirmed reports, coordinator/team changes, status links and replay progress across local server restarts, start it from the repository root with:

```bash
REACHPOINT_DB_PATH=local/reachpoint.sqlite3 REACHPOINT_VOICE=on uvicorn api.main:app --port 8081
```

The ignored SQLite file is local to one server process; `/api/demo/reset` clears it. A confirmed form, chat or voice request adds one row to `callers` with the caller-reviewed fields; unfinished chats remain in `call_sessions`. Existing `help_requests` tables migrate to `callers` on startup without changing retained fields. Do not put real household information in this demo. A local Cloud Run filesystem does not provide durable shared storage, so the selected Firestore deployment work remains separate. See [decision 0011](docs/decisions/0011-local-sqlite-interim.md).

Open `/desk` for caller reviews: transport candidates, emergency recommendations (1a, 1b, 2, 3), AI/Human provenance, evidence, history and an optional volunteer preparation summary. Production builds default to API data; `?data=api` remains available as an explicit override for development. New submissions and unreviewed rows loaded by the desk receive background review when `REACHPOINT_AI` is enabled, using the existing Gemini configuration. Disabled/unavailable AI leaves requests for human review, never automatically routine. Human changes cannot be overwritten by AI reruns. Summaries appear only in the responding team's active accepted job. Operational review is separate from case approval, clinical assessment and team commitment. These are synthetic demo endpoints with existing demo identities, not production authentication. See [decision 0014](docs/decisions/0014-desk-caller-ai-review.md) and [API contract](contract/api.md).

Use the [call conversation review script](docs/planning/call-conversation-test.md) to check chat, hands-free voice, corrections and confirmation with synthetic examples.

The public [ReachPoint repository](https://github.com/Supphaset/ReachPoint) has a minimal README on `main`. The project documentation and static review artifacts are published on `codex/project-foundation` in [draft PR #1](https://github.com/Supphaset/ReachPoint/pull/1); a human reviews and merges them. See [decision 0008](docs/decisions/0008-reachpoint-name-and-public-repository.md) for the approved name and publication boundary.

Application code and its setup instructions arrive from 12 Oct under `web/`, `api/`, `contract/` and `data/` ([0009](docs/decisions/0009-implementation-start-and-technical-direction.md)). Until then, review documentation links and run `git diff --check` before committing. See [contributing](CONTRIBUTING.md) for task ownership and review.

## Current review package

Start with the [concrete prototype v1 scope](docs/product/prototype-scope-v1.md), human-approved in [decision 0005](docs/decisions/0005-prototype-scope-proposal.md). The current plan is the [design doc](docs/designs/resource-split-and-live-loop.md) (approved product design, design-review and eng re-check decisions, approved mockups) and the [joint decision pack](docs/planning/joint-decision-pack.md) (stack, data contract, transitions, schedule), backed by the [real rescue practice research](docs/research/real-rescue-practice.md). Older drafts and wireframes were removed on 2026-10-11 and remain in git history.

Prototype v1 scope is approved; [0009](docs/decisions/0009-implementation-start-and-technical-direction.md) replaces its fictional locality with real past-event flood packages and authorizes implementation. The phone provider and spend remain open.

The [two-person delivery agreement](docs/collaboration/two-person-delivery-agreement.md) documents the assigned split: volunteer workspace/flood map for the user; resident/coordinator, chat/voice, reconciliation and database updates for the friend. It includes recommended responsibility boundaries, the shared handoff contract and joint acceptance checks.

The data contract and state transitions are in the [joint decision pack](docs/planning/joint-decision-pack.md) §3–§4, updated by the design doc's pull-model rules (who reads what, who updates shared records, synthetic payloads and errors). The starter API is in `api/`; optional local SQLite persistence is described above. The shared deployment database is still future work.

See the [proposed architecture diagrams](docs/planning/architecture-overview.md) for the whole-system connections, workstream ownership and emergency/status feedback sequence. Components/providers remain unselected.
