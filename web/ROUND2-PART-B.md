# Round 2 UI — Part B

17 Oct 2026. Builds on the uncommitted Part A working tree. Changes are limited to `web/`; nothing committed, pushed or deployed. No API/data source changes, installs or private environment reads.

## Step 6 — map-first volunteer page

- `src/features/v2/volunteer/SectorMap.tsx`: Google Maps through the existing loader; Thai roadmap by default, hybrid toggle, native zoom controls, sector fit and selected-zone pan/zoom. Unmodified base map labels remain visible beneath 35% need fills. Colours come from computed CSS tokens. Zone edges distinguish no-team coverage by weight; selected zones have a heavier stroke. Ink sector outlines, area-centroid letter buttons, named zone buttons for the top eight needs and selected sector. Buttons support keyboard activation. Overlay cleanup and resize handling included. Existing SVG remains the no-key/offline fallback, with named zones and zoom buttons.
- `src/features/v2/volunteer/OverviewPage.tsx`: shared selection and breadcrumb; numeric sector columns, need/urgent bars, zone coverage pills. Zone detail replaces the list in the right column: decision, attributed reasons, uncertainty, API-priority family sentences and sticky action footer. Planning uses vehicle/seats/time chips, editable team and message, preview and notification action. Posted count comes from `plan.told`; unavailable stays unknown. A posted plan explicitly does not mean rescue.
- `src/features/v2/volunteer/shared.tsx`: optional ledger using actual API totals and field captions; Thai-first volunteer navigation and unknown-depth label.
- `src/features/v2/volunteer/volunteer.css`: desktop `1fr 452px` workspace, map controls, list rows, panel/footer and plan styling.

## Step 7 — phones below 760 px

- `src/features/v2/V2Page.tsx`: Chat / AI / Map selection; maps and chat remain mounted across view changes; latest-evidence toast expires after six seconds and opens AI view.
- `src/features/v2/ui/DemoBar.tsx`: accessible expand/collapse handle for the dark mobile demo sheet; all existing actions and request locks retained.
- `src/features/v2/ui/phase-one.css`: phone tabs, frameless chat, evidence toast, map view and collapsed/expanded demo sheet.
- Volunteer overview/CSS: 330 px map, peek/half/full list controls, zone and planning sheets with sticky footer. Opening a zone focuses Close; Escape closes it. These are nonmodal sheets so the map remains usable.

## Step 8 — QA and regression coverage

- New `src/features/v2/volunteer/SectorMap.test.tsx`: offline named/keyboard selection markup, unknown/closed need bands, priority ordering without input mutation, token-based Google polygon options, selected halo, named overlay activation, cleanup and area centroid.
- Updated `src/features/v2/ui/DemoBar.test.tsx`: phone view selection and collapsed demo handle, alongside Part A tests.
- Code review fixes: avoid constructing Maps in a hidden zero-size host, preserve MultiPolygon zone components, restrict fallback labels to the selected sector/top eight, prevent overlay gestures reaching the map, remove repeated water figures, focus zone controls and retain clear unknown counts.

## Verification

The requested sequence was run after steps 6 and 7 and again after QA:

```sh
cd web
npx tsc -b
npm run check:tokens
npm test
VITE_DATA=api npm run build
```

- Step 6: TypeScript and token checks passed; 31 files / 170 tests passed; API-mode build passed.
- Step 7: TypeScript and token checks passed; 31 files / 170 tests passed; API-mode build passed.
- Final QA: TypeScript and token checks passed; 31 files / 174 tests passed; API-mode build passed.
- `git diff --check -- web`: passed.
- Nonfatal output: existing React Router server-render `useLayoutEffect` warnings; Vite warns that the main bundle exceeds 500 kB.

## Remaining verification

Rendered 1440×900, 390 px and 1920×1080 checks remain undone. The sandbox rejected the local Vite listener (`EPERM`), the configured Playwright browser is absent, and an attempt to launch installed Chrome was blocked. Consequently no screenshot, measured overflow/font/target audit or real-device verification is claimed. Responsive widths, minimum 14 px text and 44 px controls were reviewed in code, not measured in a browser.

The real API is unreachable from this sandbox. Google tile/POI appearance, real-key loading, live sector geometry, actual plan extraction and notification delivery still require the connected app. Google integration is covered with mocked overlays, not a live-key end-to-end test. No mockup quantities, routes or depth values were substituted for API data.

API references checked 17 Oct 2026: [Google polygon shapes](https://developers.google.com/maps/documentation/javascript/shapes) and [custom overlays](https://developers.google.com/maps/documentation/javascript/customoverlays). These document the overlay APIs; they do not establish runtime verification of this app.
