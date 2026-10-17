# Round 2, part E — volunteer overview polish

Completed 17 October 2026. Changes are limited to `web/`; no commit, push or deployment was performed.

## Changes

- Replaced the loose totals with four KPI chips: urgent, waiting, zones without a team, and next-six-hour rain. Urgent and heavy rain use the existing urgent tokens. The single ledger sentence formats the existing API counts with separators. The rain tooltip retains its source and discloses the replay forecast substitute.
- Moved the city/sector/zone breadcrumb and Map/Satellite/Water controls into one paper toolbar inside the map. The legend remains bottom-left, the unused map padding is removed, and the taller map remains sticky on desktop.
- Urgent cases use compact information rows, need pills, a priority badge with its explanation tooltip, depth/silence/last-heard metadata, and right-side actions. Shared marks have a subtle background, a filled star and the marking team; the shared API and toggle semantics are unchanged.
- An unnamed team's action stays enabled and opens the existing shell team-name input through context. Opening the editor focuses the input; saving a name enables the existing marking path. Writes still disable concurrent marking.
- Zone headers stick beneath the tabs/sort toolbar while their cases scroll. Six zones appear initially; the remaining-count button expands and collapses the groups. Clicking a map case also reveals its collapsed group and focuses its row. Hover changes the highlight without moving keyboard focus.
- Urgent dots keep 44 px hit areas with 10 px ink-ringed visuals. Marks retain their star/ring. Hover/focus links dots and rows in both map implementations. The water canvas uses 0.5 opacity during the Urgent tab and 0.7 otherwise.
- Sector rows share the compact spacing without changing their selection behavior. Below 760 px, chips use two columns, the toolbar stays on the map, and lists retain the bottom sheet. Narrow case rows wrap metadata/actions to preserve readable text. New controls use at least 44 px targets and 14 px text; colors come from existing tokens.

## Files changed

- [OverviewPage.tsx](src/features/v2/volunteer/OverviewPage.tsx)
- [OverviewPage.test.tsx](src/features/v2/volunteer/OverviewPage.test.tsx)
- [UrgentList.tsx](src/features/v2/volunteer/UrgentList.tsx)
- [UrgentList.test.tsx](src/features/v2/volunteer/UrgentList.test.tsx)
- [UrgentList.interactions.test.tsx](src/features/v2/volunteer/UrgentList.interactions.test.tsx)
- [SectorMap.tsx](src/features/v2/volunteer/SectorMap.tsx)
- [SectorMap.test.tsx](src/features/v2/volunteer/SectorMap.test.tsx)
- [shared.tsx](src/features/v2/volunteer/shared.tsx)
- [volunteer.css](src/features/v2/volunteer/volunteer.css)
- [lang.test.tsx](src/features/v2/ui/lang.test.tsx) — adjusts the expected compact silence label.
- This report.

## Verification

Commands run from `web/`:

```text
npx tsc -b                      PASS
npm run check:tokens            PASS — no raw colours outside tokens.css
npm test                        PASS — 35 test files, 199 tests
VITE_DATA=api npm run build     PASS
```

Tests cover four KPI chips in Thai and English, loading totals, heavy-rain styling/provenance, enabled team-name actions, the team-name opener and subsequent marking handler, six-zone collapse/expansion, and map-dot hover/focus/click linkage. Interaction tests use a small React state harness because the existing Vitest environment has no DOM; static-render tests separately verify markup. Existing API request and shared-mark tests still pass.

`git diff --check`, relative report-link checks, and changed-file scope/sensitive-content review passed. No packages were installed. No files under `api/` or `data/` were changed, and the prohibited account environment file was not read.

The test suite emits existing React Router SSR `useLayoutEffect` warnings. Vite emits its existing warning for a minified bundle above 500 kB.

Live visual verification at 1440 px and 390 px could not run: starting Vite on loopback was rejected with `listen EPERM`. Header height, sticky placement, 44 px targets, wrapping and the absence of horizontal page scroll were reviewed in CSS, but are not browser-measured here. A real backend marking round trip was not exercised.

Creating the task branch was also blocked because Git metadata is read-only in this sandbox. Changes remain uncommitted on the existing checkout.
