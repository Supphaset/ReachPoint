# ReachPoint — two-person delivery agreement

Date: 2026-10-11, revised the same day after the eng re-check. Owners: **You** (the user, volunteer workspace and flood map) and **Friend** (resident and coordinator side, intake, database). This revision is the user's proposal; it binds both humans once the friend confirms it in PR #1.

The base assignment is accepted in [decision 0006](../decisions/0006-two-person-work-split.md). The build is authorized from 12 Oct by [decision 0009](../decisions/0009-implementation-start-and-technical-direction.md), including its amendments. What we build is set out in:
- the [design doc](../designs/resource-split-and-live-loop.md): the pull model, the eng re-check decisions D1–D14 and the approved mockups;
- the [joint decision pack](../planning/joint-decision-pack.md): the data contract (§3), transitions (§4), flood data (§5.1b–c), checkpoints (§6) and walk-through (§7).

## This week at a glance

| When (Bangkok) | You | Friend | Joint checkpoint |
|---|---|---|---|
| Mon 12 | Earth Engine flood check + Hat Yai extent (pack §5.1c); zone boundaries; area-briefing fixtures **by noon**; **frontend foundation:** app shell, role routes, placeholder tokens, data hooks | `reachpoint-main` + budget alert; FastAPI skeleton on Cloud Run; Firestore + seed; 4 test roles; ADK hello-world | **CP0:** both deployed URLs load; contract v1.0 frozen together |
| Tue 13 | `/design-consultation` → final tokens; shared components ready for both; exposure estimate per zone (Open Buildings + WorldPop + DOPA); area briefing on live views; `tiers.py` + colour/distance sort | Text intake → Gemini proposed facts → desk approve → case/listing; view regeneration | **CP1:** text report → approved → on your P-B list/map, count unchanged |
| Wed 14 | Team list: take family groups, set window, progress, hand back, end outcomes, Busy reason | `claimListing` / hand-back / close rules with `NEED_CHANGED` + `ALLOCATION_CLOSED`; open lists per assistance type; resident status per family; browser call screen (ADK Live, fallback decided at 12:00) | **CP2:** publish → you take Families 1+2 → resident sees the per-family window |
| Thu 15 | Split panel with OR-Tools solver + "Ask these teams" + What-if; Gemini zone briefing text | Resource-failure review → hold + relist unfinished groups; message templates with "No longer current"; history view | **CP3:** full walk-through (pack §7), including the S1 failure |
| Fri 16 | Consistency pass across all six screens + accessibility review; map/UX polish; stretch: routine planner | Copilot read-only Q&A; retry/conflict handling; Firestore rules | Feature freeze 18:00; run the joint checklist below |
| Sat 17 | Video shots + deck: impact, map, data honesty | Video shots + deck: architecture, AI | **Submit by 21:00** |

Daily 15-minute check-in: what changed in `contract/`, which checkpoint passed, the blocker and its owner, and the next integration step.

## Who owns what

| Area | You | Friend |
|---|---|---|
| Flood map, zones, landmarks, exposure estimate | Build | Store/publish the files and views |
| Zone briefing (Gemini text from computed fields) | Build (prompt + UI) | Serve the view |
| Priority tiers, colour and distance sort (`api/rules/tiers.py`) | **Build** (shared with the solver) | Call it when listings change |
| Split solver (`api/rules/allocation.py`, OR-Tools) | Build | Call it, persist suggestions |
| Coordinator split panel, "Ask these teams", What-if | **Build** | Provide the direct-ask operation |
| Team list + mission screen (take, window, progress, hand back, end outcomes, Busy reason/ETA, re-confirm request) | Build | Enforce the rules behind each action |
| Copilot agent definition (instructions, tool choice) | Build | Provide the read-only tool layer |
| Resident call screen + Thai voice agent (ADK Live → push-to-talk → text) | — | Build |
| Fact extraction, matching calls to existing cases | — | Build |
| Coordinator desk (review, approve/reject, groups, messages) | — | Build |
| Rules engine: publish, claim, hand back, close, revisions, failure handling | Review | **Build** |
| Firestore model, open lists, resident status per family, history | Review | Build |
| Auth, Firestore rules, `reachpoint-main`, deploy (`scripts/deploy.sh`) | Backup Editor | Build + own |
| Contract (`api/contract/`, generated JSON Schema + TS types) | Co-own | Co-own |
| **Frontend foundation** (`web/src/shell`, `web/src/ui`, `web/src/data`): app shell, role routes, design tokens, shared components, data hooks, copy rules | **Build + own** | Use it; propose new shared parts |

The split panel and the shared tiers moved to you on 2026-10-11 (user proposal) because both sit on your solver and your friend's side carries the integration load.

### Frontend: one foundation, screens by workflow

There is one React app, but two people build screens on it. Each screen stays with the person who owns its backend logic: the call screen with the voice agent, and the desk with the proposals. You own the shared foundation, so all six screens look like one product (UX is a judging criterion).

| Foundation part | Contents |
|---|---|
| App shell | One React app, role-based routes, ReachPoint wordmark, bottom tab bar under 768 px |
| Design tokens | State colours (red/yellow/green and job states), Thai + Latin fonts, type scale, spacing; set by `/design-consultation` on Tue 13 |
| Shared components | Status chip, priority badge, dashed "AI proposal" card, error/offline banner, "last updated" line, large buttons |
| Data hooks | Sign-in, live Firestore view subscriptions, an API client typed from the generated contract |
| Copy rules | Thai first; the honest-wait wording from the design doc |

Rules:
- New shared components go through you.
- Parts used by only one screen stay with that screen's owner.
- No screen defines its own colours or fonts.
- On Fri 16 you do one consistency pass across all six screens before the accessibility review.

## Scope for the build week

- **Core:** the emergency loop from call → review → priority list → team takes a family → resident status, the S1 failure, the split panel with What-if, and the flood map with zone briefings.
- **Supplies stay in the split.** P-A food packs are allocated by the solver as supply listings that teams can take in part.
- **Stretch goal (after CP3): the separate routine relief planner.** That's the P-A "80 needed / 20 received / 30 committed" draft proposal and the coordinator review of routine plans. This is the user's proposal; it revises scope v1 ([0005](../decisions/0005-prototype-scope-proposal.md)) once the friend confirms.
- **Not in the prototype:** a real phone line, imported requests from other channels, and live flood feeds (see [TODOS](../../TODOS.md)).

## What crosses the boundary

The [integration map](integration-map.md) has the full diagram, numbered connections C1–C11 with their contract and fixture, the two cross-boundary sequence diagrams, and how our tests cover each connection.

| Producer → consumer | Action | Required result |
|---|---|---|
| You → Friend | Area, zone and landmark catalogue; flood and exposure files | Stable IDs and versions; source dates and uncertainty kept |
| Friend → You | Reviewed cases as listings (family groups, `needRevision`, `lastConfirmedAt`) | Appear in the open list for their assistance type; unreviewed reports never do |
| You → Friend | Take groups (`claimListing` with the revision seen) | One winner per group; `ALREADY_TAKEN` / `NOT_ENOUGH_CAPACITY` / `NEED_CHANGED` shown clearly |
| You → Friend | Window, progress, hand back, end outcome, Busy reason/ETA | Resident sees the window per family only after it's set; a closed job rejects late updates |
| You → Friend | Resource unavailable; field observation | Creates desk attention; after review, unfinished groups are relisted and linked messages marked "No longer current" |
| You → Friend | Split suggestion + "Ask these teams" | Direct asks to teams; nothing is assigned until a team takes it |
| Friend → You | Corrections (people count, group split, withdrawal) | Listing revision changes in the same transaction; open claims on the old revision fail |
| Friend → resident | Status and coordinator messages | Per family; team and time filled by the server; next update is not an arrival time |

Neither side keeps its own copy of missions or status. Fixture-only behaviour never counts as integrated.

## How we work during the build

- **Small PRs, one owner each.** One task, one branch (`codex/<task>` or `claude/<task>`), one editing tool per checkout ([CONTRIBUTING](../../CONTRIBUTING.md)).
- **Review rule.** The other human reviews within about 4 hours during working hours. The owner may merge their own area once the checks pass. **Any change to the shared contract or state meaning needs both humans.** No direct pushes to `main`, no force-push.
- **Tie-break.** Inside your own area, you decide. For the shared contract, if you still disagree after a short discussion, the version already in the plan stands and the alternative is noted in the PR.
- **Contract changes.** Propose them with a before/after example and the fixture impact; never rename a field without telling the other person.
- **Each handoff says:** what's ready, the contract version, a matching synthetic example, the checks actually run, known limits, and the next dependency.

## Joint acceptance checklist (future checks, not results)

| Check | Expected result | Lead / reviewer |
|---|---|---|
| Review gate | Nothing in cases, listings or views changes until the coordinator approves; a repeat call can't turn P-B's 24 into 27 | Friend / You |
| Take a family | Two teams tap the same group: one wins. Different groups: both win. A claim on an old revision gets `NEED_CHANGED` | Friend / You |
| Resident timing | No window before a team takes and sets it; status shown per family; medical stays separate | Friend / You |
| Priority order | Red always first; within a colour, nearest first; the solver and the list use the same tiers | You / Friend |
| S1 failure | Only unfinished groups go back on the list; the old window is withdrawn; "No longer current" + desk "Update needed"; unrelated jobs untouched | Both |
| Job endings | Done / Already left / Not found / Needs more help behave as designed; late updates on a closed job are rejected | Both |
| Map honesty | Flood layer labelled with its date and urban under-detection; unknown is never zero; exposure is a labelled range that never adds to counts | You / Friend |
| Retry and conflict | Retrying a submission has no duplicate effect; a stale version never overwrites a newer review | Friend / You |
| Permissions | A resident can't read another case; team leaders don't see transcripts or medical narrative; failed map tiles leave the list working | Both |

## Still open (decide together)

- Spend cap and payer (blocks CP0).
- Contract questions in pack §8, items 9–12.
- Your friend confirming 0009 and its amendments, this agreement, and owning `reachpoint-main`.
