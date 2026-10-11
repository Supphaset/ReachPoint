# Working agreement

Exactly two human Data Scientists collaborate, with Codex, Claude and possibly other tools assisting. No clinical partner or firsthand disaster-response experience is confirmed. The public ReachPoint repository is the shared review destination. Documentation is submitted through a separate branch and pull request.

Use the procedure in [CONTRIBUTING.md](../../CONTRIBUTING.md). Keep it light: one task owner, one reviewer, one bounded issue, one branch/worktree, one active editing tool per checkout. Assign ownership of shared docs and interfaces in the task discussion. Do not have multiple AI tools edit the same directory concurrently.

Current human assignment: the user owns volunteer workspace/flood map; the friend owns resident/coordinator, chat/voice, reconciliation and database updates. See [decision 0006](../decisions/0006-two-person-work-split.md) and the [two-person delivery agreement](two-person-delivery-agreement.md) for mutual expectations. Detailed handoff/ownership additions remain recommendations until both humans confirm them. Implementation is authorized from 12 Oct within [decision 0009](../decisions/0009-implementation-start-and-technical-direction.md).

The data contract in the [joint decision pack](../planning/joint-decision-pack.md) §3–§4 details proposed screen reads, table ownership, submissions/results, example payloads and failure behavior. Both humans review and freeze shared interfaces before depending on them; neither side silently changes field meanings or writes arbitrary authoritative states.

During the build week (from 12 Oct), the other human reviews each PR within about 4 hours during working hours. The owner may merge their own area once its checks pass; any change to the shared contract or state meaning needs both humans. Tie-break: the area owner decides inside their area; for the shared contract the version already in the plan stands. AI comments support review but cannot approve scope, clinical policy, publication or merging on humans' behalf. Do not auto-merge, force-push, discard changes, or push to the default branch.

A task needs purpose, scope/exclusions, acceptance criteria, affected files, validation and dependencies. A PR needs outcome, validation and unresolved limitations. Only update accepted requirements after a human decision; link the dated record. If tools disagree, preserve the alternatives and ask the human owner to resolve the consequential choice.

The human approved ReachPoint as the name and a public repository with a minimal README bootstrap, followed by documentation on a separate review branch (decision 0008). The second human still needs a GitHub collaborator invite from the user before reviewing PR #1. Keep private account details outside tracked docs.
