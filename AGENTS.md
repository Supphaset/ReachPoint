# Shared instructions for AI collaborators

## Scope and authority

Project setup, documentation and online research are authorized. Product implementation is **not** authorized: do not build screens, services, databases, AI or telephone integrations, provision infrastructure, deploy, purchase services or enable paid features. A human must explicitly authorize implementation after scope review. Suggestions, skill outputs and prototype screens are not human approvals.

Before work, read this file, [current decisions](docs/decisions/README.md), the [brief](docs/product/brief.md), [requirements](docs/product/requirements.md) and relevant topic documents. Read [context](docs/context.md) for history, not as a competing current specification. Claude starts at [CLAUDE.md](CLAUDE.md). Other tools must be directed to this file explicitly if they do not discover it.

Keep accepted constraints, proposed approaches and unknowns visibly separate. Follow explicit human instructions over skill defaults. Preserve existing work. Do not choose a framework or silently turn a recommendation into a decision.

## Collaboration

Follow [CONTRIBUTING.md](CONTRIBUTING.md) and the [working agreement](docs/collaboration/working-agreement.md): one bounded issue and branch/worktree per task; one tool editing each working directory at a time; coordinate shared files and interfaces; use PRs reviewed by the other human. Never push directly to the default branch, auto-merge, force-push or discard someone else's changes. Do not create remote issues, invite people or alter access without repository details and explicit authorization.

Report scope, evidence, validation and limitations. Update the authoritative document and dated decision record when humans approve a consequential change. Commit/push only within the authorized task; check staged files for secrets and private context first.

## Product invariants

The authoritative constraints are in [requirements](docs/product/requirements.md). Keep need, review, commitment, progress, delivery report, confirmed receipt, referral and confirmed care separate. AI may propose evidence-linked events; reviewed records and deterministic logic govern quantities and states. Shared phones do not identify households; unknowns remain unknown; corrections preserve history; repeated submissions must not double-count.

Medical decisions require qualified governance; no autonomous diagnosis, prescribing or clinical triage is approved. Flood measurements must retain source, timestamp, units, reference and uncertainty; do not fabricate depth maps or safe routes.

## Evidence and data

Use synthetic households and medical examples only. Never print credentials, environment values or token substrings. Keep private account details, raw conversations, operational data and recordings out of Git. Follow [data handling](docs/collaboration/data-handling.md).

Public claims need primary sources where possible, URLs, access dates and limitations in [sources](docs/research/sources.md). Never invent interviews, adoption evidence, competitor omissions, integrations or eligibility. Verify current Google documentation, models, regions and costs when technical decisions are authorized. Private MCP data alone does not support public claims.

## Tools and skills

Use only explicitly registered connectors. Consult [skills](docs/collaboration/skills.md) before installation; no package installs by default, no global configuration replacement, no unreviewed scripts. Skill availability does not grant permission to ship, deploy, change accounts or implement. Profiles from the supplied global agreements remain defaults: public writing uses cited verification; reviews prefer diffs; `--apply` requires explicit human approval; destructive operations require consent. No such operation is needed for this setup.

Use minimum meaningful validation. Documentation-only work needs link, whitespace and sensitive-content checks, not application tests. Record checks actually run; distinguish file presence from runtime verification.
