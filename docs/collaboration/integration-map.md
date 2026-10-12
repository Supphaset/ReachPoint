# Integration map: how our parts connect and how we test them

Companion to the [delivery agreement](two-person-delivery-agreement.md) and the [overview](../OVERVIEW.md).

- **User** owns the map, flood data, solver, tiers, team screens, split panel and the frontend foundation.
- **Friend** owns intake, the coordinator desk, the rules engine, Firestore, auth and deploys.
- Every place where one person's work touches the other's is a numbered **connection (C1–C11)**. Each connection has:
  - a contract (a model in `api/contract/`);
  - a fixture (a JSON example in `contract/fixtures/`);
  - a test on each side.

## 1. The whole system, by owner

```mermaid
flowchart LR
  subgraph USER["User"]
    direction TB
    EE["Earth Engine flood check<br/>+ exposure estimate"]
    PKG["Flood + area package<br/>data/hy-2025-11/"]
    UI_F["Frontend foundation<br/>shell · tokens · components · data hooks"]
    MAP["Map + zone briefing"]
    TEAM["Team list + mission"]
    SPLIT["Split panel + What-if"]
    TIERS["tiers.py<br/>colour → distance → waiting"]
    SOLVER["allocation.py<br/>OR-Tools solve_split"]
    BRIEF["Briefing prompts<br/>+ prose validator"]
    COPI["Copilot instructions<br/>+ tool choice"]
    EE --> PKG
  end
  subgraph SHARED["Shared"]
    direction TB
    CONTRACT["api/contract/ (Pydantic)<br/>→ JSON Schema + TS types"]
    FIX["contract/fixtures/*.json"]
    CONTRACT --- FIX
  end
  subgraph FRIEND["Friend"]
    direction TB
    CALL["Call screen"]
    VOICE["Voice agent<br/>Gemini Live (ADK)"]
    EXTRACT["Fact extraction<br/>Gemini Flash"]
    DESK["Coordinator desk"]
    RULES["Rules engine<br/>transitions.py"]
    TOOLS["Tool layer<br/>read / propose only"]
    FS[("Firestore<br/>records + views")]
    RES["Resident status"]
    ADK["ADK runtime"]
    CALL --> VOICE --> EXTRACT --> DESK --> RULES --> FS
    FS --> RES
    ADK --- TOOLS
  end
  PKG -- "C1 area package" --> RULES
  FS -- "C2 area briefing view" --> MAP
  TIERS -- "C3 sort_key()" --> RULES
  RULES -- "C4 AllocationInput → Suggestion" --> SOLVER
  FS -- "C5 open-list view" --> TEAM
  TEAM -- "C6 claim · hand back · close · update" --> RULES
  SPLIT -- "C7 askTeams" --> RULES
  RULES -- "C8 BriefingFacts → text" --> BRIEF
  COPI -- "C9 agent config" --> ADK
  UI_F -- "C10 components + hooks" --> CALL
  UI_F -- "C10" --> DESK
  UI_F -- "C10" --> RES
  CONTRACT -. "C11 generated types" .-> UI_F
  CONTRACT -. "C11" .-> RULES
```

## 2. The connections

| # | From → To | What crosses | Contract (in `api/contract/`) | Fixture | Needed by |
|---|---|---|---|---|---|
| **C1** | User package → Friend seed + rules | Areas, zones, landmarks, flood extent (GeoJSON in Cloud Storage), exposure ranges | `AreaPackage`, `Landmark`, `ExposureEstimate` | `areas.hy-2025-11.json` | Mon 12 noon |
| **C2** | Friend views → User map | Badges, Facts, Unknown row, cases in zone, exposure range, briefing text | `AreaBriefingView`, `ZoneBriefingView` | `areaBriefing.P-B.json` (+ empty, stale, failed-layer variants) | Mon 12 noon (fixture), Tue 13 (live) |
| **C3** | User `tiers.py` → Friend rules/views | `colour(listing)`, `sort_key(listing, team_location)` | Python function signature + `PriorityColour` enum | `listings.sort-cases.json` (shipped 12 Oct with `expectedOrder`; draft listing fields in `TierInput.from_listing`) | Tue 13 |
| **C4** | Friend snapshot → User solver → Friend persists | Reviewed needs, teams, resources, accepted allocations → assignments + unmet reasons | `AllocationInput`, `AllocationSuggestion` | `allocationInput.cp3.json` (shipped 12 Oct; hand run in `api/notebooks/split-solver.ipynb`), `allocationSuggestion.cp3.json` | Tue 13 (stub), Thu 15 (real) |
| **C5** | Friend views → User team list | Open listings per help type, with groups, `needRevision`, `lastConfirmedAt`, distance | `OpenListView`, `TeamView` | `openList.evacuation.json` | Wed 14 |
| **C6** | User team UI → Friend API | `claimListing`, `handBack`, `closeAllocation`, `submitTeamUpdate` (window, progress, status + reason/ETA, problem report, re-confirm request) | Request/response models + error codes `ALREADY_TAKEN`, `NOT_ENOUGH_CAPACITY`, `NEED_CHANGED`, `ALLOCATION_CLOSED`, `VERSION_CONFLICT` | `claim.*.json` (one per result) | Wed 14 |
| **C7** | User split panel → Friend API | `askTeams(suggestionId, inputVersions, teamIds)` → one-time "Can you take this?" on each team view | `AskTeamsRequest/Result` | `askTeams.ok.json`, `askTeams.stale.json` | Thu 15 |
| **C8** | Friend view regeneration → User briefing module | Computed zone facts → two Gemini sentences, or a fallback if blocked | `BriefingFacts` → `BriefingText` | `briefingFacts.B-3.json` | Thu 15 |
| **C9** | User copilot config → Friend ADK runtime | Instructions, allowed tool names, examples | `CopilotConfig` | `copilot.questions.json` | Fri 16 |
| **C10** | User frontend foundation → Friend screens | Shell, routes, tokens, `StatusChip`, `PriorityBadge`, `ProposalCard`, `OfflineBanner`, `useView(path)`, `api.*` | Component props + generated TS types | Storybook-style example page `/dev/ui` | Mon 12 (shell), Tue 13 (components) |
| **C11** | Shared contract → both | Pydantic models → `contract/schema/*.json` + `web/src/types/*.ts` | The models themselves | All fixtures | Mon 12 freeze |

What does **not** cross is internal to its owner. Examples: voice → extraction → desk (friend), and Earth Engine → package (user).

## 3. Two key flows across the boundary

**CP2: a team takes a family (Wed 14)**

```mermaid
sequenceDiagram
  participant Desk as Coordinator desk (Friend)
  participant Rules as Rules engine (Friend)
  participant FS as Firestore views (Friend)
  participant Team as Team list (User)
  participant Res as Resident status (Friend)
  Desk->>Rules: approve facts (C-01)
  Rules->>FS: listing rev 1 + openList view, sorted with tiers.py (C3)
  FS-->>Team: open list update (C5)
  Team->>Rules: claimListing(groups 1+2, rev 1) (C6)
  Rules-->>Team: accepted (or ALREADY_TAKEN / NEED_CHANGED)
  Team->>Rules: submitTeamUpdate(window 13:00–14:00) (C6)
  Rules->>FS: allocation + residentStatus per family
  FS-->>Res: "Family 1: boat on the way 13:00–14:00"
```

**CP3: boat S1 fails and the plan is redone (Thu 15)**

```mermaid
sequenceDiagram
  participant Team as Team list (User)
  participant Rules as Rules engine (Friend)
  participant Desk as Coordinator desk (Friend)
  participant Solver as solve_split (User)
  participant Split as Split panel (User)
  Team->>Rules: submitTeamUpdate(problem: S1 unavailable) (C6)
  Rules->>Desk: attention item
  Desk->>Rules: review → hold, relist unfinished groups (rev 2)
  Rules->>Solver: AllocationInput snapshot (C4)
  Solver-->>Rules: AllocationSuggestion
  Rules-->>Split: suggestion view
  Split->>Rules: askTeams([T-K]) (C7)
  Note over Rules,Team: T-K takes the family through C6 as usual
```

## 4. How our tests fit together

```mermaid
flowchart TB
  subgraph L1["1 · Unit tests"]
    U1["Each owner, every PR<br/>User: solver · tiers property test · package validator · UI components"]
    F1["Friend: transitions on Firestore emulator · idempotency · views · message rules · extraction parsing"]
  end
  subgraph L2["2 · Contract tests"]
    C["Shared, every PR<br/>Every fixture validates against the generated JSON Schema;<br/>regenerating schema/types gives no diff; TS compiles"]
  end
  subgraph L3["3 · Connection tests"]
    P["One pair per C1–C10<br/>Producer test: my real output matches the fixture shape"]
    K["Consumer test: my code handles every fixture variant"]
  end
  subgraph L4["4 · End-to-end"]
    E["Shared, before each checkpoint<br/>Playwright on the deployed URL: E2E-1 take a family · E2E-2 S1 failure"]
  end
  subgraph L5["5 · AI evals"]
    A["Owner of each AI part<br/>Thai intake · extraction · briefing validator · copilot citations · prompt injection"]
  end
  L1 --> L2 --> L3 --> L4
  L5 -.-> L4
```

The idea is that **each connection is tested from both sides against the same fixture**. The producer proves its output looks like the fixture; the consumer proves it handles the fixture. If both pass, the real connection works before we ever run them together. If someone changes a field, the contract test fails at once and names the file.

### Connection tests

| # | Producer test (proves the output) | Consumer test (proves handling) |
|---|---|---|
| C1 | **User:** `scripts/validate_package.py`: GeoJSON valid, < 300 KB, IDs unique, every landmark inside its zone, source dates present | **Friend:** the seed script loads the fixture into the emulator; area IDs resolve |
| C2 | **Friend:** regenerating P-B from seed matches `areaBriefing.P-B.json` (shape + counts: still 24 after C-01) | **User:** the map renders every variant (normal, empty "not checked", stale, flood layer missing → nothing shaded dry) |
| C3 | **User:** Hypothesis property test: red always first; same tiers as the solver; nearest first within a colour | **Friend:** the open-list view order equals `sort_key` order on `listings.sort-cases.json` |
| C4 | **User:** `solve_split` on `allocationInput.cp3.json` returns a valid suggestion in < 5 s; never exceeds capacity; tier 1a before tier 2 | **Friend:** storing a suggestion; a stale `inputVersions` → `VERSION_CONFLICT`, writes nothing |
| C5 | **Friend:** a team turning Available sees all open listings for its capability | **User:** the team list renders groups, colour, distance, "last confirmed 2h 40m ago" |
| C6 | **Friend:** two claims on the same group → one wins; disjoint groups → both win; old revision → `NEED_CHANGED`; closed → `ALLOCATION_CLOSED`; retry → no duplicate | **User:** the team UI shows the right message for every `claim.*.json` result and keeps the draft on network failure |
| C7 | **Friend:** `askTeams` creates exactly one prompt per team; a stale suggestion → `VERSION_CONFLICT` | **User:** the split panel shows "Taken 1 of N · still waiting 2" and the conflict diff |
| C8 | **User:** the validator blocks route, depth or priority claims; numbers in the text equal the input facts | **Friend:** if Gemini or the validator fails, the view still publishes facts with "Briefing unavailable" |
| C9 | **User:** copilot eval: answers cite record IDs; only allowed tools used | **Friend:** the runtime rejects any tool not in the allowlist (injection eval, T5) |
| C10 | **User:** `/dev/ui` page renders every shared component in every state; contrast check | **Friend:** call, desk and resident screens use only shared tokens (lint rule: no raw colours) |

### Who runs what, and when

| When | What runs | Who |
|---|---|---|
| Before opening a PR | Your own unit tests + contract tests + your side of any connection you touched | PR author |
| On every PR (Cloud Build trigger, T10) | All unit, contract and connection tests; Python + TypeScript type checks | Automatic; the PR can't merge if red |
| A contract model changes | Regenerate schema/types, update the affected fixtures, rerun both sides' connection tests | PR author; needs both humans' review |
| Each checkpoint evening (CP1–CP3) | E2E on the deployed URL + the joint checklist rows for that checkpoint | Both, together in the check-in |
| Wed 14 12:00 | Thai intake eval (3 scripted sessions) → decides live voice or push-to-talk | Friend |
| Fri 16 before freeze | Full E2E + all AI evals + accessibility review | Both |

### Working before the other side is ready

| Not ready yet | Use instead | Owner of the stand-in |
|---|---|---|
| Live views (C2, C5) | Fixture-backed mock: `useView()` reads `contract/fixtures/*` in dev mode | User |
| Real solver (C4) | `solve_split_stub()` returning `allocationSuggestion.cp3.json` | User ships it Tue 13 |
| Real `tiers.py` (C3) | Sort by waiting time only, behind the same function name | User ships it Tue 13 |
| API actions (C6, C7) | Mock API returning each `claim.*.json` result | Friend ships it Wed 14 morning |
| Shared components (C10) | Plain HTML using the placeholder tokens | User ships placeholder tokens Mon 12 |

Stand-ins never count as integrated. A connection is **done** only when both of its connection tests pass against the real code and its E2E step passes on the deployed URL.

### Joint checklist → tests

| Checklist row ([delivery agreement](two-person-delivery-agreement.md#joint-acceptance-checklist-future-checks-not-results)) | Covered by |
|---|---|
| Review gate | C2 producer (count still 24) + Friend unit (nothing changes before approval) |
| Take a family | C6 producer + E2E-1 |
| Resident timing | E2E-1 (window only after it's set, per family) |
| Priority order | C3 both sides |
| S1 failure | E2E-2 + C4 consumer |
| Job endings | C6 producer |
| Map honesty | C1 producer + C2 consumer + C8 producer |
| Retry and conflict | C6 producer + C4/C7 conflict tests |
| Permissions | Friend unit (Firestore rules) + C10 consumer + E2E role logins |
