# Round 2 · Part C — owner feedback

17 October 2026. Scope: React app under `web/` only.

## Changes

1. **Floating demo launcher and report space.** Removed the fixed full-width footer and its page padding. The dark launcher runs the first unfinished event in `SIMULATIONS` order with one tap; after all five events it offers Start over. Its anchored popover contains done ticks, the result/proof line and folded clock controls. Without a family session it contains only clock controls. Escape, outside click and Close dismiss it; below 760 px it becomes a bottom sheet. The existing request lock, busy state and location gate remain. The report header is tighter; phone and trace share the available viewport height, with scrolling inside the chat and trace instead of a fixed chat height.
2. **Get ready checklist.** Explicit full-width rows use a 22 px native checkbox beside Thai text and an English gloss underneath. Completed rows use the done token and strike-through. Progress remains; no images were added.
3. **Volunteer map hierarchy.** The map fills the left column with a viewport-relative height and a 520 px minimum. Totals are compact, the paragraph beneath the map is removed, and a closed Legend chip combines need, water/go-by and shelter keys. Map/Satellite/Water share a reserved control strip. Zone label candidates are the top five by need plus the selected sector, or all visible zones at zoom 16 and above. A pure projected-pixel spacing helper keeps labels at least 70 px apart; OverlayView drawing and zoom changes recalculate placement. Sector badges are 30 px with extended hit areas and disappear above zoom 14. Water mode removes need fill and shows urgent/waiting count bubbles; switching water off restores need fill. The outline fallback also supports urgent dots.
4. **Urgent cases by zone.** Added the urgent read and shared do-first write APIs and types. Sectors/Urgent tabs sit above the list and in the mobile sheet. Urgent groups preserve server priority order by default, with Deepest and Longest silent alternatives. Group headers show place, depth, go-by, water trend, urgent count and team coverage, and select the map zone. Cases show needs, depth, last-heard/silence, priority explanation, shared team/time marks, Do first and Open. Polling runs every 10 seconds and on replay-clock changes; request generations prevent stale reads from overwriting a completed mark. Team-name edits now reach the overview immediately. Urgent dots select, scroll to and highlight their row; starred cases have a star ring. Repeated taps on the same dot scroll again.

## Files changed

Paths below are relative to `web/`.

| File | Purpose |
| --- | --- |
| `src/features/v2/api.ts` | Urgent case/group/view types, `vol.urgent`, `vol.first` |
| `src/features/v2/ui/DemoBar.tsx` | Floating launcher, next event, popover, dismissal |
| `src/features/v2/ui/DemoBar.test.tsx` | Next-event order/restart, disabled/busy state, closed popover |
| `src/features/v2/ui/FamilyFollowUp.tsx` | Completed checklist row state |
| `src/features/v2/ui/FamilyFollowUp.test.tsx` | Checklist row markup, gloss and progress |
| `src/features/v2/ui/phase-four.css` | Checklist sizing and completion treatment |
| `src/features/v2/ui/phase-one.css` | Remove footer styles/padding, launcher/sheet styles, viewport report layout |
| `src/features/v2/volunteer/OverviewPage.tsx` | Tabs, urgent integration and map/list selection |
| `src/features/v2/volunteer/UrgentList.tsx` | Urgent polling, sorting, shared marks and case rows (new) |
| `src/features/v2/volunteer/UrgentList.test.tsx` | Sorting, case markup, disabled marks, encoded route and on/off payloads (new) |
| `src/features/v2/volunteer/SectorMap.tsx` | Label placement, counts, badges, urgent dots, compact legend |
| `src/features/v2/volunteer/SectorMap.test.tsx` | Pixel spacing, zoom redraw/badge visibility, water fill/count behavior |
| `src/features/v2/volunteer/shared.tsx` | Synchronize current team across shell/overview and browser tabs |
| `src/features/v2/volunteer/volunteer.css` | Map hierarchy, compact controls/labels/totals, urgent list and mobile sheet |
| `src/ui/tokens.css` | Translucent paper and transparent map-hit tokens |
| `ROUND2-PART-C.md` | This summary (new) |

## Verification

Executed from `web/`:

```text
npx tsc -b
PASS (exit 0)

npm run check:tokens
Tokens check passed: no raw colours outside tokens.css

npm test
Test Files  32 passed (32)
Tests       185 passed (185)

VITE_DATA=api npm run build
PASS — 172 modules transformed; production build completed
```

The tests emit React Router server-rendering `useLayoutEffect` warnings. Vite reports its chunk-size advisory for the main bundle above 500 kB; the build succeeds. Token checking and the build were repeated after the final CSS adjustment. `git diff --check` also passes.

## Remaining verification and limits

- No browser surface is available in this session. Rendered 1440×900, 1280×720 and 390 px layouts, horizontal overflow, live Google Maps and pointer/keyboard interactions need a visual pass. CSS implements these layouts; this is not a claim of screenshot verification.
- The API is unreachable here. API behavior is verified against the supplied TypeScript contract and mocked fetch tests, not a live server or two connected volunteer sessions.
- All four requested implementation items are covered; the live/visual checks above remain unverified.
- No commit, push or deployment. No changes outside `web/`; the private env file was not read. Creating a task branch was blocked by read-only Git metadata, so the edits remain uncommitted on the existing checkout.
