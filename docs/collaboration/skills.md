# Skills and verified status

> **Status update 2026-10-11 (later):** `/office-hours`, `/plan-eng-review` (twice, with the Codex CLI outside voice on the ChatGPT subscription) and `/plan-design-review` have run on the plan. Next: `/design-consultation` and an accessibility review before styling; `/review`, `/qa-only` and `/audit` once screens exist. The version details below are the original inventory and may be out of date.

Inventory date: **2026-10-11**. Recommendations are optional capabilities, not automatic workflow or implementation approval. No skill/package was installed, upgraded or executed as a product workflow during setup. `find-skills` was used for discovery; existing files, headers and dependencies were inspected.

## Small recommended set

Start with office-hours for problem discovery. Add plan-eng-review once scope is agreed; use browse/qa-only, audit, review and cso when their targets exist. Use primary-source browsing plus the source register for research rather than adding a generic research package. Defer Google integration skills until technical planning needs them.

### Gstack: local evidence and compatibility

Source: [garrytan/gstack](https://github.com/garrytan/gstack). On this machine:

| Host | Verified file state | Checkout version / commit | Runtime status |
|---|---|---|---|
| Codex | Selected skill files exist and are exposed in this session's catalog | 1.57.10.0 / `a5833c413f98b13f105beac96262e8098b628461` | Availability verified; workflows not run; old skill preambles contain Claude-specific paths/tool names |
| Claude Code | Selected skill files exist in its user skill checkout | **1.91.83.0** / `5cb5e1cf` (upgraded 2026-10-11 at the user's request via `/gstack-upgrade`; previously 1.60.1.0 / `a3259400`) | Upgrade, setup and migrations completed; setup registered a gstack timeline Stop hook in the user's Claude settings |

Current [upstream version](https://raw.githubusercontent.com/garrytan/gstack/main/VERSION) was 1.91.70.0. Neither local checkout was updated. The [README](https://github.com/garrytan/gstack) lists Claude as full support and Codex as experimental, with different installation targets and advisory safety on Codex. These upstream statements do not certify our older local installs. Do not assume identical names, hooks or formats across tools.

| Skill / local header version | Purpose and timing | Why useful here | Permissions / dependencies | Status and fallback |
|---|---|---|---|---|
| office-hours / 2.0.0 | Problem discovery before features | Challenge user, pain, evidence and scope | Read/write discovery docs; web; shell preamble/global state behavior; no runtime needed for manual method | Present for both hosts; recommended first, runtime unverified. Fallback: open-questions + published evidence review |
| plan-eng-review / 1.0.0 | Architecture and implementation planning after human scope decision | Examine states, data flows, failures and meaningful tests | Read/write plans, shell/web; host-specific preamble | Present both; recommended later. Fallback: written alternatives/edge-case review |
| browse / 1.1.0 | Browser verification against an authorized target | Verify rendered behavior rather than trust screenshots | Browser executable, Bun, browser runtime; shell, network, local state; interactions must fit authorization | Present both; browse executable exists in Codex checkout, browser session not tested. Fallback: built-in browser tools/manual review |
| qa-only / 1.0.0 | Report-only end-to-end QA after a target exists | Assess flows/failures without automatically implementing fixes | Browse runtime; network, screenshots/report writes; synthetic data | Present both; runtime unverified, no app target built. Fallback: human scenario checklist |
| review / 1.0.0 | Review a bounded change/PR | Check logic, trust boundaries and risky side effects | Git diff, read/write/edit, shell and possible agent tools; gh/auth for remote work | Present both; runtime unverified; gh auth not ready. Fallback: local diff review by AI plus other human |
| cso / 2.0.0 | Authorized security/threat review when code/data design exists | Sensitive medical/location data and untrusted intake | Shell/files/web, helpers and toolchain; active checks require authorized target; transitive runtime prerequisites not verified | Present both; security runtime not assessed. Fallback: documented threat model and manual trust/permission review |

All rows share the host-specific versions/commits above. Header versions are from the inspected Codex checkout; they are not proof that Claude files are identical. plan-ceo-review is also present (1.0.0 locally), but office-hours covers the immediate need; avoid piling on overlapping planning rituals.

Bun 1.3.13, Git, Codex CLI, Claude CLI and GitHub CLI were detected. Current gstack README recommends tested Bun 1.4.2+ and describes an older-version floor; detection alone does not establish compatibility with today's upstream build. Authentication for Codex/Claude, browser launch, CSO helper readiness and cross-model review were not tested.

### UX/accessibility

Source: [Impeccable](https://github.com/pbakaus/impeccable). Local `audit`, `shape`, `critique` and prerequisite `impeccable` files exist and are catalogued for Codex; headers report 2.1.1. Selected recommendation: **audit**, for accessibility, responsiveness and measurable UI quality after an approved target exists. It reports findings; it is not a complete WCAG compliance certification.

Local audit SHA-256: `877a126d91e1f72137ea94309282beca2fc756167aa38d27fd8e8eac70dc79d6`. Exact upstream commit/provenance match is unverified. Needs its impeccable context/teach prerequisite, file inspection and possibly browser checks. Codex availability verified; Claude installation and runtime not verified. Setup for another tool should follow its upstream host-specific distribution and be reviewed first. Fallback: keyboard/focus/contrast/error/uncertainty checklist and human review. Do not invoke a build-oriented prerequisite as authorization to build screens.

### Google AI and Cloud documentation

Source: [google-gemini/gemini-skills](https://github.com/google-gemini/gemini-skills), main inspected 2026-10-11; no release/commit pinned for installation. The README documents Codex and Claude installation routes; it also disclaims official product support. The discovery listing reports 23.5k installs and 4.3k stars ([listing](https://www.skills.sh/google-gemini/gemini-skills/gemini-api-dev)); popularity is not a security audit.

| Candidate | Purpose / project value | Setup, permissions and dependencies | Verified status / fallback |
|---|---|---|---|
| gemini-api-dev | Later API/SDK planning for evidence-linked proposals and structured outputs | Read SKILL.md/references; pin source first; reviewed project-local host installation where supported. Network to current docs; approved runtime would need SDK/auth/API costs | Upstream instruction inspected; no direct install found in checked Codex/Claude/shared user skill roots; not in this session catalog; not installed here. Runtime blocked by pending scope/architecture. Use official API docs now |
| gemini-live-api-dev | Later streaming/session planning if selected | Host-specific install; network, audio/session tooling and credentials only after approval | Upstream inspected; same local absence check; deferred. Live API is not an inbound phone network. Fallback: official docs and separate telecom feasibility |
| Google Cloud Gemini API skill | Cloud-specific planning; Gemini README says Vertex skill moved here | [Current source directory](https://github.com/google/skills/tree/main/skills/cloud/gemini-api), pin/audit full references before any install; future cloud auth/SDK/billing requires authorization | Directory confirmed; detailed skill/dependency audit pending; not installed here. Fallback: current Google Cloud docs |

For AI evaluation, start with the synthetic C-01 walk-through in the [joint decision pack](../planning/joint-decision-pack.md) §7, deterministic semantic checks and human labels. Consult the [current evaluation docs](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/evaluation-overview) later; a paid evaluation service or extra framework is not necessary for discovery. No testing/evaluation package is selected yet.

## Installation assessment and recommendation

The current gstack setup's host options, version checks and installation-state sections were inspected, not executed. It builds tools and can write agent/global state; README team mode includes hooks, auto-update and committing repository configuration. Its complete transitive build/install chain has **not** been security-reviewed here. No install is needed to complete this setup, so do not run its quick-start, auto-update/team-init or globally replace either existing version by default.

For a future team install: agree on a pinned version, inspect every executed script and dependency, test the selected host in isolation, prefer repository-local configuration where supported, document writes/network/telemetry/hooks and obtain consent for global changes. Keep downloaded dependencies and machine paths out of Git. Do not mandate gstack on both humans until each tool's runtime is verified.

Avoid ship/land-and-deploy/autoplan automation during discovery: their write/publish behavior exceeds current scope. Browser-cookie import is unnecessary and touches personal sessions. Do not add Supabase or framework skills while architecture remains open.

A practical fallback for every skill is the shared task, sources, decisions, workflow examples and human review process. Both humans can use this repository without installing any skill.
