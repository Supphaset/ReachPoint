# Round 2, part D — judge UI language

Completed 17 October 2026. Changes are limited to `web/`; no commit, push or deployment was performed.

## Behavior and coverage

- `UiLangProvider` wraps the app routes. Initial resolution is valid `?lang=en|th`, then `rp.v2.lang` in localStorage, then Thai for a navigator language starting with `th`, otherwise English. Storage access is guarded. The setter preserves other URL parameters, the hash and history state, uses `replaceState`, and saves the preference.
- `useUiLang()` supplies `lang` and `setLang`. `useT()` binds the plain-text `t(th, en, lang)` helper to the context; `Tr` renders English alone or Thai with a small English gloss. Fixed copy uses explicit pairs.
- The shared StepHeader includes the segmented ไทย / EN control, including the volunteer shell and its server-unavailable fallback. The controls have 44 px minimum dimensions and 14 px text. The phone header places the toggle beside the brand, with navigation wrapping below it. Colors use existing tokens.
- The overview shows “Prefer English? Tap EN (top right)” only in Thai mode.
- Converted report headings/tabs, Phone chrome and receipts, location/shelter/notice/status cards, quick actions, checklist labels, demo launcher/events, evidence timeline, volunteer overview and zone panel, UrgentList, shared volunteer labels, SectorMap controls/overlays/legend/key, plan screens and trip map copy. Zone, case and feed pages inherit the translated shell; their existing English-only chrome stays English.
- V2Page reads the context language. Changing it remounts Phone, runs its existing `start(lang)` path for a fresh session, stops the previous phone's voice connection, and clears the family's report/map evidence. The separate menu language action is removed. Sample chips and local quick-action messages use the session language.
- V2 Google Maps loaders request English consistently: the SDK loads once per page, so its vendor controls must not retain Thai after an EN toggle. App map overlays and controls still follow the live context.

## Thai still visible in English

- The explicit **ไทย** language button remains so readers can switch back.
- Server content is preserved: zone/place/shelter names, team names, quotes, observations, briefings, saved plans, conversations and errors may contain Thai. Zone names remain next to their IDs. Existing records are not translated or rewritten; agent replies and family notices come from the fresh session's language.
- Google basemap geographic labels can contain local Thai place names.
- No other fixed Thai UI copy is intentionally retained in English mode. The English fixtures in the static-render tests contain no Thai characters across the demo launcher, urgent list, dynamic cards, report tabs and map legend.

## Verification

Requested commands, run from `web/`:

```text
npx tsc -b                         PASS
npm run check:tokens               PASS — no raw colours outside tokens.css
npm test                          PASS — 33 test files, 192 tests
VITE_DATA=api npm run build        PASS — built in 2.40s
```

`git diff --check` also passed. Tests cover language precedence/fallback, blocked storage, preference saving and URL preservation, both translation modes, header selection markup, English quick-action payloads, and English static markup checked with `/[฀-๿]/`. Existing Thai assertions were updated for the small-gloss markup.

The test run emits React Router's SSR `useLayoutEffect` warnings. The build emits a warning for a minified bundle above 500 kB (the main bundle is about 552 kB).

A live 390 px browser/interaction check and real server chat verification were **not run**: starting Vite on the loopback listener failed with `listen EPERM`. Target sizes and wrapping were inspected in CSS; the no-horizontal-scroll condition is not browser-verified here.

The sandbox also blocked creating the task branch because `.git` is read-only. The checkout remains on its original branch with uncommitted web-only edits. No packages were installed; the prohibited account environment file was not read.

## Files changed

- [ROUND2-PART-D.md](ROUND2-PART-D.md)
- [src/App.tsx](src/App.tsx)
- [src/features/v2/BoardMap.tsx](src/features/v2/BoardMap.tsx)
- [src/features/v2/NeighbourPicture.tsx](src/features/v2/NeighbourPicture.tsx)
- [src/features/v2/OverviewLanding.tsx](src/features/v2/OverviewLanding.tsx)
- [src/features/v2/Panels.tsx](src/features/v2/Panels.tsx)
- [src/features/v2/Phone.tsx](src/features/v2/Phone.tsx)
- [src/features/v2/PlanPage.tsx](src/features/v2/PlanPage.tsx)
- [src/features/v2/V2Page.tsx](src/features/v2/V2Page.tsx)
- [src/features/v2/ui/ChatShell.tsx](src/features/v2/ui/ChatShell.tsx)
- [src/features/v2/ui/DemoBar.tsx](src/features/v2/ui/DemoBar.tsx)
- [src/features/v2/ui/DepthBars.tsx](src/features/v2/ui/DepthBars.tsx)
- [src/features/v2/ui/FamilyFollowUp.test.tsx](src/features/v2/ui/FamilyFollowUp.test.tsx)
- [src/features/v2/ui/FamilyFollowUp.tsx](src/features/v2/ui/FamilyFollowUp.tsx)
- [src/features/v2/ui/LocationCard.tsx](src/features/v2/ui/LocationCard.tsx)
- [src/features/v2/ui/NoticeCard.tsx](src/features/v2/ui/NoticeCard.tsx)
- [src/features/v2/ui/Shared.tsx](src/features/v2/ui/Shared.tsx)
- [src/features/v2/ui/ShelterCard.tsx](src/features/v2/ui/ShelterCard.tsx)
- [src/features/v2/ui/TraceTimeline.tsx](src/features/v2/ui/TraceTimeline.tsx)
- [src/features/v2/ui/TripMap.tsx](src/features/v2/ui/TripMap.tsx)
- [src/features/v2/ui/lang.test.tsx](src/features/v2/ui/lang.test.tsx)
- [src/features/v2/ui/lang.tsx](src/features/v2/ui/lang.tsx)
- [src/features/v2/ui/phase-one.css](src/features/v2/ui/phase-one.css)
- [src/features/v2/volunteer/OverviewPage.tsx](src/features/v2/volunteer/OverviewPage.tsx)
- [src/features/v2/volunteer/SectorMap.tsx](src/features/v2/volunteer/SectorMap.tsx)
- [src/features/v2/volunteer/TripPage.tsx](src/features/v2/volunteer/TripPage.tsx)
- [src/features/v2/volunteer/UrgentList.test.tsx](src/features/v2/volunteer/UrgentList.test.tsx)
- [src/features/v2/volunteer/UrgentList.tsx](src/features/v2/volunteer/UrgentList.tsx)
- [src/features/v2/volunteer/shared.tsx](src/features/v2/volunteer/shared.tsx)
