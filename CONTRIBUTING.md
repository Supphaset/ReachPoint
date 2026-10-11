# Contributing

Exactly two human collaborators own this project. AI tools assist; human review grants approval.

1. Agree on a bounded task with acceptance criteria. Once GitHub is configured and issue creation authorized, use the local [task template](.github/ISSUE_TEMPLATE/task.md).
2. Assign one human owner and one branch or worktree per task. Use `codex/<task>` for Codex work and `claude/<task>` for Claude Code work. Check `git status` before editing; preserve others' changes. An existing checkout must have only one active editing tool.
3. Reserve shared documents and proposed interface changes in the task discussion before editing. A second tool uses a separate checkout and task.
4. Make a focused change. Record evidence and mark proposals. Update relevant docs when an approved decision changes.
5. Validate according to the task. For documentation: check relative links, source URLs/access dates, whitespace, secret/private content and scope. `git diff --check` checks tracked changes; review new files separately.
6. Open a PR only after a remote and publishing authorization exist. Use the [PR template](.github/pull_request_template.md). The other human reviews (within about 4 hours during the build week); the owner may merge their own area after checks pass, but shared contract or state changes need both humans. AI review is advisory. No automatic merge or direct push to the default branch.

Do not force-push, discard another person's changes, invite collaborators or change repository visibility without explicit authorization. Do not commit real household data, medical details, recordings, credentials or machine paths. Review ignored files too: `.gitignore` is not a security scanner.

## First publication

ReachPoint and public repository creation/publication are approved in decision 0008. The repository is initialized with a minimal README; the planning package is submitted on a separate review branch. Confirm CLI/connector authentication privately. Review curated context and source provenance before publication. A public source repository is required at submission; initial visibility is a human choice. Licensing and any later visibility change also need a human decision.

Then create the first reviewed local commit on the task branch, configure the chosen remote, publish the branch and use a PR where an existing default branch exists. For any future new empty remote, agree on the initial default-branch bootstrap before publishing. No GitHub automation, access changes or paid services are configured here.
