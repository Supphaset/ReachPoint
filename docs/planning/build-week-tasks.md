# Build-week task list (12–17 Oct 2026)

Based on the [delivery agreement](../collaboration/two-person-delivery-agreement.md) and the eng review tasks (T-numbers). For the whole flow, see the [overview](../OVERVIEW.md). Times are Bangkok.

**Owners**
- **You:** map, flood data, solver, team screens, split panel.
- **Friend:** voice and intake, coordinator desk, rules engine, database, deploys.
- **Frontend:** one app. You own the shared foundation (shell, tokens, components, data hooks). Each person builds their own screens on it.

## Before Mon 12 (today)

| # | Task | Who |
|---|---|---|
| 0.1 | Invite your friend as a GitHub collaborator on Supphaset/ReachPoint | You |
| 0.2 | Review PR #1. Confirm 0009 and its amendments, the delivery agreement, owning `reachpoint-main`, and pack §8 questions 9–12 | Friend |
| 0.3 | Agree the spend cap and payer | Both |
| 0.4 | Check you're both registered; read the deadline time on the dashboard | Both |
| 0.5 | Mark PR #1 ready and merge | Both |

## Mon 12 — CP0: both apps deployed, contract frozen

**You**
- [ ] Register the Earth Engine noncommercial project (your sandbox)
- [ ] Flood check (pack §5.1c): list the Sentinel-1 scenes for Oct–Dec 2025, run change detection, compare with the EOS/AIT maps, record the result in `data/SOURCES.md`
- [ ] Export the Hat Yai extent as GeoJSON under 300 KB (T9)
- [ ] Draw the P-A/P-B/P-C areas and zones B-1…B-5, with landmarks L1–L3 and D1
- [ ] Ship the area-briefing fixture files **by noon**
- [ ] **Frontend foundation (you own it):** one React app shell, role routes, wordmark, phone tab bar; placeholder tokens; data hooks (sign-in, live Firestore views, typed API client)
- [ ] Map + list on the shell, same IDs

**Friend**
- [ ] Create `reachpoint-main` with a budget alert on every project; add you as Editor
- [ ] FastAPI skeleton on Cloud Run; `scripts/deploy.sh`
- [ ] Firestore + a seed script that loads your fixtures
- [ ] Firebase Auth with 4 test roles (coordinator, T-R, T-S, qualified-reviewer fixture)
- [ ] ADK hello-world agent deployed

**Both**
- [ ] Freeze contract v1.0: Pydantic models in `api/contract/` generate the JSON Schema and TS types (T2, T12): listings with family groups, `needRevision`, `lastConfirmedAt`; per-group allocations; team status reason/ETA
- [ ] Test harness: pytest, Hypothesis, Firestore emulator, Playwright (T11)

## Tue 13 — CP1: text report → approved → shows on your map, count unchanged

**You**
- [ ] Run `/design-consultation` → final tokens (state colours, Thai + Latin fonts, spacing)
- [ ] Shared components ready for your friend: status chip, priority badge, "AI proposal" card, error/offline banner, "last updated" line, big buttons
- [ ] Exposure estimate per zone: Open Buildings + WorldPop, cross-checked with DOPA, shown as a range
- [ ] Area and zone briefing screen on live views
- [x] `api/rules/tiers.py`: red/yellow/green tiers, then distance, then waiting time; property test that the sort and the solver share tiers (T15). Done: `tier()`, `colour()`, `sort_key()` and Hypothesis tests (RED first, nearest first, waiting breaks ties, colour = view of tier); the solver half of T15 is added when `allocation.py` calls `tier()`
- [x] Solver notebook run on the fixture (`api/notebooks/split-solver.ipynb` on `contract/fixtures/allocationInput.cp3.json`: checks (a)–(d) pass; seat units and safe splits (D33–D35) take S1 from 12 to 16 people; findings: weights ≥ 0.1, and stretcher cases need an urgent flag)

**Friend**
- [ ] Text intake → Gemini structured output → proposed facts with transcript quotes
- [ ] Desk approve/reject → case → listing; views regenerated in the same transaction (T3)
- [ ] Allowlisted read/propose-only tool registry + prompt-injection eval (T5)
- [ ] Start screens (call, desk, resident) on your shared shell and components; ask you for any new shared component
- [ ] Intake records each household's make-up (`party`: adults, children under 12, babies, stretchers or wheelchairs) for seat units (D33); desk prompts for an urgent flag when a request includes a stretcher or wheelchair (proposed, see D33–D36; the coordinator decides, nothing becomes urgent automatically)

## Wed 14 — CP2: publish → you take Families 1+2 → resident sees the window per family

**You**
- [ ] Team list: colour, distance, last confirmed, "Ask desk to re-confirm"
- [ ] Take whole family groups; set window; progress; hand back; end outcomes (Done / Already left / Not found / Needs more help); Busy reason + "back about" (T17)
- [ ] Clear errors: Already taken, This case changed, Needs N seats, This job is closed

**Friend**
- [ ] `claimListing`, hand back, close: one transaction; `NEED_CHANGED`, `ALLOCATION_CLOSED` (T13)
- [ ] Shared open lists per assistance type; one-time urgent prompt on becoming Available (T14)
- [ ] Resident status page per family, using the token link
- [ ] Browser call screen on ADK Live (T6). **12:00 decision:** if 3 Thai test calls aren't clean, switch to push-to-talk

## Thu 15 — CP3: full walk-through, including the S1 failure

**You**
- [x] OR-Tools split solver: staged, reasons, cache key, 5 s limit (T4) (`api/rules/allocation.py`: `solve_split`, `compare_scenarios`; `suggestionId` from the input is the cache key; seat units and safe splits D33–D35; solver half of T15 in `api/tests/test_allocation.py`; fixture `allocationSuggestion.cp3.json`)
- [ ] Split panel: team rows, "Still unmet", "Ask these N teams", What-if tab
- [ ] Gemini zone briefing text, from computed fields only; prose validator (T7, shared)

**Friend**
- [ ] S1 failure review: hold, relist unfinished groups, withdraw the old window
- [ ] Message templates: server fills team and time; "No longer current" + desk "Update needed" (T16)
- [ ] Direct-ask operation for the split panel; history view

**Both**
- [ ] Run the pack §7 walk-through on the deployed app

## Fri 16 — feature freeze at 18:00

**You**
- [ ] Consistency pass across all six screens, then the accessibility review
- [ ] Map/UX polish, phone layout
- [ ] Stretch only if CP3 passed: routine planner (T8)

**Friend**
- [ ] Copilot read-only Q&A (you write its instructions and tool choice)
- [ ] Retries, conflicts, Firestore rules, status-link rules; Cloud Build trigger (T10)

**Both**
- [ ] Joint acceptance checklist (delivery agreement)

## Sat 17 — submit by 21:00

| You | Friend |
|---|---|
| Video shots: map, team, split | Video shots: call, desk, resident |
| Deck: impact, map, data honesty | Deck: architecture, AI |
| Judge-facing README (together) | Final deploy + check the live URL |

**Sun 18:** buffer only.

## Cut order if behind
1. Bangkok package
2. Reconciliation UI polish
3. Copilot replan drafting
4. Whole copilot
5. P-C field-report scene
6. Open Buildings counts
