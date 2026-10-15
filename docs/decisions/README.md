# Decision log

Only explicit human approvals are accepted product decisions. AI recommendations stay proposed. Current authoritative requirements live in [requirements](../product/requirements.md).

| Record | Status | Subject |
|---|---|---|
| [0001](0001-foundation-and-scope.md) | Accepted setup boundary, directly instructed by user | Retain local repo; shared documentation; discovery only |
| [0002](0002-satellite-estimation-request.md) | Accepted requested capability; approach/MVP unapproved | Satellite-informed building and population exposure estimates |
| [0003](0003-map-emphasis-request.md) | Accepted requested capability/emphasis; approach/MVP unapproved | Map emphasis in product and wireframes |
| [0004](0004-workflow-reframe-request.md) | Accepted requested jobs and hybrid operating direction; policies/MVP unapproved | Volunteer daily planning, capacity and resident/emergency workflow |
| [0005](0005-prototype-scope-proposal.md) | Accepted prototype scope; implementation unapproved | Prototype v1 scope, five experiences and integrated demo |
| [0006](0006-two-person-work-split.md) | Accepted human work assignment; detailed handoff proposed | Volunteer/map versus resident/coordinator ownership |
| [0007](0007-logical-architecture-proposal.md) | Proposed logical architecture; technologies/implementation unapproved | Shared backend, review/state rules and connected views |
| [0008](0008-reachpoint-name-and-public-repository.md) | Accepted name and public documentation publication | ReachPoint, public repository and review PR |
| [0009](0009-implementation-start-and-technical-direction.md) | Accepted by the user; friend confirmation pending | Implementation from 12 Oct, stack A, Google Cloud layout, real past-event flood packages, browser-voice interim intake |
| [0010](0010-surge-demonstration-and-exception-review.md) | Accepted user clarification, 12 Oct 2026 | 1,000+ synthetic-request demonstration; automatic organization and human exception review |
| [0011](0011-local-sqlite-interim.md) | Accepted by user, 13 Oct 2026 | Temporary local SQLite persistence and caller-confirmed `help_requests`; deployed database remains future work |
| [0012](0012-shared-caller-schema.md) | Accepted by user, 13 Oct 2026 | Form, chat, voice and `help_requests` share 15 fields; no caller name; required phone and food/evacuation type |
| [0013](0013-caller-tracking-demo.md) | Accepted by user, 13 Oct 2026 | Four-step tracking, prominent copy link and local demo controls |
| [0014](0014-desk-caller-ai-review.md) | Accepted by user, 15 Oct 2026 | Caller table rename; AI/Human operational review, routine Level 3 and optional preparation summary |

For the next consequential choice create `0015-<topic>.md` with date, status (proposed/accepted/superseded), human approval reference, context/evidence, decision, rationale, alternatives, consequences and affected docs. Drafting a record does not accept it. Preserve superseded decisions and link replacements.

Prototype v1 scope is accepted in 0005 and revised by 0009 (real past-event flood packages instead of a fictional locality). 0009 selects the framework, database, hosting, map and AI route, pending the friend's confirmation. Telecom provider, spend cap and any real clinical workflow are not accepted. Public repository visibility is accepted in 0008.
