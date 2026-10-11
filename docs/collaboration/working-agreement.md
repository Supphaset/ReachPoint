# Working agreement

Exactly two human Data Scientists collaborate, with Codex, Claude and possibly other tools assisting. No clinical partner or firsthand disaster-response experience is confirmed. The public ReachPoint repository is the shared review destination. Documentation is submitted through a separate branch and pull request.

Use the procedure in [CONTRIBUTING.md](../../CONTRIBUTING.md). Keep it light: one task owner, one reviewer, one bounded issue, one branch/worktree, one active editing tool per checkout. Assign ownership of shared docs and interfaces in the task discussion. Do not have multiple AI tools edit the same directory concurrently.

Current human assignment: the user owns volunteer workspace/flood map; the friend owns resident/coordinator, chat/voice, reconciliation and database updates. See [decision 0006](../decisions/0006-two-person-work-split.md) and the [two-person delivery agreement](two-person-delivery-agreement.md) for mutual expectations. Detailed handoff/ownership additions remain recommendations; implementation still requires separate authorization.

The [draft volunteer/backend contract](volunteer-backend-contract-v1.md) details proposed screen reads, table ownership, submissions/results, example payloads and failure behavior. Both humans review and freeze shared interfaces before depending on them; neither side silently changes field meanings or writes arbitrary authoritative states.

The other human reviews a PR. AI comments support review but cannot approve scope, clinical policy, publication or merging on humans' behalf. Do not auto-merge, force-push, discard changes, or push to the default branch. A human merges after acceptance checks.

A task needs purpose, scope/exclusions, acceptance criteria, affected files, validation and dependencies. A PR needs outcome, validation and unresolved limitations. Only update accepted requirements after a human decision; link the dated record. If tools disagree, preserve the alternatives and ask the human owner to resolve the consequential choice.

The human approved ReachPoint as the name and a public repository with a minimal README bootstrap, followed by documentation on a separate review branch (decision 0008). The second human's GitHub access remains unresolved; no invitations have been sent. Keep private account details outside tracked docs.
