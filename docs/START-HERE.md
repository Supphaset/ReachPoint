# Start here

The repo has about 40 files, but each of us needs only about 4 of them, and only parts of the two long ones. Most of the rest is history or background. Reading the list below takes about 40 minutes.

**First, read the [overview](OVERVIEW.md)** (10 minutes): the whole flow, a job's lifecycle, components and owners, and where the AI is. Then check your tasks in the [build-week task list](planning/build-week-tasks.md).

## Both of us

| # | File | Read | Skip |
|---|---|---|---|
| 1 | [Delivery agreement](collaboration/two-person-delivery-agreement.md) | All (about 110 lines): the week table, who owns what, the frontend foundation, what crosses the boundary, the review rule | — |
| 2 | [Decision 0009](decisions/0009-implementation-start-and-technical-direction.md) | The decisions table and **Amendments** | — |
| 3 | [Design doc](designs/resource-split-and-live-loop.md) | "What Makes This Cool"; step **3a** (pull model) and **3b** (failed resource); **Eng re-check decisions**; the Approved Mockups table; the state table in Pass 2 | Reviewer Concerns, Cross-Model Perspective, "What I noticed", the review reports at the end |
| 4 | [Joint decision pack](planning/joint-decision-pack.md) | The "read first" box at the top; **§6** (tasks, checkpoints, acceptance criteria); **§7** (the walk-through) | §1, §2 (stack options, already decided); §5.1a; §5.2/§5.2a (phone, dropped) |

## Volunteer and map owner (user)

- Pack **§5.1b–§5.1c**: the flood events, the Monday flood check, and the exposure estimate.
- Design doc **Pass 1** and **Pass 6**: the split panel layout, map levels, and phone layout.

## Intake, coordination and backend owner (friend)

- Pack **§3 and §4**, in full: the data contract, examples, permissions and transitions.
- Design doc **Approach C, steps 1–2**: the voice fallback ladder and agent ownership.
- [Data handling](collaboration/data-handling.md) (16 lines): what must never go into seeds or the repo.
- Pack **§8, questions 9–12**: these need your answers before the contract freeze.

## Only when needed

| File | When |
|---|---|
| [Requirements](product/requirements.md) | When a rule is unclear, e.g. "unknown is never zero" or "no AI clinical triage" |
| [Hackathon](hackathon.md) | When writing the deck: judging criteria and deadline |
| [Real rescue practice](research/real-rescue-practice.md) | When someone asks why the workflow is designed this way |
| [TODOS](../TODOS.md) | After the hackathon |
| [CONTRIBUTING](../CONTRIBUTING.md), [working agreement](collaboration/working-agreement.md) | Once, for branch and review rules (the delivery agreement summarises them) |

## Safe to skip

- **Decisions 0001–0008.** They record how we got here; 0009 and its amendments override what matters.
- **Older product docs:** `context.md`, `planning/roadmap.md`, `product/brief.md`, `product/prototype-prd.md`, `product/prototype-scope-v1.md`. They are kept as the accepted scope record, but in practice the design doc replaces them.
- **`planning/architecture-overview.md`.** Its diagrams predate the pull-model decisions.
- **Other research:** `competitors.md`, `sources.md`, `gaps-and-assumptions.md`, `prototype-feasibility.md`, `flood-situation-updates.md`, `unreported-needs.md`.
- **`collaboration/skills.md`, `AGENTS.md`, `CLAUDE.md`, `.github/` templates.** These are instructions for AI tools and GitHub.
