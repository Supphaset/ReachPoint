# 0001 — Foundation and scope boundary

Date: 2026-10-11 (Asia/Bangkok)
Status: Accepted setup constraints; implemented locally.
Approval basis: Explicit human setup request supplied in the context archive; no independent AI approval implied.

## Decision and rationale

Retain the existing empty local Git repository. Create a lightweight Markdown foundation shared by two humans, Codex, Claude and other tools. Keep instructions in AGENTS.md, a short Claude entry point, one canonical document per topic and a historical context archive. Use task branches and human-reviewed PRs; preserve existing work.

Product implementation, integrations, infrastructure, deployment and purchases remain unauthorized. No remote is configured or published without owner/name/visibility and authorization.

## Alternatives

A new repository elsewhere adds unnecessary fragmentation. Application scaffolding would prematurely choose a stack. Treating the UI as a final specification would settle unresolved product questions without evidence. Installing duplicate global skill suites would add drift and configuration risk.

## Consequences

Foundation work is on `codex/project-foundation`; no initial commit/push has been made. Local documents and GitHub templates are reviewable. Skill recommendations do not require new installations now. Product decisions and GitHub publication remain pending.
