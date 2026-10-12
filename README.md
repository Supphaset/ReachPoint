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

The public [ReachPoint repository](https://github.com/Supphaset/ReachPoint) has a minimal README on `main`. The project documentation and static review artifacts are published on `codex/project-foundation` in [draft PR #1](https://github.com/Supphaset/ReachPoint/pull/1); a human reviews and merges them. See [decision 0008](docs/decisions/0008-reachpoint-name-and-public-repository.md) for the approved name and publication boundary.

Application code and its setup instructions arrive from 12 Oct under `web/`, `api/`, `contract/` and `data/` ([0009](docs/decisions/0009-implementation-start-and-technical-direction.md)). Until then, review documentation links and run `git diff --check` before committing. See [contributing](CONTRIBUTING.md) for task ownership and review.

## Current review package

Start with the [concrete prototype v1 scope](docs/product/prototype-scope-v1.md), human-approved in [decision 0005](docs/decisions/0005-prototype-scope-proposal.md). The current plan is the [design doc](docs/designs/resource-split-and-live-loop.md) (approved product design, design-review and eng re-check decisions, approved mockups) and the [joint decision pack](docs/planning/joint-decision-pack.md) (stack, data contract, transitions, schedule), backed by the [real rescue practice research](docs/research/real-rescue-practice.md). Older drafts and wireframes were removed on 2026-10-11 and remain in git history.

Prototype v1 scope is approved; [0009](docs/decisions/0009-implementation-start-and-technical-direction.md) replaces its fictional locality with real past-event flood packages and authorizes implementation. The phone provider and spend remain open.

The [two-person delivery agreement](docs/collaboration/two-person-delivery-agreement.md) documents the assigned split: volunteer workspace/flood map for the user; resident/coordinator, chat/voice, reconciliation and database updates for the friend. It includes recommended responsibility boundaries, the shared handoff contract and joint acceptance checks.

The data contract and state transitions are in the [joint decision pack](docs/planning/joint-decision-pack.md) §3–§4, updated by the design doc's pull-model rules (who reads what, who updates shared records, synthetic payloads and errors). No backend or database has been built yet.

See the [proposed architecture diagrams](docs/planning/architecture-overview.md) for the whole-system connections, workstream ownership and emergency/status feedback sequence. Components/providers remain unselected.
