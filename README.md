# ReachPoint

Working direction for the Google Cloud AI Builder Cup 2026, Sustainability & Social Impact.

We are two Data Scientists exploring how organized volunteer teams could plan where to help and what resources to bring, while coordinators validate/allocate emergency assistance and residents follow their own request status. The problem, operational partner and smallest useful scope still need evidence.

**Current phase: build week (12–18 Oct 2026).** [Decision 0009](docs/decisions/0009-implementation-start-and-technical-direction.md) authorizes implementation and sets the stack: React on Firebase Hosting, FastAPI on Cloud Run, Firestore, Gemini via Vertex AI, Google Maps. Flood data comes from real past events (Hat Yai Nov 2025 main, Bangkok Sep 2026 second); operational records are synthetic. The [joint decision pack](docs/planning/joint-decision-pack.md) holds the contract proposal, the walk-through and the daily plan. The old discussion prototype is not the specification and its code is not reused.

## Start here

1. Read [shared AI instructions](AGENTS.md) and [working agreement](docs/collaboration/working-agreement.md).
2. Read the [brief](docs/product/brief.md), [requirements](docs/product/requirements.md) and [open questions](docs/product/open-questions.md).
3. Check [decisions](docs/decisions/README.md), [hackathon rules](docs/hackathon.md) and [source register](docs/research/sources.md).
4. Consult [skills and verified status](docs/collaboration/skills.md) and the [discovery roadmap](docs/planning/roadmap.md).

[Context summary](docs/context.md) records the project history. Current topic documents remain authoritative. Raw supplied discussion is retained only in an ignored local archive.

## Local setup

The public [ReachPoint repository](https://github.com/Supphaset/ReachPoint) has a minimal README on `main`. The project documentation and static review artifacts are published on `codex/project-foundation` in [draft PR #1](https://github.com/Supphaset/ReachPoint/pull/1); a human reviews and merges them. See [decision 0008](docs/decisions/0008-reachpoint-name-and-public-repository.md) for the approved name and publication boundary.

No application dependencies, environment variables or build commands are required. Review documentation links and run `git diff --check` before committing. See [contributing](CONTRIBUTING.md) for task ownership and review.

## Current review package

Start with the [concrete prototype v1 scope](docs/product/prototype-scope-v1.md), human-approved in [decision 0005](docs/decisions/0005-prototype-scope-proposal.md). Review the [volunteer planning and emergency workflow](docs/product/volunteer-workflow-proposal.md) and [current prototype PRD](docs/product/prototype-prd.md) first. The latest human correction makes daily mission planning, uncovered response needs, emergency allocation and resident assistance status the starting point. The [earlier product detail](docs/product/product-detail.md), [wireframes](docs/design/wireframe-guide.md) and [synthetic scenario](docs/product/demo-scenario.md) are preserved prior drafts pending workflow review. [Replacement static wireframes](docs/design/workflow-wireframe-guide.md) translate the accepted scope; their layouts remain for review. Earlier quantity examples remain supporting invariants, not the headline demo.

Prototype v1 scope is approved; [0009](docs/decisions/0009-implementation-start-and-technical-direction.md) replaces its fictional locality with real past-event flood packages and authorizes implementation. The phone provider and spend remain open.

The [two-person delivery agreement](docs/collaboration/two-person-delivery-agreement.md) documents the assigned split: volunteer workspace/flood map for the user; resident/coordinator, chat/voice, reconciliation and database updates for the friend. It includes recommended responsibility boundaries, the shared handoff contract and joint acceptance checks.

The [draft volunteer/backend integration contract](docs/collaboration/volunteer-backend-contract-v1.md) makes that handoff concrete: what each screen reads, who updates shared records, proposed operations/fields, synthetic payloads and error handling. It specifies expectations; no backend or database has been built.

See the [proposed architecture diagrams](docs/planning/architecture-overview.md) for the whole-system connections, workstream ownership and emergency/status feedback sequence. Components/providers remain unselected.
