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
| 0.6 | Pinpoint API: check its terms and cost for a noncommercial demo, then put the key in Secret Manager (never in Git). Google Places is the fallback. **13 Oct: the friend has a tested key; the server adapter is built. Remaining steps: [Pinpoint handoff](pinpoint-handoff.md)** | Friend |

## Mon 12 — CP0: both apps deployed, contract frozen

**You**
- [ ] Register the Earth Engine noncommercial project (your sandbox)
- [ ] Flood check (pack §5.1c): list the Sentinel-1 scenes for Oct–Dec 2025, run change detection, compare with the EOS/AIT maps, record the result in `data/SOURCES.md`
- [ ] Export the Hat Yai extent as GeoJSON under 300 KB (T9)
- [x] Draw the P-A/P-B/P-C areas and zones, with landmarks and D1, and cut each zone into **segments** (D30: city zones along OSM streets inside the 4 city districts, `cut_city_zones.py` + `build_geography.py`; 17 zones, 66 segments; C1 fixture `contract/fixtures/areas.hy-2025-11.json`)
- [x] Add the "no satellite data" area (dense urban core) to the package, so nothing is ever shown as dry (D26) (`flood_check.py nodata`; 16 of 17 reported points inside)
- [x] Ship the area-briefing fixture files **by noon** (`contract/fixtures/areaBriefing.*.json`: P-A/P-B/P-C + empty, stale and layer-missing variants; `build_briefing_fixtures.py`)
- [x] **Frontend foundation (you own it):** one React app shell, role routes, wordmark, phone tab bar; placeholder tokens; data hooks (sign-in, live Firestore views, typed API client) (`web/`; demo role picker and fixture-backed `useView` until Firebase Auth and Firestore are up)
- [x] Map + list on the shell, same IDs (offline schematic map from the package; Google Maps base later)

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
- [ ] Run `/design-consultation` → final tokens (state colours, Thai + Latin fonts, spacing). Proposed tokens are in `web/src/ui/tokens.css`; the consultation adjusts values, not names
- [x] Shared components ready for your friend: status chip, priority badge, "AI proposal" card, error/offline banner, "last updated" line, big buttons (`web/src/ui/`, all states on `/dev/ui`)
- [x] Exposure estimate **per segment** (D27): two ranges each, everyone living there and people inside the satellite extent (Open Buildings + WorldPop, cross-checked with DOPA)
- [x] Sanity check: the district total against GISTDA's 25 Nov figure (52,731 rai, ~150,000 people affected); record it in `data/SOURCES.md`
- [ ] Area and zone briefing screen on live views (built on the C2 fixtures with every state; switch to the live view when the friend's Firestore views exist)
- [x] `api/rules/tiers.py`: red/yellow/green tiers, then distance, then waiting time; property test that the sort and the solver share tiers (T15). Done: `tier()`, `colour()`, `sort_key()` and Hypothesis tests (RED first, nearest first, waiting breaks ties, colour = view of tier); the solver half of T15 is added when `allocation.py` calls `tier()`
- [x] Solver notebook run on the fixture (`api/notebooks/split-solver.ipynb` on `contract/fixtures/allocationInput.cp3.json`: checks (a)–(d) pass; seat units and safe splits (D33–D35) take S1 from 12 to 16 people; findings: weights ≥ 0.1, and stretcher cases need an urgent flag)

**Friend**
- [ ] Text intake → Gemini structured output → proposed facts with transcript quotes
- [ ] Desk approve/reject → case → listing; views regenerated in the same transaction (T3)
- [ ] Allowlisted read/propose-only tool registry + prompt-injection eval (T5)
- [ ] Start screens (call, desk, resident) on your shared shell and components; ask you for any new shared component
- [ ] Intake asks consent to share health needs with the rescue team; desk writes the team's medical notes (functional first, then condition) and sets each family's destination, D1 or H1 (D38, D39, proposed)
- [ ] Intake records each household's make-up (`party`: adults, children under 12, babies, stretchers or wheelchairs) for seat units (D33); desk prompts for an urgent flag when a request includes a stretcher or wheelchair (proposed, see D33–D36; the coordinator decides, nothing becomes urgent automatically)

## Wed 14 — CP2: publish → you take Families 1+2 → resident sees the window per family

**You**
- [x] Team list: colour, distance, last confirmed, "Ask desk to re-confirm" (`web/src/features/team/`, on the C5 fixture `teamMissions.T-S.json`, order from `tiers.py`)
- [x] Take whole family groups; set window; progress; hand back; end outcomes (Done / Already left / Not found / Needs more help); Busy reason + "back about" (T17) (fixture-mode store applies the C6 rules; switch to the friend's API when it is up)
- [x] Clear errors: Already taken, This case changed, Needs N seats, This job is closed (`claim.*.json`; `?claim=` dev switch)
- [x] Job view: exact point, precision and "Navigate" link shown **only after the team has taken the job** (D25, C16) (points from `pickups.synthetic.json`, coordinator-side)
- [x] Map: "no satellite data" area and live "reported by callers" points (D26) (reviewed requests only, at landmark level, body-height band, stale after 6 h; still shown when the flood layer is missing; `callerWater` in the C2 view, live once the friend's views regenerate it)

**Friend**
- [ ] `claimListing`, hand back, close: one transaction; `NEED_CHANGED`, `ALLOCATION_CLOSED` (T13)
- [ ] Shared open lists per assistance type; one-time urgent prompt on becoming Available (T14)
- [ ] Resident status page per family, using the token link
- [ ] Location resolver (D25, C16): Pinpoint for Thai addresses, Google Places for building names, caller pin or Maps link; snap to zone/segment/landmark with source + precision; failures → unlocated list on the desk (13 Oct: built in `api/location/` with caller GPS/map pin, Pinpoint adapter and stand-in; the friend matches the Pinpoint request, see [Pinpoint handoff](pinpoint-handoff.md). Google Places not built)
- [ ] Places and report kinds (D29): my household / check-on / neighbour report; one place per building; "at least N" = largest single neighbour report, never a sum; exact point readable only by the coordinator and the taking team (Firestore rules test)
- [ ] Browser call screen on ADK Live (T6). **12:00 decision:** if 3 Thai test calls aren't clean, switch to push-to-talk

## Thu 15 — CP3: full walk-through, including the S1 failure

**You**
- [x] OR-Tools split solver: staged, reasons, cache key, 5 s limit (T4) (`api/rules/allocation.py`: `solve_split`, `compare_scenarios`; `suggestionId` from the input is the cache key; seat units and safe splits D33–D35; solver half of T15 in `api/tests/test_allocation.py`; fixture `allocationSuggestion.cp3.json`)
- [x] Split panel: team rows, "Still unmet", "Ask these N teams", What-if tab (`web/src/features/split/`, `/desk/split`; real solver output in `splitPanel.cp3.json` with precomputed What-ifs until the API serves `compare_scenarios`; stale ask shows the diff; `askTeams.*.json`)
- [x] Gemini zone briefing text, from computed fields only; prose validator (T7, shared) (`api/ai/briefing_text.py`: numbers and places must be in the facts; no route, safety, dryness or priority claims; written in the background once per set of facts)

**Friend**
- [ ] S1 failure review: hold, relist unfinished groups, withdraw the old window
- [ ] Message templates: server fills team and time; "No longer current" + desk "Update needed" (T16)
- [ ] Direct-ask operation for the split panel; history view

**Both**
- [ ] Run the pack §7 walk-through on the deployed app

## Thu 15 — zone missions (also CP3)

**You**
- [x] Zone order rule in `tiers.py` (called → register → estimate in segments not yet checked → time since check) + suggested checks with reasons; property test
- [ ] `api/rules/exposure.py` (C15): segment basis (satellite → callers → checked), zone "not yet checked" range, call rate per 1,000 residents + "quiet: phones may be down" flag; property tests
- [ ] Depth tool for the triage agent (C17, D32): segment band, sources, trend, conflicts, kit; area-depth raise with its own reason; tests
- [x] Synthetic vulnerable-residents register fixture (`register.hy-2025-11.json`, landmark-level)
- [x] Team screen: take a segment, pickup list, mark Checked / Partly checked / Couldn't reach, field report button (starter server + `web/src/features/team/Segments.tsx`; B-4 scene in `api/tests/test_b4_scene.py`)
- [ ] Copilot instructions for `propose_zone_priority_change`

**Friend**
- [ ] Zone missions + segments in the rules engine (`publishZoneMission`, cut segments, `takeSegment`, `markSegment`)
- [ ] Intake extraction: `waterDepth` (quote, band, time) + eval (C17, D32)
- [ ] Register stored with coordinator-only access (Firestore rules test)
- [ ] Desk: suggested checks (publish / dismiss), segment cutting, copilot proposals (accept / reject)
- [ ] Resident line "Team T-x is working in your area today"
- [ ] Zone view regenerated with `exposure.py` after each reviewed water report and `markSegment`; reviewed water reports written as caller flood points

**Both**
- [ ] B-4 scene on the deployed URL: suggested check → T-R takes B-4 · L5 → field report → C-07 (RED) → T-S takes it → "Partly checked · 1 household found"

## Thu 15 — surge and triage agent (also CP3)

**You**
- [x] Triage agent definition: instructions, tools, safety-floor call to `tiers.py`, reasons with quotes (`api/ai/triage.py`, Google ADK; rules live in the tools)
- [x] Triage eval set: emergencies, duplicates, unclear requests, injection attempts ("rank me first"), plus place cases (Condo X: three callers, overlapping counts; a linked request with a new hazard) (`api/scripts/triage_eval.py`, 8/8 live on 12 Oct; condo case still to add)
- [ ] Surge simulator: 300 fictional Thai text requests from templates + live counters page

**Friend**
- [ ] Triage agent on the ADK runtime; ranks and merges written to the live list; human overrides final; logs
- [ ] Auto-filing of clear requests as "AI-read" into zone segments; separate counts
- [ ] Desk: group review, verify/correct, pin/re-rank/unflag

**Both**
- [ ] Surge demo on the deployed URL: 300 requests in 2 minutes; first emergency at the top in seconds; one live voice call alongside

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
1. Bangkok package (already a stretch goal)
2. Reconciliation UI polish
3. Copilot replan drafting
4. Whole copilot
5. P-C field-report scene
6. Open Buildings counts (the per-segment estimate falls back to WorldPop only)
